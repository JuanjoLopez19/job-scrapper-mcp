import re
from dataclasses import dataclass
from sys import argv

from bs4 import BeautifulSoup as bs
from pydantic_core import Url

from job_offer_scraper_mcp.scrapper.base import JobOfferExtractor
from job_offer_scraper_mcp.scrapper.config import SupportedSites
from job_offer_scraper_mcp.shared.constants import criteria_handler


@dataclass(slots=True)
class LinkedinScrapper(JobOfferExtractor):
    type: str = SupportedSites.LINKEDIN.value

    job_offer_title_pattern = re.compile(
        r"^(.+?)\s+hiring\s+(.+)\s+in\s+(.+?)\s+\|\s+LinkedIn$"
    )

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

    def find_job_title(self, html: bs):
        title_tag = html.find("title")
        if title_tag is None:
            return None
        content = title_tag.text.strip()

        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group(2)

    def find_job_company(self, html: bs):
        title_tag = html.find("title")
        if title_tag is None:
            return None
        content = title_tag.text.strip()
        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group(1)

    def find_job_location(self, html: bs):
        title_tag = html.find("title")
        if title_tag is None:
            return None
        content = title_tag.text.strip()
        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group(3)


if __name__ == "__main__":
    from job_offer_scraper_mcp.scrapper.factory import FactoryScrapper

    url = Url(argv[1])

    scrapper: LinkedinScrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    print(scrapper.get_job_description())
    print(scrapper.get_job_criteria())
