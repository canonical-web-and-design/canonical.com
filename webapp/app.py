# Standard library
import datetime
import flask
import markdown
import re
import time


# Packages
from canonicalwebteam.flask_base.app import FlaskBase
from canonicalwebteam.templatefinder import TemplateFinder
from slugify import slugify


# Local
from webapp.greenhouse_api import (
    get_vacancies,
    get_vacancies_by_skills,
    get_vacancy,
    submit_to_greenhouse,
)
from webapp.partners_api import get_partner_groups, get_partner_list

app = FlaskBase(
    __name__,
    "canonical.com",
    template_folder="../templates",
    static_folder="../static",
    template_404="404.html",
    template_500="500.html",
)


@app.route("/")
def index():
    partner_groups = get_partner_groups()
    return flask.render_template("index.html", partner_groups=partner_groups)


# Career departments
@app.route("/careers/results")
def results():
    context = {}
    vacancies = []
    departments = []
    message = ""
    if flask.request.args:
        core_skills = flask.request.args["coreSkills"].split(",")
        context["core_skills"] = core_skills
        vacancies = get_vacancies_by_skills(core_skills)
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


@app.route("/careers/thank-you", methods=["POST"])
def careers_thank_you():
    messages = []
    job_id_list = flask.request.form.get("applicationJobIdList").split(",")
    job_title_list = flask.request.form.get("applicationJobTitleList").split(
        ","
    )
    print(flask.request.form)
    i = 0
    while i < len(job_id_list):
        response = submit_to_greenhouse(
            flask.request.form, flask.request.files, job_id_list[i]
        )
        if response.status_code == 200:
            messages.append(
                {
                    "type": "success",
                    "title": f"{job_title_list[i]}",
                    "text": ("Successfully submitted."),
                }
            )
        else:
            messages.append(
                {
                    "type": "error",
                    "title": f"{job_title_list[i]}",
                    "text": (
                        f"Error {response.status_code}. {response.reason}."
                        "<br /><a href='/careers/{job_id_list[i]}' "
                        "style='padding-left: 2rem;'>"
                        "Please try to apply to this job again!</a>"
                    ),
                    "response": response,
                }
            )
        i = i + 1
        # time.sleep(60)
    if len(messages) > 0:
        return flask.render_template(
            "careers/thank-you.html", messages=messages
        )
    else:
        return flask.redirect("/careers")


@app.route(
    "/careers/<regex('[a-z-]*[a-z][a-z-]*'):department>",
    methods=["GET", "POST"],
)
def department_group(department):
    vacancies = get_vacancies(department)
    if flask.request.method == "POST":
        response = submit_to_greenhouse(
            flask.request.form, flask.request.files
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

        return flask.render_template(
            f"careers/{department}.html", vacancies=vacancies, message=message
        )

    return flask.render_template(
        f"careers/{department}.html", vacancies=vacancies
    )


@app.route("/careers/<regex('[0-9]+'):job_id>")
def job_details(job_id):
    job = get_vacancy(job_id)

    return flask.render_template("/careers/job/job-detail.html", job=job)


# Partners
@app.route("/partners/find-a-partner")
def find_a_partner():
    partners = sorted(get_partner_list(), key=lambda item: item["name"])
    return flask.render_template(
        "/partners/find-a-partner.html", partners=partners
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
    short_path = path.split("/")[1]

    return short_path


@app.template_filter()
def slug(text):
    return slugify(text)


@app.template_filter()
def markup(text):
    return markdown.markdown(text)
