from dataclasses import dataclass

from bs4 import BeautifulSoup as bs

from scrapper.base import JobOfferExtractor


@dataclass(slots=True)
class IndeedScrapper(JobOfferExtractor):
    type: str = "indeed"
    description: str | None = None
    criteria: str | None = None

    def find_job_offer_info(self, html: bs):
        return html

    def find_job_description(self, job_offer: bs):
        return ""

    def find_job_criteria(self, job_offer: bs):
        return ""


if __name__ == "__main__":
    from pydantic_core import Url

    from scrapper.factory import FactoryScrapper

    url = Url(
        "https://es.indeed.com/viewjob?jk=eb3fab2db3e35ef2&from=shareddesktop_copy"
    )

    scrapper: IndeedScrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    print(scrapper.get_job_description())
    print(scrapper.get_job_criteria())
