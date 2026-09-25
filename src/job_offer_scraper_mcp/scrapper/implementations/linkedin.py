import re
from dataclasses import dataclass

from bs4 import BeautifulSoup as bs

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
        for section in html.find_all("section", class_="core-section-container"):
            if section.find("div", class_="show-more-less-html__markup"):
                return section

        if html.find("div", class_="show-more-less-html__markup"):
            return html
        return None

    def find_job_description(self, html: bs):
        description = html.find("div", class_="show-more-less-html__markup")
        if description is None:
            return None

        return description.text.strip()

    def find_job_criteria(self, html: bs):
        criteria = html.find("ul", class_="description__job-criteria-list")
        if criteria is None:
            return None
        items = criteria.find_all("li")
        criteria_list = []
        for li in items:
            if self.type not in criteria_handler:
                return None
            li = li
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
        title = html.find("h1", class_="topcard__title")
        if title is not None:
            return title.get_text(" ", strip=True)

        title_tag = html.find("title")
        if title_tag is None:
            return None
        content = title_tag.text.strip()

        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group(2)

    def find_job_company(self, html: bs):
        company = html.find("a", class_="topcard__org-name-link")
        if company is not None:
            return company.get_text(" ", strip=True)

        title_tag = html.find("title")
        if title_tag is None:
            return None
        content = title_tag.text.strip()
        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group(1)

    def find_job_location(self, html: bs):
        location = html.find("span", class_="topcard__flavor--bullet")
        if location is not None:
            return location.get_text(" ", strip=True)

        title_tag = html.find("title")
        if title_tag is None:
            return None
        content = title_tag.text.strip()
        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group(3)


if __name__ == "__main__":
    from sys import argv

    from pydantic_core import Url

    from job_offer_scraper_mcp.scrapper.factory import FactoryScrapper

    url = Url(argv[1])

    scrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    print(scrapper.get_job_offer_info())
