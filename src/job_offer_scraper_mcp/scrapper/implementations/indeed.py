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
    description: str | None = None
    criteria: str | None = None

    def find_job_offer_info(self, html: bs):
        info = html.find("div", class_="jobsearch-JobComponent")

        return info

    def find_job_description(self, html: bs):
        container = html.find("div", {"class": "jobsearch-JobComponent-description"})

        if container is None:
            return None

        container = cast(Tag, container)
        description = container.find("div", {"id": "jobDescriptionText"})
        if description is None:
            return None
        return description.text.strip()

    def find_job_criteria(self, html: bs, **kwargs):
        return None
        # header = job_offer.find(
        #     "div",
        #     {"class": "jobsearch-InfoHeaderContainer jobsearch-DesktopStickyContainer"},
        # )

        # header_container = header.find(
        #     "div", {"data-testid": "jobsearch-CompanyInfoContainer"}
        # )

        # print(header_container.text.strip().split("\n"))


if __name__ == "__main__":
    from pydantic_core import Url

    from job_offer_scraper_mcp.scrapper.factory import FactoryScrapper

    url = Url(argv[1])

    scrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    print(scrapper.get_job_description())
    print(scrapper.get_job_criteria())
