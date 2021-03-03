# Standard library
import bleach
import datetime
import flask
import markdown
import os
import re

# Packages
from canonicalwebteam.flask_base.app import FlaskBase
from canonicalwebteam.templatefinder import TemplateFinder
from slugify import slugify
import talisker.requests

# Local
from webapp.greenhouse import Greenhouse
from webapp.greenhouse import _parse_feed_department
from webapp.partners import Partners

app = FlaskBase(
    __name__,
    "canonical.com",
    template_folder="../templates",
    static_folder="../static",
    template_404="404.html",
    template_500="500.html",
)
session = talisker.requests.get_session()
greenhouse_api = Greenhouse(session)
greenhouse_api_key = os.environ.get("GREENHOUSE_API_KEY")
partners_api = Partners(session)


@app.route("/")
def index():
    partner_groups = partners_api.get_partner_groups()
    return flask.render_template("index.html", partner_groups=partner_groups)


@app.route("/secure-boot-master-ca.crl")
def secure_boot():
    return flask.send_from_directory(
        "../static/files", "secure-boot-master-ca.crl"
    )


# Class that collects department-specific content
class Department(object):
    def __init__(self, name):
        self.name = name
        self.slug = _parse_feed_department(self.name)

    def __lt__(self, other):
        return self.name < other.name


# Generates a list of departments
def get_department_list():
    departments = set()

    try:
        all_departments = greenhouse_api.get_departments()
    except Exception as error:
        flask.abort(502, str(error))

    # Populate departments[] with Department objects,
    # ensuring that there are no duplicates
    for item in all_departments:
        departments.add(Department(item))

    return sorted(departments)


def render_navigation():
    context = {}
    departments = get_department_list()
    all_vacancies = greenhouse_api.get_vacancies_by_department("all")
    vacancy_count = {}

    # Populate vacancy_count dictionary with 0 values
    for department in departments:
        vacancy_count[department.slug] = 0

    # Count number of vacancies in each department,
    # and add relevant departments to the vacancies
    # list that gets rendered
    for vacancy in all_vacancies:
        dept = Department(vacancy["department"])
        vacancy_count[dept.slug] += 1

    context["nav_departments"] = departments
    context["nav_vacancy_count"] = vacancy_count

    return context


# Career departments
@app.route("/careers/results")
def results():
    # context = render_navigation()
    context = {}
    vacancies = []
    departments = []
    message = ""
    if flask.request.args:
        core_skills = flask.request.args["coreSkills"].split(",")
        context["core_skills"] = core_skills
        vacancies = greenhouse_api.get_vacancies_by_skills(core_skills)
    else:
        message = "There are no roles matching your selection."
    if len(vacancies) == 0:
        message = "There are no roles matching your selection."
    else:
        for job in vacancies:
            if not (job["department"] in departments):
                departments.append(job["department"])
    context["message"] = message
    context["vacancies"] = vacancies
    context["departments"] = departments
    return flask.render_template("careers/results.html", **context)


@app.route(
    "/careers/<regex('[0-9]+'):job_id>",
    methods=["GET", "POST"],
    defaults={"job_title": None},
)
@app.route(
    "/careers/<regex('[0-9]+'):job_id>/<job_title>", methods=["GET", "POST"]
)
def job_details(job_id, job_title):
    context = render_navigation()
    context["bleach"] = bleach
    context["job"] = greenhouse_api.get_vacancy(job_id)
    if not context["job"]:
        flask.abort(404)

    if flask.request.method == "POST":
        response = greenhouse_api.submit_application(
            greenhouse_api_key, flask.request.form, flask.request.files, job_id
        )
        if response.status_code == 200:
            context["message"] = {
                "type": "positive",
                "title": "Success",
                "text": (
                    "Your application has been successfully submitted."
                    " Thank you!"
                ),
            }
        else:
            context["message"] = {
                "type": "negative",
                "title": f"Error {response.status_code}",
                "text": f"{response.reason}. Please try again!",
            }

        return flask.render_template("/careers/job-detail.html", **context)

    return flask.render_template("/careers/job-detail.html", **context)


@app.route("/careers/<department>", methods=["GET", "POST"])
def department_group(department):
    context = render_navigation()
    context["department"] = None
    templates = []

    # Generate list of templates in the /templates/careers folder,
    # and remove the .html suffix
    for template in os.listdir("./templates/careers"):
        if template.endswith(".html"):
            template = template[:-5]
        templates.append(template)

    # Check if deparment exist or return 404
    for dept in context["nav_departments"]:
        if dept.slug == department:
            context["department"] = dept
            context["vacancies"] = greenhouse_api.get_vacancies_by_department(
                dept.slug
            )

    if not context["department"] and department not in templates:
        flask.abort(404)
    elif department == "all":
        context["vacancies"] = greenhouse_api.get_vacancies_by_department(
            "all"
        )

    context["templates"] = templates

    if flask.request.method == "POST":
        response = greenhouse_api.submit_application(
            os.environ["GREENHOUSE_API_KEY"],
            flask.request.form,
            flask.request.files,
        )
        if response.status_code == 200:
            message = {
                "type": "positive",
                "title": "Success",
                "text": (
                    "Your application has been successfully submitted."
                    " Thank you!"
                ),
            }
        else:
            message = {
                "type": "negative",
                "title": f"Error {response.status_code}",
                "text": f"{response.reason}. Please try again!",
            }

        context["message"] = message

        return flask.render_template("careers/base-template.html", **context)

    return flask.render_template("careers/base-template.html", **context)


# Partners
@app.route("/partners/find-a-partner")
def find_a_partner():
    partners = sorted(
        partners_api.get_partner_list(), key=lambda item: item["name"]
    )
    return flask.render_template(
        "/partners/find-a-partner.html", partners=partners
    )


@app.route("/partners/channel-and-reseller")
@app.route("/partners/desktop")
@app.route("/partners/gsi")
@app.route("/partners/ihv-and-oem")
@app.route("/partners/public-cloud")
def partner_details():
    partners = partners_api._get(
        partners_api.partner_page_map[flask.request.path.split("/")[2]]
    )
    return flask.render_template(
        f"{flask.request.path}.html", partners=partners
    )


# Template finder
template_finder_view = TemplateFinder.as_view("template_finder")
app.add_url_rule("/<path:subpath>", view_func=template_finder_view)


@app.context_processor
def inject_today_date():
    return {"current_year": datetime.date.today().year}


@app.template_filter()
def convert_to_kebab(kebab_input):
    words = re.findall(
        r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\d|\W|$)|\d+", kebab_input
    )

    return "-".join(map(str.lower, words))


@app.template_filter()
def get_nav_path(path):
    short_path = ""
    split_path = path.split("/")
    if len(split_path) > 1:
        short_path = path.split("/")[1]
    return short_path


@app.template_filter()
def get_secondary_nav_path(path):
    secondary_path = ""
    split_path = path.split("/")
    if len(split_path) > 2:
        secondary_path = path.split("/")[2]
    return secondary_path


@app.template_filter()
def slug(text):
    return slugify(text)


@app.template_filter()
def markup(text):
    return markdown.markdown(text)


@app.errorhandler(502)
def bad_gateway(e):
    prefix = "502 Bad Gateway: "
    if str(e).find(prefix) != -1:
        message = str(e)[len(prefix) :]
    return flask.render_template("/502.html", message=message), 502
