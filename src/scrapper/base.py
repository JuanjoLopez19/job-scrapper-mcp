import logging
import os
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, Optional

from bs4 import BeautifulSoup as bs
from pydantic_core import Url
from requests import Session, exceptions

from shared.constants import USER_AGENTS, JobOfferCriteria

# Configurar logger
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class JobOfferExtractor(ABC):
    """
    Abstract base class for extracting job offer information from various websites.

    This class provides common functionality for web scraping job offers, including
    HTML extraction using both requests and Selenium as a fallback. It defines the
    framework that concrete implementations should follow.

    Attributes:
        url (Url): The URL of the job offer to extract information from.
        headers (Dict[str, str]): HTTP headers to use when making requests.
        html (Optional[bs]): The parsed HTML content of the page once extracted.
        description (Optional[str]): The extracted job description.
        criteria (Optional[str]): The extracted job criteria.
    """

    url: Url

    offer_description: Optional[str] = None
    offer_criteria: Optional[JobOfferCriteria] = field(default_factory=JobOfferCriteria)
    company_name: Optional[str] = None
    offer_title: Optional[str] = None
    company_url: Optional[Url] = None
    html: Optional[bs] = None

    # Class variables
    MAX_RETRIES: ClassVar[int] = 3
    RETRY_DELAY: ClassVar[int] = 2

    # Instance variables with defaults
    session: Session = field(default_factory=Session)
    headers: Dict[str, str] = field(
        default_factory=lambda: {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
    )

    def _extract_html(self) -> Optional[bs]:
        """
        Extracts HTML content from the URL using requests with retry mechanism.
        Falls back to Selenium if requests fails.

        Returns:
            Optional[bs]: BeautifulSoup object of the parsed HTML or None if extraction fails.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(
                    f"Attempting to fetch URL: {self.url} (Attempt {attempt + 1}/{self.MAX_RETRIES})"
                )
                response = self.session.get(self.url, headers=self.headers, timeout=10)
                response.raise_for_status()
                logger.info(f"Successfully fetched URL: {self.url}")
                return bs(response.text, "html.parser")
            except exceptions.RequestException as e:
                logger.warning(f"Error fetching URL on attempt {attempt + 1}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    logger.info(f"Retrying in {self.RETRY_DELAY} seconds...")
                    time.sleep(self.RETRY_DELAY)
                else:
                    logger.warning(
                        "All retry attempts failed, falling back to Selenium"
                    )
                    return self._extract_html_selenium()
        return None

    def _extract_html_selenium(self) -> Optional[bs]:
        """
        Extracts HTML content using Selenium WebDriver when requests fails.

        Returns:
            Optional[bs]: BeautifulSoup object of the parsed HTML or None if extraction fails.
        """
        from seleniumbase import Driver

        logger.info(f"Attempting to fetch URL with Selenium: {self.url}")
        driver = Driver(
            uc=True,
            headless=os.getenv("IS_MCP", False) == "True",
            chromium_arg=["--auto-open-devtools-for-tabs"],
        )
        try:
            driver.maximize_window()
            driver.get(str(self.url))
            driver.sleep(6)

            html = bs(driver.page_source, "html.parser")
            logger.info(f"Successfully fetched URL with Selenium: {self.url}")
            return html
        except Exception as e:
            logger.error(f"Error with Selenium: {e}")
            return None
        finally:
            driver.quit()

    def extract(self) -> bool:
        """
        Main method to extract job offer information.
        Handles the complete extraction workflow from HTML fetching to information parsing.

        Returns:
            bool: True if extraction was successful, False otherwise.
        """
        self.html = self._extract_html()
        if self.html is None:
            logger.error("Failed to extract HTML content")
            return False

        # self.company_info = self.get_company_info(self.html)

        job_offer_info = self.find_job_offer_info(self.html)
        if job_offer_info is None:
            logger.error("Failed to find job offer information")
            return False

        # job_description = self.find_job_description(job_offer_info)
        # self.description = job_description if job_description else None

        self.find_job_criteria(job_offer_info, **{"source": self.html})

        return True

    def get_job_description(self) -> Optional[str]:
        """Returns the extracted job description if available."""
        return self.offer_description

    def get_job_criteria(self) -> Optional[str]:
        """Returns the extracted job criteria if available."""
        return self.offer_criteria

    def get_extraction_result(self) -> Dict[str, Any]:
        """
        Returns a dictionary with all extracted information.

        Returns:
            Dict[str, Any]: Dictionary containing the extracted information.
        """
        return {"description": self.offer_description, "criteria": self.offer_criteria}

    @abstractmethod
    def find_job_offer_info(self, html: bs) -> Optional[bs]:
        """
        Extracts the job offer information section from the HTML.

        Args:
            html (bs): The parsed HTML of the page.

        Returns:
            Optional[bs]: The job offer information section or None if not found.
        """
        pass

    @abstractmethod
    def find_job_description(self, job_offer: bs) -> Optional[str]:
        """
        Extracts the job description from the job offer information.

        Args:
            job_offer (bs): The job offer information section.

        Returns:
            Optional[str]: The job description or None if not found.
        """
        pass

    @abstractmethod
    def find_job_criteria(self, job_offer: bs, **kwargs: bs) -> Optional[str]:
        """
        Extracts the job criteria from the job offer information.

        Args:
            job_offer (bs): The job offer information section.

        Returns:
            Optional[str]: The job criteria or None if not found.
        """
        pass

    # @abstractmethod
    # def get_company_info(self, html: bs) -> Optional[CompanyInfo]:
    #     """
    #     Returns the company information if available.

    #     Returns:
    #         Optional[CompanyInfo]: The company information or None if not available.
    #     """
    #     pass
