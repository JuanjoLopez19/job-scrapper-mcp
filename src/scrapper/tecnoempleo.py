import json
from dataclasses import dataclass

from bs4 import BeautifulSoup as bs
from pydantic_core import Url

from scrapper.base import JobOfferExtractor


@dataclass(slots=True)
class TecnoEmpleoScrapper(JobOfferExtractor):
    type: str = "tecnoempleo"

    def find_job_offer_info(self, html: bs):
        return html

    def find_job_description(self, job_offer: bs):
        script = job_offer.find("script", type="application/ld+json")
        if script is None:
            return False

        data = json.loads(script.string)
        if data is None:
            return False
        self.offer_description = data.get("description", None)
        return True

    def find_job_criteria(self, job_offer: bs, **kwargs: bs):
        list_items = (
            job_offer.select_one("div[class='mt-0']").find_next("ul").find_all("li")
        )

        items = list_items[: len(list_items) - 1]

        for item in items:
            if item.find("span") is not None:
                span = item.find("span")
                span_text = span.text.strip().replace("\t", "").replace("\n", "")
                tag = span.next_sibling.next_sibling.next_sibling.next_sibling.text.strip()
                self.console.print(f"Tag: {tag}, Span: {span_text}", style="bold green")
                if tag == "Funciones":
                    self.offer_criteria.function = span_text
                elif tag == "Jornada":
                    self.offer_criteria.worktime_type = span_text
                elif tag == "Tipo contrato":
                    self.offer_criteria.contract_type = span_text
                elif tag == "Experiencia":
                    self.offer_criteria.profesional_level = span_text
                elif tag == "Salario":
                    self.offer_criteria.salary = span_text.replace("\xa0", " ")
                elif tag == "":
                    self.offer_criteria.site_type = span_text

        return True

    def get_company_info(self, html):
        self.offer_title = html.find("h1", {"itemprop": "title"}).text.strip()

        script = html.find("script", type="application/ld+json")

        if script is None:
            return None

        data = json.loads(script.string)

        self.company_info.company_name = data.get("hiringOrganization", {}).get(
            "name", None
        )

        self.company_info.company_location = (
            data.get("jobLocation", {}).get("address", {}).get("addressRegion", None)
        )

        self.company_info.company_website = Url(
            html.find("h1", {"itemprop": "title"}).parent.next_sibling.next_sibling.get(
                "href"
            )
        )


if __name__ == "__main__":
    from scrapper.factory import FactoryScrapper

    url = "https://www.tecnoempleo.com/programador-python-flask-django-pss/python-flask-fastapi-django-sql-nosql-/rf-0009129f72ee338a674b"

    scrapper: TecnoEmpleoScrapper = FactoryScrapper.get_scrapper(Url(url))
    scrapper.extract()

    scrapper.console.print(scrapper.get_extraction_result())
