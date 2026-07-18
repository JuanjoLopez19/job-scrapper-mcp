import pytest
from bs4 import BeautifulSoup
from pydantic_core import Url

from job_offer_scraper_mcp.scrapper.implementations.indeed import IndeedScrapper
from job_offer_scraper_mcp.scrapper.implementations.info_empleo import (
    InfoEmpleoScrapper,
)
from job_offer_scraper_mcp.scrapper.implementations.linkedin import LinkedinScrapper
from job_offer_scraper_mcp.scrapper.implementations.tecnoempleo import (
    TecnoEmpleoScrapper,
)


@pytest.mark.parametrize(
    ("scraper", "html", "expected"),
    [
        (
            LinkedinScrapper(Url("https://linkedin.com/jobs/view/1")),
            '<div class="show-more-less-html__markup"> Python backend </div>',
            "Python backend",
        ),
        (
            InfoEmpleoScrapper(Url("https://infoempleo.com/job/1")),
            '<div class="offer"> Data engineer </div>',
            "Data engineer",
        ),
        (
            IndeedScrapper(Url("https://indeed.com/viewjob?jk=1")),
            '<div class="jobsearch-JobComponent-description">'
            '<div id="jobDescriptionText"> Platform engineer </div></div>',
            "Platform engineer",
        ),
    ],
)
def test_find_job_description_extracts_normalized_text(
    scraper, html: str, expected: str
) -> None:
    soup = BeautifulSoup(html, "html.parser")

    assert scraper.find_job_description(soup) == expected


def test_linkedin_find_job_criteria_maps_known_labels() -> None:
    scraper = LinkedinScrapper(Url("https://linkedin.com/jobs/view/1"))
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


def test_tecnoempleo_find_job_description_reads_json_ld() -> None:
    scraper = TecnoEmpleoScrapper(Url("https://tecnoempleo.com/job/1"))
    soup = BeautifulSoup(
        '<script type="application/ld+json">'
        '{"description": "Senior Python developer"}'
        "</script>",
        "html.parser",
    )

    assert scraper.find_job_description(soup) == "Senior Python developer"


@pytest.mark.parametrize(
    "scraper",
    [
        LinkedinScrapper(Url("https://linkedin.com/jobs/view/1")),
        InfoEmpleoScrapper(Url("https://infoempleo.com/job/1")),
        TecnoEmpleoScrapper(Url("https://tecnoempleo.com/job/1")),
    ],
)
def test_find_job_description_without_expected_markup_returns_none(scraper) -> None:
    assert scraper.find_job_description(BeautifulSoup("", "html.parser")) is None
