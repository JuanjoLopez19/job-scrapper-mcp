from pydantic_core import Url

from src.shared.constants import ScrapperSelectionError


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
    def get_scrapper(url: Url):
        domain = url.host

        if not domain:
            raise ValueError("Invalid URL: No domain found.")

        if "linkedin" in domain:
            from src.scrapper.linkedin import LinkedinScrapper

            return LinkedinScrapper(url)
        elif "infoempleo" in domain:
            from src.scrapper.info_empleo import InfoEmpleoScrapper

            return InfoEmpleoScrapper(url)
        elif "tecnoempleo" in domain:
            from src.scrapper.tecnoempleo import TecnoEmpleoScrapper

            return TecnoEmpleoScrapper(url)
        elif "indeed" in domain:
            from src.scrapper.indeed import IndeedScrapper

            return IndeedScrapper(url)
        else:
            raise ScrapperSelectionError(f"Unsupported domain: {domain}")
