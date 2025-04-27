from dataclasses import dataclass

from bs4 import BeautifulSoup as bs
from pydantic_core import Url
from rich.console import Console

from scrapper.base import JobOfferExtractor

console = Console(record=True)


@dataclass(slots=True)
class LinkedinScrapper(JobOfferExtractor):
    type: str = "linkedin"

    def find_job_offer_info(self, html: bs):
        job_offer = html.find("section", class_="core-section-container")
        if job_offer is None:
            return None
        return job_offer

    def find_job_description(self, job_offer: bs):
        description = job_offer.find("div", class_="show-more-less-html__markup")
        if description is None:
            return False

        self.offer_description = description.text.strip()
        return True

    def find_job_criteria(self, job_offer: bs, **kwargs: bs):
        if (
            "remote" in self.offer_description.lower()
            or "teletrabajo" in self.offer_description.lower()
        ):
            self.offer_criteria.site_type = "remote"
        else:
            self.offer_criteria.site_type = "on-site"

        ul = job_offer.find("ul", class_="description__job-criteria-list")

        if ul is None:
            return False

        li_items = ul.find_all("li")
        for li in li_items:
            item_title = li.find("h3").text.strip()
            item_value = li.find("span").text.strip()
            if item_title in ["Nivel de antigüedad"]:
                self.offer_criteria.profesional_level = item_value
            elif item_title in ["Tipo de empleo"]:
                self.offer_criteria.worktime_type = item_value
            elif item_title in ["Función laboral"]:
                self.offer_criteria.function = item_value

        self.offer_criteria.contract_type = "permanent"
        self.offer_criteria.salary = "not specified"

        return True

    def get_company_info(self, html: bs) -> bool:
        self.offer_title = html.find("h1", class_="top-card-layout__title").text.strip()
        header = html.find("div", class_="top-card-layout__card")
        if not header:
            return False

        topcard_flavors = header.find_all("span", class_="topcard__flavor")
        for topcard in topcard_flavors:
            a_tag = topcard.find("a")
            if a_tag and a_tag.has_attr("href"):
                self.company_info.company_website = Url(a_tag["href"])
                self.company_info.company_name = a_tag.text.strip()
            else:
                self.company_info.company_location = topcard.text.strip()

        return True


if __name__ == "__main__":
    from scrapper.factory import FactoryScrapper

    url = "https://es.linkedin.com/jobs/view/frontend-developer-html-css-javascript-indonesia-at-crisp-studio-4160063116?refId=1DKRX95K2N39AzMBr%2FAeIg%3D%3D&trackingId=1HAUIGlM1RVfbZI7mOTgZg%3D%3D"

    scrapper: LinkedinScrapper = FactoryScrapper.get_scrapper(Url(url))
    scrapper.extract()
    print(scrapper.get_extraction_result())
