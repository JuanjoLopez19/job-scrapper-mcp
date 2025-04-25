import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

from bs4 import BeautifulSoup as bs
from requests import Session, exceptions

from shared.constants import USER_AGENTS


@dataclass(slots=True)
class JobOfferExtractor(ABC):
    url: str
    session = Session()
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    html: bs | None = None

    def __extract_html(self):
        try:
            response = self.session.get(self.url, headers=self.headers)
            response.raise_for_status()
            return bs(response.text, "html.parser")
        except exceptions.RequestException as e:
            print(f"Error fetching the URL: {e}")
            return None

    def extract(self):
        self.html = self.__extract_html()
        if self.html is None:
            return None

        job_offer_info = self.find_job_offer_info(self.html)
        if job_offer_info is None:
            return None
        job_description = self.find_job_description(job_offer_info)
        self.description = job_description if job_description else None

        job_criteria = self.find_job_criteria(job_offer_info)
        self.criteria = job_criteria if job_criteria else None

    def get_job_description(self) -> str | None:
        return self.description

    def get_job_criteria(self) -> str | None:
        return self.criteria

    @abstractmethod
    def find_job_offer_info(self, html) -> bs | None:
        pass

    @abstractmethod
    def find_job_description(self, html) -> str | None:
        pass

    @abstractmethod
    def find_job_criteria(self, html) -> str | None:
        pass
