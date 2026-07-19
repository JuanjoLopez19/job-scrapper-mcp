from pydantic_core import Url

from job_offer_scraper_mcp.scrapper.base import JobOfferExtractor
from job_offer_scraper_mcp.scrapper.config import SITE_DOMAINS, SupportedSites
from job_offer_scraper_mcp.shared.constants import ScrapperSelectionError


class FactoryScrapper:
    """
    A factory class for creating web scrapper instances based on job website URLs.
    This class provides a factory method to instantiate the appropriate scrapper
    based on the domain of the provided URL. Currently supports LinkedIn, InfoEmpleo,
    and TecnoEmpleo job websites.
    Methods
    -------
    get_scrapper(url: str)
        Creates and returns a scrapper instance appropriate for the given URL.
        Parameters
        ----------
        url : str
            The URL of the job posting to scrape.
        Returns
        -------
        Scrapper
            An instance of a scrapper appropriate for the given URL.
        Raises
        ------
        ValueError
            If the URL is invalid or no domain is found.
        ImportError
            If the module for the required scrapper cannot be imported.
    """

    @staticmethod
    def get_scrapper(url: Url) -> JobOfferExtractor:
        domain = url.host

        if not domain:
            raise ValueError("Invalid URL: No domain found.")

        if FactoryScrapper._matches_site(domain, SupportedSites.LINKEDIN):
            from job_offer_scraper_mcp.scrapper.implementations.linkedin import (
                LinkedinScrapper,
            )

            return LinkedinScrapper(url)
        elif FactoryScrapper._matches_site(domain, SupportedSites.INFO_EMPLEO):
            from job_offer_scraper_mcp.scrapper.implementations.info_empleo import (
                InfoEmpleoScrapper,
            )

            return InfoEmpleoScrapper(url)
        elif FactoryScrapper._matches_site(domain, SupportedSites.TECNO_EMPLEO):
            from job_offer_scraper_mcp.scrapper.implementations.tecnoempleo import (
                TecnoEmpleoScrapper,
            )

            return TecnoEmpleoScrapper(url)
        elif FactoryScrapper._matches_site(domain, SupportedSites.INDEED):
            from job_offer_scraper_mcp.scrapper.implementations.indeed import (
                IndeedScrapper,
            )

            return IndeedScrapper(url)
        else:
            raise ScrapperSelectionError(f"Unsupported domain: {domain}")

    @staticmethod
    def _matches_site(domain: str, site: SupportedSites) -> bool:
        normalized_domain = domain.rstrip(".").lower()
        return any(
            normalized_domain == allowed_domain
            or normalized_domain.endswith(f".{allowed_domain}")
            for allowed_domain in SITE_DOMAINS[site]
        )
