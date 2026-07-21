from bs4 import BeautifulSoup
from pydantic_core import Url

from job_offer_scraper_mcp.scrapper.implementations.info_empleo import (
    InfoEmpleoScrapper,
)


def test_find_job_description_extracts_normalized_text() -> None:
    scraper = InfoEmpleoScrapper(Url("https://infoempleo.com/job/1"))
    soup = BeautifulSoup('<div class="offer"> Data engineer </div>', "html.parser")

    assert scraper.find_job_description(soup) == "Data engineer"


def test_find_job_description_without_expected_markup_returns_none() -> None:
    scraper = InfoEmpleoScrapper(Url("https://infoempleo.com/job/1"))

    assert scraper.find_job_description(BeautifulSoup("", "html.parser")) is None
