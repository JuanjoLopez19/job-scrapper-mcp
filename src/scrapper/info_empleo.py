from dataclasses import dataclass

from bs4 import BeautifulSoup as bs

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
            return None
        return description.text.strip()

    def find_job_criteria(self, job_offer: bs):
        criteria = job_offer.find("div", {"class": "offer-excerpt"})
        if criteria is None:
            return None
        ul = criteria.find_all("ul", {"class": "inline"})
        if not ul:
            return None
        criteria_list = []
        row_1 = ul[1]
        row_2 = ul[3]

        type: str = row_2.find_all("li").pop().find("p").text.strip()

        function: str = row_1.find("ul", {"class": "position-name"}).text.strip()

        level: str = row_1.find_all("li").pop().find("p").text.strip()
        industry: str = (
            row_1.select("div[class='multipos-visible-content'] p:nth-child(1)")
            .pop()
            .find("strong")
            .text.strip()
        )

        criteria_list.append(f"type: {type}")
        criteria_list.append(f"function: {function}")
        criteria_list.append(f"level: {level}")
        criteria_list.append(f"industry: {industry}")

        return "\n".join(criteria_list)


if __name__ == "__main__":
    from scrapper.factory import FactoryScrapper

    url = ""

    scrapper: InfoEmpleoScrapper = FactoryScrapper.get_scrapper(url)
    scrapper.extract()
    print(scrapper.get_job_description())
    print(scrapper.get_job_criteria())
