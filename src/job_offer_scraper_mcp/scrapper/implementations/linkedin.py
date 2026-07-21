import re
from dataclasses import dataclass
from sys import argv
from typing import cast

from bs4 import BeautifulSoup as bs
from bs4 import Tag
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

    def find_job_description(self, html: bs):
        description = html.find("div", class_="show-more-less-html__markup")
        if description is None:
            return None

        return description.text.strip()

    def find_job_criteria(self, html: bs):
        criteria = html.find("ul", class_="description__job-criteria-list")
        if criteria is None:
            return None
        items = cast(Tag, criteria).find_all("li")
        criteria_list = []
        for li in items:
            if self.type not in criteria_handler:
                return None
            li = cast(Tag, li)
            h3 = li.find("h3")
            if h3 is None:
                return None
            title = criteria_handler[self.type][h3.text.strip()]
            level = li.find("span")
            if level is None:
                return None
            level = level.text.strip()
            if level is None:
                return None
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

    scrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    print(scrapper.get_job_description())
    print(scrapper.get_job_criteria())
