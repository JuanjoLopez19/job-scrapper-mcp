import json
from dataclasses import dataclass
from sys import argv
from typing import cast

from bs4 import BeautifulSoup as bs
from bs4 import Tag

from job_offer_scraper_mcp.scrapper.base import JobOfferExtractor
from job_offer_scraper_mcp.scrapper.config import SupportedSites


@dataclass(slots=True)
class IndeedScrapper(JobOfferExtractor):
    type: str = SupportedSites.INDEED.value

    job_type_map = {
        "FULL_TIME": "Full-time",
        "PART_TIME": "Part-time",
        "CONTRACT": "Contract",
        "TEMPORARY": "Temporary",
        "INTERN": "Intern",
    }

    def find_job_offer_info(self, html: bs):
        return html

    def find_job_description(self, html: bs):

        data = self.__load_json_data(html)
        if data is None:
            return None
        return data.get("description", "No description available")

    def find_job_criteria(self, html: bs, **kwargs):
        data = self.__load_json_data(html)
        if data is None:
            return None

        criteria_list = []
        if "employmentType" in data:
            employment_type = self.job_type_map.get(
                data["employmentType"][0], "Unknown"
            )
            criteria_list.append(f"Employment type: {employment_type}")

        if "baseSalary" in data:
            base_salary = data["baseSalary"]["value"]
            if "maxValue" in base_salary:
                max_base_salary = base_salary["maxValue"]
            else:
                max_base_salary = "Not specified"
            if "minValue" in base_salary:
                min_base_salary = base_salary["minValue"]
            else:
                min_base_salary = "Not specified"
            criteria_list.append(f"Base salary:{min_base_salary}-{max_base_salary}")

        if "jobLocationType" in data:
            job_location_type = data["jobLocationType"]
            criteria_list.append(f"Job location type: {job_location_type}")

        if "applicantLocationRequirements" in data:
            applicant_location_requirements = data["applicantLocationRequirements"]
            criteria_list.append(
                f"Applicant location requirements: {json.dumps(applicant_location_requirements)}"
            )

        return "\n".join(criteria_list)

    def find_job_title(self, html: bs):
        data = self.__load_json_data(html)
        if data is None:
            return None
        return data.get("title", "No title available")

    def find_job_company(self, html: bs):
        data = self.__load_json_data(html)
        if data is None:
            return None

        if "hiringOrganization" in data:
            return data["hiringOrganization"]["name"]

    def find_job_location(self, html: bs):
        data = self.__load_json_data(html)
        if data is None:
            return None

        if "jobLocation" in data:
            return data["jobLocation"]["address"]["addressLocality"]

    def __load_json_data(self, html: bs) -> dict | None:
        script = html.find("script", type="application/ld+json")
        if script is None:
            return None

        return json.loads(cast(Tag, script).string or "")


if __name__ == "__main__":
    from pydantic_core import Url

    from job_offer_scraper_mcp.scrapper.factory import FactoryScrapper

    url = Url(argv[1])

    scrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    print(scrapper.get_job_offer_info())
