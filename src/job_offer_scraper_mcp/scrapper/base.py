import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Protocol, cast

from bs4 import BeautifulSoup as bs
from pydantic_core import Url
from requests import Session, exceptions

from job_offer_scraper_mcp.shared.constants import USER_AGENTS, JobOfferInfo
from job_offer_scraper_mcp.shared.url_validation import validate_public_http_url
from job_offer_scraper_mcp.shared.utils import fetch_url_response

logger = logging.getLogger(__name__)


class SeleniumDriver(Protocol):
    page_source: str

    def get(self, url: str) -> None: ...

    def sleep(self, seconds: int) -> None: ...

    def quit(self) -> None: ...


def _default_headers() -> dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }


@dataclass(slots=True)
class JobOfferExtractor(ABC):
    url: Url
    session: Session = field(default_factory=Session, repr=False)
    headers: dict[str, str] = field(default_factory=_default_headers)
    html: bs | None = field(default=None, init=False)
    description: str | None = field(default=None, init=False)
    criteria: str | None = field(default=None, init=False)
    title: str | None = field(default=None, init=False)
    company: str | None = field(default=None, init=False)
    location: str | None = field(default=None, init=False)

    def __extract_html(self) -> bs | None:
        try:
            response = fetch_url_response(
                self.session,
                self.url,
                headers=self.headers,
            )
            return bs(response.text, "html.parser")
        except exceptions.RequestException:
            logger.warning("HTTP extraction failed; trying browser fallback")
            return self.__extract_html_selenium()

    def extract(self) -> None:
        self.html = self.__extract_html()
        if self.html is None:
            return

        self.title = self.find_job_title(self.html)
        self.company = self.find_job_company(self.html)
        self.location = self.find_job_location(self.html)

        job_offer_info = self.find_job_offer_info(self.html)
        if job_offer_info is None:
            return

        job_description = self.find_job_description(job_offer_info)
        self.description = job_description if job_description else None

        job_criteria = self.find_job_criteria(job_offer_info)
        self.criteria = job_criteria if job_criteria else None

    def __extract_html_selenium(self) -> bs | None:
        from seleniumbase import Driver

        driver: SeleniumDriver | None = None
        try:
            validate_public_http_url(str(self.url))
            driver = cast(
                SeleniumDriver,
                cast(Any, Driver)(uc=True, headless=True, disable_gpu=True),
            )
            driver.get(str(self.url))
            driver.sleep(5)
            return bs(driver.page_source, "html.parser")
        except Exception:
            logger.exception("Browser extraction failed")
            return None
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    logger.exception("Unable to close browser driver")

    def get_job_description(self) -> str | None:
        return self.description

    def get_job_criteria(self) -> str | None:
        return self.criteria

    def get_job_title(self) -> str | None:
        return self.title

    def get_job_company(self) -> str | None:
        return self.company

    def get_job_location(self) -> str | None:
        return self.location

    def get_job_offer_info(self) -> JobOfferInfo:
        return JobOfferInfo(
            url=self.url,
            title=self.get_job_title(),
            company_name=self.get_job_company(),
            location=self.get_job_location(),
            description=self.get_job_description(),
            criteria=self.get_job_criteria(),
        )

    @abstractmethod
    def find_job_offer_info(self, html: Any) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    def find_job_description(self, html: Any) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def find_job_criteria(self, html: Any) -> str | None:
        raise NotImplementedError

    def find_job_title(self, html: Any) -> str | None:
        return None

    def find_job_company(self, html: Any) -> str | None:
        return None

    def find_job_location(self, html: Any) -> str | None:
        return None
