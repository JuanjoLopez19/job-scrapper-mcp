from dataclasses import dataclass

from bs4 import BeautifulSoup as bs
from pydantic_core import Url

from scrapper.base import JobOfferExtractor


@dataclass(slots=True)
class InfoEmpleoScrapper(JobOfferExtractor):
    type: str = "info_empleo"
    description: str | None = None
    criteria: str | None = None

    def find_job_offer_info(self, html: bs):
        return html

    def find_job_description(self, job_offer: bs):
        description = job_offer.find("div", {"class": "offer"})
        if description is None:
            return False
        self.offer_description = description.text.strip()
        return True

    def find_job_criteria(self, job_offer: bs, **kwargs: bs):
        criteria = job_offer.find("div", {"class": "offer-excerpt"})
        if criteria is None:
            return False
        ul_items = criteria.find_all("ul", {"class": "inline"})
        if not ul_items:
            return False

        for ul in ul_items:
            p_items = ul.find_all("p")

            h3_items = ul.find_all("h3")

            for h3, p in zip(h3_items, p_items):
                title = h3.text.strip()
                value = p.find(text=True).strip()
                if title in ["Experiencia"]:
                    self.offer_criteria.profesional_level = value
                elif title in ["Salario"]:
                    self.offer_criteria.salary = value
                elif title in ["Área - Puesto"]:
                    self.offer_criteria.function = value
                elif title in ["Contrato"]:
                    self.offer_criteria.contract_type = value
                elif title in ["Jornada"]:
                    self.offer_criteria.worktime_type = value

        return True

    def get_company_info(self, html):
        header = html.find("div", class_="main-title")
        if header is None:
            return False

        self.offer_title = header.find("h1", class_="h1").text.strip()
        ul_company_item = header.find("ul", class_="details companyjobtype")
        if ul_company_item is None:
            return False

        a_tag = ul_company_item.find("a")
        if a_tag:
            self.company_info.company_name = a_tag.text.strip()
            url = (
                a_tag["href"]
                if "infoempleo" in a_tag["href"]
                else f"https://{self.url.host}{a_tag['href']}"
            )
            self.company_info.company_website = Url(url)

        ul_location = header.find("ul", class_="details inline pt20")

        if ul_location is None:
            return False
        location_item = ul_location.find("li", class_="block")

        if location_item:
            self.company_info.company_location = location_item.text.strip().split(
                "\xa0"
            )[0]
        return True


if __name__ == "__main__":
    from scrapper.factory import FactoryScrapper

    url = "https://www.infoempleo.com/ofertasdetrabajo/programadora-backend/almeria/3097402/"

    scrapper: InfoEmpleoScrapper = FactoryScrapper.get_scrapper(Url(url))
    scrapper.extract()

    scrapper.console.print(scrapper.get_extraction_result())
