from dataclasses import dataclass

from bs4 import BeautifulSoup as bs

from scrapper.base import JobOfferExtractor


@dataclass(slots=True)
class IndeedScrapper(JobOfferExtractor):
    type: str = "indeed"
    description: str | None = None
    criteria: str | None = None

    def find_job_offer_info(self, html: bs):
        info = html.find("div", class_="jobsearch-JobComponent")

        return info

    def find_job_description(self, job_offer: bs):
        container = job_offer.find(
            "div", {"class": "jobsearch-JobComponent-description"}
        )
        return container.find("div", {"id": "jobDescriptionText"}).text.strip()

    def find_job_criteria(self, job_offer: bs, **kwargs):
        header = job_offer.find(
            "div",
            {"class": "jobsearch-InfoHeaderContainer jobsearch-DesktopStickyContainer"},
        )

        header_container = header.find(
            "div", {"data-testid": "jobsearch-CompanyInfoContainer"}
        )

        print(header_container.text.strip().split("\n"))


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
