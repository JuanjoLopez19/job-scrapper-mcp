import pytest
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


def test_find_job_description_uses_default_when_description_is_missing() -> None:
    scraper = TecnoEmpleoScrapper(Url("https://tecnoempleo.com/job/1"))
    soup = BeautifulSoup(
        '<script type="application/ld+json">{"name": "Job"}</script>',
        "html.parser",
    )

    assert scraper.find_job_description(soup) == "No description available"


def test_find_job_criteria_extracts_offer_metadata() -> None:
    scraper = TecnoEmpleoScrapper(Url("https://tecnoempleo.com/job/1"))
    soup = BeautifulSoup(
        """
        <div itemprop="description"></div>
        <div></div>
        <div><i class="fi fi-shield-ok"></i></div>
        <div></div>
        <div>
            Senior
        </div>
        <div class="mt-0">
            <ul>
                <li><i class="fi fi-pin"></i><span class="float-end">Madrid</span></li>
                <li><i class="fi fi-shield-ok"></i><span class="float-end">Senior</span></li>
                <li><i class="fi fi-calendar"></i><span class="float-end">Full-time</span></li>
                <li><i class="fi fi-users"></i><span class="float-end">Backend</span></li>
                <li><i class="fi fi-task-list"></i><span class="float-end">Permanent</span></li>
                <li><i class="fi fi-plus"></i><span class="float-end">40k</span></li>
            </ul>
        </div>
        """,
        "html.parser",
    )

    assert scraper.find_job_criteria(soup) == (
        "location: Madrid\nexperience: Senior\nworking_time: Full-time\n"
        "function: Backend\ncontract_type: Permanent\nsalary: 40k"
    )


@pytest.mark.parametrize(
    "html",
    [
        "",
        '<div itemprop="description"></div>',
        '<div class="mt-0"></div>',
    ],
)
def test_find_job_criteria_without_expected_markup_returns_none(html: str) -> None:
    scraper = TecnoEmpleoScrapper(Url("https://tecnoempleo.com/job/1"))

    assert scraper.find_job_criteria(BeautifulSoup(html, "html.parser")) is None


def test_metadata_methods_extract_title_location_and_company() -> None:
    scraper = TecnoEmpleoScrapper(Url("https://tecnoempleo.com/job/1"))
    soup = BeautifulSoup(
        """
        <title>Oferta de Empleo backend developer en remoto, Example Corp</title>
        <ul class="details companyjobtype">
            <li class="companyname"><a>Example Corp</a></li>
        </ul>
        """,
        "html.parser",
    )

    assert scraper.find_job_title(soup) == "backend developer"
    assert scraper.find_job_location(soup) == "remoto"
    assert scraper.find_job_company(soup) == "Example Corp"


def test_metadata_methods_without_expected_markup_return_none() -> None:
    scraper = TecnoEmpleoScrapper(Url("https://tecnoempleo.com/job/1"))

    assert scraper.find_job_title(BeautifulSoup("", "html.parser")) is None
    assert scraper.find_job_location(BeautifulSoup("", "html.parser")) is None
    assert scraper.find_job_company(BeautifulSoup("", "html.parser")) is None


@pytest.mark.parametrize(
    ("page_title", "expected"),
    [
        (
            "Oferta de Empleo desarrollador/a python/django + vue.js en remoto, "
            "CAS TRAINING",
            {
                "title": "desarrollador/a python/django + vue.js",
                "location": "remoto",
                "company": "CAS TRAINING",
            },
        ),
        (
            "Oferta de Empleo desarrollador c++ / pro*c en Málaga, "
            "Serem - Tecnoempleo.com",
            {
                "title": "desarrollador c++ / pro*c",
                "location": "Málaga",
                "company": "Serem",
            },
        ),
        (
            "Oferta de Empleo desarrollador backend con java en Madrid, Michael Page",
            {
                "title": "desarrollador backend con java",
                "location": "Madrid",
                "company": "Michael Page",
            },
        ),
    ],
)
def test_title_pattern_extracts_job_metadata(
    page_title: str, expected: dict[str, str]
) -> None:
    match = TecnoEmpleoScrapper.job_offer_title_pattern.fullmatch(page_title)

    assert match is not None
    assert match.groupdict() == expected


def test_title_pattern_rejects_unrelated_title() -> None:
    match = TecnoEmpleoScrapper.job_offer_title_pattern.fullmatch("Oferta no válida")

    assert match is None
