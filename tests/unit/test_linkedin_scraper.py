import pytest
from bs4 import BeautifulSoup
from pydantic_core import Url

from job_offer_scraper_mcp.scrapper.implementations.linkedin import LinkedinScrapper


@pytest.fixture
def scraper() -> LinkedinScrapper:
    return LinkedinScrapper(Url("https://linkedin.com/jobs/view/1"))


def test_find_job_description_extracts_normalized_text(
    scraper: LinkedinScrapper,
) -> None:
    soup = BeautifulSoup(
        '<div class="show-more-less-html__markup"> Python backend </div>',
        "html.parser",
    )

    assert scraper.find_job_description(soup) == "Python backend"


def test_find_job_description_without_expected_markup_returns_none(
    scraper: LinkedinScrapper,
) -> None:
    assert scraper.find_job_description(BeautifulSoup("", "html.parser")) is None


def test_find_job_criteria_maps_known_labels(scraper: LinkedinScrapper) -> None:
    soup = BeautifulSoup(
        """
        <ul class="description__job-criteria-list">
          <li><h3>Employment type</h3><span>Full-time</span></li>
          <li><h3>Job function</h3><span>Engineering</span></li>
        </ul>
        """,
        "html.parser",
    )

    assert scraper.find_job_criteria(soup) == ("type: Full-time\nfunction: Engineering")


@pytest.mark.parametrize(
    ("page_title", "expected_company", "expected_title", "expected_location"),
    [
        (
            "WongDoody hiring Senior AI Engineer in Stuttgart Region | LinkedIn",
            "WongDoody",
            "Senior AI Engineer",
            "Stuttgart Region",
        ),
        (
            "exmox GmbH hiring Senior Backend Engineer (f/m/x) in Hamburg, "
            "Hamburg, Germany | LinkedIn",
            "exmox GmbH",
            "Senior Backend Engineer (f/m/x)",
            "Hamburg, Hamburg, Germany",
        ),
        (
            "Whitebox AI hiring Senior AI developer in Denmark | LinkedIn",
            "Whitebox AI",
            "Senior AI developer",
            "Denmark",
        ),
    ],
)
def test_extracts_metadata_from_page_title(
    scraper: LinkedinScrapper,
    page_title: str,
    expected_company: str,
    expected_title: str,
    expected_location: str,
) -> None:
    soup = BeautifulSoup(f"<title>{page_title}</title>", "html.parser")

    assert scraper.find_job_company(soup) == expected_company
    assert scraper.find_job_title(soup) == expected_title
    assert scraper.find_job_location(soup) == expected_location


@pytest.mark.parametrize(
    "html",
    [
        "",
        "<title>Unsupported LinkedIn title</title>",
    ],
)
def test_metadata_without_supported_page_title_returns_none(
    scraper: LinkedinScrapper, html: str
) -> None:
    soup = BeautifulSoup(html, "html.parser")

    assert scraper.find_job_company(soup) is None
    assert scraper.find_job_title(soup) is None
    assert scraper.find_job_location(soup) is None
