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
class InfoJobsScrapper(JobOfferExtractor):
    type: str = SupportedSites.INFOJOBS.value
    job_offer_title_pattern = re.compile(r"^Oferta de empleo:\s(.*)en\s(.*)\s-")
    job_offer_company_pattern = re.compile(r"en la empresa\s(.*)\.\s")

    def find_job_offer_info(self, html: bs):
        container = html.find(
            "div", {"class": "ij-Box ij-OfferDetailPage-mainContent-container"}
        )
        if container is None:
            return None

        return container

    def find_job_description(self, html: bs):
        section = html.find_all("article")
        if len(section) < 2:
            return None

        section = cast(Tag, section[1])
        div = section.find(
            "div", {"class": "ij-Box mb-xl mt-l ij-EnrichedTextArea-paragraph"}
        )

        if div is None:
            return None

        return div.text.strip()

    def find_job_criteria(self, html: bs):
        section = html.find_all("article")
        if len(section) < 2:
            return None

        dl_tag = cast(Tag, section[0]).find("dl")
        if dl_tag is None:
            return None
        dl_tag = cast(Tag, dl_tag)
        criteria_1 = self.__extract_criteria(dl_tag)

        dl_tag = cast(Tag, section[1]).find("dl")
        if dl_tag is None:
            return None
        dl_tag = cast(Tag, dl_tag)
        criteria_2 = self.__extract_criteria(dl_tag)
        return f"{criteria_1}\n{criteria_2}".strip()

    def find_job_title(self, html: bs):
        title_tag = html.find("title")

        if title_tag is None:
            return None
        content = title_tag.text.strip()
        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group(1).strip()

    def find_job_company(self, html: bs):
        meta_tag = html.find("meta", {"name": "description"})
        if meta_tag is None:
            return None
        meta_tag = cast(Tag, meta_tag)
        content = meta_tag.get("content", "")
        if content is None:
            return None
        match = self.job_offer_company_pattern.search(cast(str, content))
        if match is None:
            return None
        return match.group(1).strip()

    def find_job_location(self, html: bs):
        title_tag = html.find("title")

        if title_tag is None:
            return None
        content = title_tag.text.strip()
        match = self.job_offer_title_pattern.search(content)
        if match is None:
            return None
        return match.group(2).strip()

    def __extract_criteria(self, dl_tag: Tag):
        dd_tags = dl_tag.find_all("dd")
        dt_tags = dl_tag.find_all("dt")
        criteria = ""
        for dd_tag, dt_tag in zip(dd_tags, dt_tags, strict=False):
            dt_tag_text = dt_tag.text.strip()
            if dt_tag_text == "Conocimientos necesarios":
                a_tags = cast(Tag, dd_tag).find_all("a")
                knowledge = []
                if a_tags is not None and len(a_tags) > 0:
                    for a_tag in a_tags:
                        knowledge.append(a_tag.text.strip())
                criteria += f"{dt_tag_text}: {', '.join(knowledge)}\n"
            else:
                criteria += f"{dt_tag.text.strip()}: {dd_tag.text.strip()}\n"

        return criteria.strip()


if __name__ == "__main__":
    from pprint import pprint

    from job_offer_scraper_mcp.scrapper.factory import FactoryScrapper

    url = Url(argv[1])

    scrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    pprint(scrapper.get_job_offer_info().model_dump())
