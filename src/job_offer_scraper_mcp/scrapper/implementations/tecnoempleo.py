import json
import re
from dataclasses import dataclass
from typing import cast

from bs4 import BeautifulSoup as bs
from bs4 import Tag

from job_offer_scraper_mcp.scrapper.base import JobOfferExtractor
from job_offer_scraper_mcp.scrapper.config import SupportedSites


@dataclass(slots=True)
class TecnoEmpleoScrapper(JobOfferExtractor):
    type: str = SupportedSites.TECNO_EMPLEO.value
    job_offer_title_pattern = re.compile(
        r"^Oferta de Empleo\s+(?P<title>.+?)\s+en\s+"
        r"(?P<location>.+?),\s+(?P<company>.+?)"
        r"(?:\s+-\s+Tecnoempleo\.com)?$"
    )

    icons_map = {
        "fi-pin": "location",
        "fi-shield-ok": "experience",
        "fi-calendar": "working_time",
        "fi-users": "function",
        "fi-task-list": "contract_type",
        "fi-plus": "salary",
    }

    def find_job_offer_info(self, html: bs):
        return html

    def find_job_description(self, html: bs):
        script = html.find("script", type="application/ld+json")
        if script is None:
            return None

        data = json.loads(cast(Tag, script).string or "")
        if data is None:
            return None
        return data.get("description", "No description available")

    def find_job_criteria(self, html: bs):
        criteria_list = []

        criteria_container = html.select_one("div[class='mt-0']")
        if criteria_container is None:
            return None
        criteria_list_tag = criteria_container.find_next("ul")
        if not isinstance(criteria_list_tag, Tag):
            return None
        list_items = criteria_list_tag.find_all("li")

        for item in list_items:
            item = cast(Tag, item)
            icon = item.find("i", {"class": "fi"})
            if icon is None:
                continue
            icon = cast(Tag, icon)
            icon_class = icon.get("class")
            if icon_class is None:
                continue
            icon_class = icon_class[1]
            icon_name = self.icons_map.get(icon_class)
            if icon_name is None:
                continue
            content = item.find("span", {"class": "float-end"})
            if content is None:
                continue
            content = content.text.strip()
            criteria_list.append(f"{icon_name}: {content}")

        return "\n".join(criteria_list)

    def find_job_title(self, html: bs):
        title_tag = html.find("title")

        if title_tag is None:
            return None
        content = title_tag.text.strip()
        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group("title")

    def find_job_company(self, html: bs):
        title_tag = html.find("title")

        if title_tag is None:
            return None
        content = title_tag.text.strip()
        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group("company")

    def find_job_location(self, html: bs):
        title_tag = html.find("title")
        if title_tag is None:
            return None
        content = title_tag.text.strip()
        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group("location")


if __name__ == "__main__":
    from sys import argv

    from pydantic_core import Url

    from job_offer_scraper_mcp.scrapper.factory import FactoryScrapper

    url = Url(argv[1])

    scrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    print(scrapper.get_job_criteria())
