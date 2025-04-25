from dataclasses import dataclass

from bs4 import BeautifulSoup as bs

from scrapper.base import JobOfferExtractor
from shared.constants import criteria_handler


@dataclass(slots=True)
class LinkedinScrapper(JobOfferExtractor):
    type: str = "linkedin"
    description: str | None = None
    criteria: str | None = None

    def find_job_offer_info(self, html: bs):
        job_offer = html.find("section", class_="core-section-container")
        if job_offer is None:
            return None
        return job_offer

    def find_job_description(self, job_offer: bs):
        description = job_offer.find("div", class_="show-more-less-html__markup")
        if description is None:
            return None

        return description.text.strip()

    def find_job_criteria(self, job_offer: bs):
        criteria = job_offer.find("ul", class_="description__job-criteria-list")
        if criteria is None:
            return None
        items = criteria.find_all("li")
        criteria_list = []
        for li in items:
            title = criteria_handler.get(self.type)[li.find("h3").text.strip()]
            level = li.find("span").text.strip()
            criteria_list.append(f"{title}: {level}")
        return "\n".join(criteria_list)


if __name__ == "__main__":
    from scrapper.factory import FactoryScrapper

    url = ""

    scrapper: LinkedinScrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    print(scrapper.get_job_description())
    print(scrapper.get_job_criteria())
