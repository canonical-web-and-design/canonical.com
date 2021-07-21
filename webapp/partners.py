class Partners:
    base_url = "https://partners.ubuntu.com/partners.json"

    partner_page_map = {
        "channel-and-reseller": "programme__name=Channel%20/%20Reseller"
        "&featured=true",
        "desktop": "programme__name=Desktop&featured=true",
        "devices-and-iot": "programme__name=Internet%20of%20Things"
        "&featured=true",
        "ihv-and-oem": "programme__name=IHV%20%2F%20OEM&featured=true",
        "iot": "programme__name=Internet%20of%20Things&featured=true",
        "gsi": "programme__name=Global%20System%20Integrators&featured=true",
        "public-cloud": "programme__name=Public%20Cloud&featured=true",
        "software": "programme__name=ISV",
    }

    def __init__(self, session):
        self.session = session

    def _get(self, query=""):
        if query:
            return self.session.get(f"{self.base_url}?{query}").json()[:10]
        else:
            return self.session.get(self.base_url).json()

    def get_partner_groups(self):
        return {
            "Apps & snaps": self._get("programme__name=Desktop&featured=true"),
            "Channel / Reseller": self._get(
                "programme__name=Channel%20/%20Reseller&featured=true"
            ),
            "Charms": self._get(
                "programme__name=Charm%20Partner%20Programme&featured=true"
            ),
            "Cloud": self._get("technology__name=Cloud/server&featured=true"),
            "Desktop": self._get("programme__name=Desktop&featured=true"),
            "IHV / OEM": self._get(
                "programme__name=IHV%20/%20OEM&featured=true"
            ),
            "Devices": self._get("programme__name=Desktop&featured=true"),
            "Internet of Things": self._get(
                "programme__name=Internet%20of%20Things&featured=true"
            ),
            "Global System Integrators": self._get(
                "programme__name=Global%20System%20Integrators&featured=true"
            ),
            "Hosting": self._get(
                "service__offered=Hosting%20provider&featured=true"
            ),
            "Kubernetes": self._get("programme__name=Desktop&featured=true"),
            "OpenStack": self._get("programme__name=Desktop&featured=true"),
            "PAAS": self._get("programme__name=Desktop&featured=true"),
            "Server": self._get("technology__name=Cloud/server&featured=true"),
            "Serverless": self._get("programme__name=Desktop&featured=true"),
            "Silicon": self._get("programme__name=Desktop&featured=true"),
            "Snapcraft": self._get(
                "programme__name=Internet%20of%20Things&featured=true"
            ),
            "Software": self._get("programme__name=ISV"),
            "Training": self._get("programme__name=Desktop&featured=true"),
        }

    def get_partner_list(self):
        return self._get()
