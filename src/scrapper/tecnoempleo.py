import json
from dataclasses import dataclass

from bs4 import BeautifulSoup as bs
from pydantic_core import Url

from scrapper.base import JobOfferExtractor


@dataclass(slots=True)
class TecnoEmpleoScrapper(JobOfferExtractor):
    type: str = "tecnoempleo"
    description: str | None = None
    criteria: str | None = None

    def find_job_offer_info(self, html: bs):
        return html

    def find_job_description(self, job_offer: bs):
        script = job_offer.find("script", type="application/ld+json")
        if script is None:
            return None

        data = json.loads(script.string)
        if data is None:
            return None
        return data.get("description", "No description available")

    def find_job_criteria(self, job_offer: bs, **kwargs: bs):
        criteria_list = []
        level = (
            job_offer.find("div", {"itemprop": "description"})
            .next_sibling.next_sibling.find("i", {"class": "fi fi-shield-ok"})
            .parent.next_sibling.next_sibling.text.strip()
            .replace("\t", "")
            .split("\n")[1]
        )

        list_items = (
            job_offer.select_one("div[class='mt-0']").find_next("ul").find_all("li")
        )

        function = list_items[2].find_next("span").text.strip()
        offer_type = list_items[3].find_next("span").text.strip()

        criteria_list.append(f"type: {offer_type}")
        criteria_list.append(f"function: {function}")
        criteria_list.append(f"level: {level}")
        criteria_list.append(f"industry: {None}")

        return "\n".join(criteria_list)


if __name__ == "__main__":
    from scrapper.factory import FactoryScrapper

    url = "https://www.tecnoempleo.com/engineering-operations-technician-amazon-web-servi/aws/rf-0de4198da26b53cec144"

    scrapper: TecnoEmpleoScrapper = FactoryScrapper.get_scrapper(Url(url))
    scrapper.extract()
    print(scrapper.get_job_description())
    print(scrapper.get_job_criteria())
