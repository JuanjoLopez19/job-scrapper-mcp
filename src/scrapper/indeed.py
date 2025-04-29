from dataclasses import dataclass

from bs4 import BeautifulSoup as bs
from pydantic_core import Url

from scrapper.base import JobOfferExtractor


@dataclass(slots=True)
class IndeedScrapper(JobOfferExtractor):
    type: str = "indeed"

    def find_job_offer_info(self, html: bs):
        info = html.find("div", class_="jobsearch-JobComponent")

        return info

    def find_job_description(self, job_offer: bs):
        container = job_offer.find(
            "div", {"class": "jobsearch-JobComponent-description"}
        )
        return container.find("div", {"id": "jobDescriptionText"}).text.strip()

    def find_job_criteria(self, job_offer: bs, **kwargs: bs):
        header = kwargs.get("source").find(
            "div", {"data-testid": "simpler-simplified-header"}
        )
        if header:
            self.offer_title: str = header.find(
                "h2", {"data-testid": "simpler-jobTitle"}
            ).text.strip()

            site_type = (
                header.find(
                    "div", {"data-testid": "jobsearch-JobInfoHeader-companyLocation"}
                )
                .text.strip()
                .split("&nbsp;")[1]
            )

            self.offer_criteria.site_type = site_type.strip()

            detail_section = kwargs.get("source").find(
                "div", {"id": "jobDetailsSection"}
            )

            groups = detail_section.find_all("div", {"role": "group"})

            for group in groups:
                title = group.find("h3").text.strip()
                if title == "Salario":
                    span = group.find("span")
                    if span:
                        self.offer_criteria.salary = span.text.strip()
                    else:
                        self.offer_criteria.salary = None
                elif title == "Tipo de empleo":
                    span = group.find_all("span")
                    if span:
                        self.offer_criteria.worktime_type = ",".join(
                            [s.text.strip() for s in span]
                        )
                    else:
                        self.offer_criteria.worktime_type = None
            return True
        else:
            header = kwargs.get("source").find(
                "div", {"data-testid": "jobsearch-CompanyInfoContainer"}
            )

        # header = job_offer.find(
        #     "div",
        #     {"class": "jobsearch-InfoHeaderContainer jobsearch-DesktopStickyContainer"},
        # )

        # header_container = header.find(
        #     "div", {"data-testid": "jobsearch-CompanyInfoContainer"}
        # )

        # print(header_container.text.strip().split("\n"))

    def get_company_info(self, html: bs):
        header = html.find("div", {"data-testid": "simpler-simplified-header"})

        if header:
            self.company_info.company_name = header.find(
                "span", {"class": "jobsearch-JobInfoHeader-companyNameSimple"}
            ).text.strip()

            self.company_info.company_location = (
                header.find(
                    "div", {"data-testid": "jobsearch-JobInfoHeader-companyLocation"}
                )
                .text.split("&nbsp;")[0]
                .strip()
            )

            return True
        else:
            header = html.find("div", {"data-testid": "jobsearch-CompanyInfoContainer"})

            if not header:
                return False

            a_tag = header.find("a")

            if a_tag:
                self.company_info.company_name = a_tag.text.strip()
                self.company_info.company_url = Url(a_tag.get("href"))

            self.company_info.company_location = header.find(
                "div", {"data-testid": "inlineHeader-companyLocation"}
            ).text.strip()

            return True


if __name__ == "__main__":
    from pydantic_core import Url

    from scrapper.factory import FactoryScrapper

    url = Url(
        "https://es.indeed.com/viewjob?jk=eb3fab2db3e35ef2&from=shareddesktop_copy"
    )

    scrapper: IndeedScrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    scrapper.console.print(scrapper.get_extraction_result())
