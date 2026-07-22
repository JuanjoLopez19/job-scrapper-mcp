import re
from dataclasses import dataclass
from sys import argv
from typing import cast

from bs4 import BeautifulSoup as bs
from bs4 import Tag
from pydantic_core import Url

from job_offer_scraper_mcp.scrapper.base import JobOfferExtractor
from job_offer_scraper_mcp.scrapper.config import SupportedSites


@dataclass(slots=True)
class InfoEmpleoScrapper(JobOfferExtractor):
    type: str = SupportedSites.INFO_EMPLEO.value
    job_offer_title_pattern = re.compile(
        r"^(.+?)\s+en\s+([^|]+?)(?:\s*\|\s*Infoempleo)?$"
    )

    def find_job_offer_info(self, html: bs):
        return html

    def find_job_description(self, html: bs):
        description = html.find("div", {"class": "offer"})
        if description is None:
            return None
        return description.text.strip()

    def find_job_criteria(self, html: bs):
        criteria = html.find("div", {"class": "offer-excerpt"})
        if criteria is None:
            return None
        ul = cast(Tag, criteria).find_all("ul", {"class": "inline"})
        if not ul:
            return None
        criteria_list = []
        row_1 = cast(Tag, ul[1])
        row_2 = cast(Tag, ul[3])

        type = cast(Tag, row_2.find_all("li").pop()).find("p")
        if type is None:
            return None
        type = type.text.strip()

        function = row_1.find("ul", {"class": "position-name"})
        if function is None:
            return None
        function = cast(Tag, function).text.strip()

        level = cast(Tag, row_1.find_all("li").pop()).find("p")
        if level is None:
            return None
        level = level.text.strip()

        industry = (
            row_1.select("div[class='multipos-visible-content'] p:nth-child(1)")
            .pop()
            .find("strong")
        )
        if industry is None:
            return None
        industry = industry.text.strip()

        criteria_list.append(f"type: {type}")
        criteria_list.append(f"function: {function}")
        criteria_list.append(f"level: {level}")
        criteria_list.append(f"industry: {industry}")

        return "\n".join(criteria_list)

    def find_job_title(self, html: bs):
        title_tag = html.find("title")

        if title_tag is None:
            return None
        content = title_tag.text.strip()
        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group(1)

    def find_job_company(self, html: bs):
        company_info_ul = html.find("ul", {"class": "details companyjobtype"})
        if company_info_ul is None:
            return None

        company_info_li = cast(Tag, company_info_ul).select_one("li.companyname")
        if company_info_li is None:
            return None
        company_name = cast(Tag, company_info_li.select_one("a"))

        if company_name is None:
            return None

        return company_name.get_text(" ", strip=True)

    def find_job_location(self, html: bs):
        title_tag = html.find("title")
        if title_tag is None:
            return None
        content = title_tag.text.strip()
        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group(2)


if __name__ == "__main__":
    from job_offer_scraper_mcp.scrapper.factory import FactoryScrapper

    url = Url(argv[1])

    scrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    print(scrapper.get_job_description())
    print(scrapper.get_job_criteria())
