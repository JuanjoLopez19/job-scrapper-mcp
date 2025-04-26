import logging
from typing import Dict, Optional, Type

from pydantic_core import Url

from scrapper.base import JobOfferExtractor
from shared.constants import ScrapperSelectionError

# Configurar logger
logger = logging.getLogger(__name__)


class FactoryScrapper:
    """
    A factory class for creating web scrapper instances based on job website URLs.

    This class provides a factory method to instantiate the appropriate scrapper
    based on the domain of the provided URL. It follows the Factory design pattern
    to create instances of different scrapper classes based on the website URL.

    Attributes:
        _scrapper_registry (Dict[str, Type[JobOfferExtractor]]): Registry of supported scrapers
            mapping domain keywords to scraper classes.
    """

    # Registro de scrapers disponibles (inicializado en _init_registry)
    _scrapper_registry: Dict[str, Type[JobOfferExtractor]] = {}

    @classmethod
    def _init_registry(cls) -> None:
        """
        Initialize the registry of supported scrapers.

        This method is called internally to lazily load scraper classes
        to avoid circular imports.
        """
        # Solo inicializar si el registro está vacío
        if not cls._scrapper_registry:
            from scrapper.indeed import IndeedScrapper
            from scrapper.info_empleo import InfoEmpleoScrapper
            from scrapper.linkedin import LinkedinScrapper
            from scrapper.tecnoempleo import TecnoEmpleoScrapper

            cls._scrapper_registry = {
                "linkedin": LinkedinScrapper,
                "infoempleo": InfoEmpleoScrapper,
                "tecnoempleo": TecnoEmpleoScrapper,
                "indeed": IndeedScrapper,
            }
            logger.info(
                f"Scrapper registry initialized with {len(cls._scrapper_registry)} scrapers"
            )

    @classmethod
    def register_scrapper(
        cls, domain_key: str, scrapper_class: Type[JobOfferExtractor]
    ) -> None:
        """
        Register a new scrapper class for a specific domain.

        Args:
            domain_key (str): The domain keyword to match in URLs.
            scrapper_class (Type[JobOfferExtractor]): The scrapper class to instantiate.
        """
        cls._init_registry()
        cls._scrapper_registry[domain_key] = scrapper_class
        logger.info(f"Registered new scrapper for domain '{domain_key}'")

    @classmethod
    def get_supported_domains(cls) -> list[str]:
        """
        Get a list of supported domain keywords.

        Returns:
            list[str]: List of domain keywords that can be handled.
        """
        cls._init_registry()
        return list(cls._scrapper_registry.keys())

    @classmethod
    def get_scrapper(cls, url: Url) -> JobOfferExtractor:
        """
        Creates and returns a scrapper instance appropriate for the given URL.

        Args:
            url (Url): The URL of the job posting to scrape.

        Returns:
            JobOfferExtractor: An instance of a scrapper appropriate for the URL.

        Raises:
            ValueError: If the URL is invalid or no domain is found.
            ScrapperSelectionError: If no suitable scrapper is found for the domain.
        """
        cls._init_registry()

        domain = url.host
        if not domain:
            logger.error("Invalid URL: No domain found")
            raise ValueError("Invalid URL: No domain found.")

        logger.info(f"Finding scrapper for domain: {domain}")

        # Buscar un scrapper adecuado en el registro
        matching_key: Optional[str] = None
        for key in cls._scrapper_registry:
            if key in domain:
                matching_key = key
                break

        if matching_key:
            scrapper_class = cls._scrapper_registry[matching_key]
            logger.info(
                f"Found matching scrapper '{scrapper_class.__name__}' for domain '{domain}'"
            )
            try:
                return scrapper_class(url)
            except Exception as e:
                logger.error(f"Error instantiating scrapper for {domain}: {e}")
                raise

        logger.error(f"Unsupported domain: {domain}")
        raise ScrapperSelectionError(f"Unsupported domain: {domain}")
