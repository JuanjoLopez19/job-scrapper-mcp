import json
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup as bs

from job_offer_scraper_mcp.scrapper.base import JobOfferExtractor
from job_offer_scraper_mcp.scrapper.config import SupportedSites


@dataclass(slots=True)
class IndeedScrapper(JobOfferExtractor):
    type: str = SupportedSites.INDEED.value
    structured_data_selector = 'script[type="application/ld+json"]'

    job_type_map = {
        "FULL_TIME": "Full-time",
        "PART_TIME": "Part-time",
        "CONTRACT": "Contract",
        "TEMPORARY": "Temporary",
        "INTERN": "Intern",
    }

    def is_browser_fallback_required(self, html: bs) -> bool:
        return self.__load_json_data(html) is None

    def get_browser_ready_selector(self) -> str:
        return self.structured_data_selector

    def find_job_offer_info(self, html: bs):
        return html

    def find_job_description(self, html: bs):
        data = self.__load_json_data(html)
        if data is None:
            return None

        description = data.get("description")
        if not isinstance(description, str):
            return None

        return bs(description, "html.parser").get_text("\n", strip=True)

    def find_job_criteria(self, html: bs, **kwargs):
        data = self.__load_json_data(html)
        if data is None:
            return None

        criteria_list = []
        employment_types = data.get("employmentType")
        if isinstance(employment_types, str):
            employment_types = [employment_types]
        if isinstance(employment_types, list):
            formatted_types = [
                self.job_type_map.get(value, "Unknown")
                for value in employment_types
                if isinstance(value, str)
            ]
            if formatted_types:
                criteria_list.append(f"Employment type: {', '.join(formatted_types)}")

        salary = data.get("baseSalary")
        if isinstance(salary, dict) and isinstance(salary.get("value"), dict):
            base_salary = salary["value"]
            if "maxValue" in base_salary:
                max_base_salary = base_salary["maxValue"]
            else:
                max_base_salary = "Not specified"
            if "minValue" in base_salary:
                min_base_salary = base_salary["minValue"]
            else:
                min_base_salary = "Not specified"
            criteria_list.append(f"Base salary:{min_base_salary}-{max_base_salary}")

        job_location_type = data.get("jobLocationType")
        if isinstance(job_location_type, str):
            criteria_list.append(f"Job location type: {job_location_type}")

        applicant_location_requirements = data.get("applicantLocationRequirements")
        if applicant_location_requirements is not None:
            criteria_list.append(
                "Applicant location requirements: "
                f"{json.dumps(applicant_location_requirements, ensure_ascii=False)}"
            )

        return "\n".join(criteria_list)

    def find_job_title(self, html: bs):
        data = self.__load_json_data(html)
        if data is None:
            return None
        title = data.get("title")
        return title if isinstance(title, str) else None

    def find_job_company(self, html: bs):
        data = self.__load_json_data(html)
        if data is None:
            return None

        hiring_organization = data.get("hiringOrganization")
        if isinstance(hiring_organization, dict):
            name = hiring_organization.get("name")
            return name if isinstance(name, str) else None

        return None

    def find_job_location(self, html: bs):
        data = self.__load_json_data(html)
        if data is None:
            return None

        job_location = data.get("jobLocation")
        if isinstance(job_location, list):
            job_location = next(
                (location for location in job_location if isinstance(location, dict)),
                None,
            )
        if not isinstance(job_location, dict):
            return None

        address = job_location.get("address")
        if not isinstance(address, dict):
            return None

        locality = address.get("addressLocality")
        return locality if isinstance(locality, str) else None

    def __load_json_data(self, html: bs) -> dict[str, Any] | None:
        for script in html.select(self.structured_data_selector):
            try:
                payload = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue

            candidates = payload if isinstance(payload, list) else [payload]
            if isinstance(payload, dict) and isinstance(payload.get("@graph"), list):
                candidates.extend(payload["@graph"])

            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                schema_type = candidate.get("@type")
                schema_types = (
                    schema_type if isinstance(schema_type, list) else [schema_type]
                )
                if "JobPosting" in schema_types:
                    return candidate

        return None


if __name__ == "__main__":
    from sys import argv

    from pydantic_core import Url

    from job_offer_scraper_mcp.scrapper.factory import FactoryScrapper

    url = Url(argv[1])

    scrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    print(scrapper.get_job_offer_info())
