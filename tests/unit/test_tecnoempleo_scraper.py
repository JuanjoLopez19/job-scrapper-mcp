from bs4 import BeautifulSoup
from pydantic_core import Url

from job_offer_scraper_mcp.scrapper.implementations.tecnoempleo import (
    TecnoEmpleoScrapper,
)


def test_find_job_description_reads_json_ld() -> None:
    scraper = TecnoEmpleoScrapper(Url("https://tecnoempleo.com/job/1"))
    soup = BeautifulSoup(
        '<script type="application/ld+json">'
        '{"description": "Senior Python developer"}'
        "</script>",
        "html.parser",
    )

    assert scraper.find_job_description(soup) == "Senior Python developer"


def test_find_job_description_without_expected_markup_returns_none() -> None:
    scraper = TecnoEmpleoScrapper(Url("https://tecnoempleo.com/job/1"))

    assert scraper.find_job_description(BeautifulSoup("", "html.parser")) is None
