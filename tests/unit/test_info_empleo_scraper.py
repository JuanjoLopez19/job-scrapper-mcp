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


def test_find_job_company_extracts_anchor_without_badge() -> None:
    scraper = InfoEmpleoScrapper(Url("https://infoempleo.com/job/1"))
    soup = BeautifulSoup(
        """
        <ul class="details companyjobtype">
            <li class="companyname">
                <a href="/empresa/acme">Acme Technologies</a>
                <span class="badge">Oferta destacada</span>
            </li>
        </ul>
        """,
        "html.parser",
    )

    assert scraper.find_job_company(soup) == "Acme Technologies"


def test_find_job_company_without_company_list_returns_none() -> None:
    scraper = InfoEmpleoScrapper(Url("https://infoempleo.com/job/1"))

    assert scraper.find_job_company(BeautifulSoup("", "html.parser")) is None


def test_find_job_company_without_company_link_returns_none() -> None:
    scraper = InfoEmpleoScrapper(Url("https://infoempleo.com/job/1"))
    soup = BeautifulSoup(
        '<ul class="details companyjobtype"><li class="companyname">Acme</li></ul>',
        "html.parser",
    )

    assert scraper.find_job_company(soup) is None


def test_find_job_title_extracts_title_from_page_title() -> None:
    scraper = InfoEmpleoScrapper(Url("https://infoempleo.com/job/1"))
    soup = BeautifulSoup(
        "<title>Desarrollador JAVA en Madrid | Infoempleo</title>",
        "html.parser",
    )

    assert scraper.find_job_title(soup) == "Desarrollador JAVA"


def test_find_job_location_extracts_location_without_source_suffix() -> None:
    scraper = InfoEmpleoScrapper(Url("https://infoempleo.com/job/1"))
    soup = BeautifulSoup(
        "<title>Desarrollador JAVA en Madrid | Infoempleo</title>",
        "html.parser",
    )

    assert scraper.find_job_location(soup) == "Madrid"


def test_find_job_title_and_location_without_source_suffix() -> None:
    scraper = InfoEmpleoScrapper(Url("https://infoempleo.com/job/1"))
    soup = BeautifulSoup(
        "<title>Ingeniero Backend en Almería</title>",
        "html.parser",
    )

    assert scraper.find_job_title(soup) == "Ingeniero Backend"
    assert scraper.find_job_location(soup) == "Almería"
