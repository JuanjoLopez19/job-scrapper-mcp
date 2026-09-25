import json

import pytest
from bs4 import BeautifulSoup
from pydantic_core import Url

from job_offer_scraper_mcp.scrapper.implementations.indeed import IndeedScrapper


@pytest.fixture
def scraper() -> IndeedScrapper:
    return IndeedScrapper(Url("https://indeed.com/viewjob?jk=1"))


def soup_with_structured_data(**data: object) -> BeautifulSoup:
    payload = json.dumps({"@type": "JobPosting", **data})
    return BeautifulSoup(
        f'<script type="application/ld+json">{payload}</script>', "html.parser"
    )


def test_find_job_description_reads_structured_data(scraper: IndeedScrapper) -> None:
    soup = soup_with_structured_data(
        description="<p>Platform engineer</p><ul><li>Python</li><li>APIs</li></ul>"
    )

    assert scraper.find_job_description(soup) == "Platform engineer\nPython\nAPIs"


def test_page_without_job_posting_requires_browser_fallback(
    scraper: IndeedScrapper,
) -> None:
    soup = BeautifulSoup(
        "<html><p>Additional verification required</p></html>", "html.parser"
    )

    assert scraper.is_browser_fallback_required(soup) is True


def test_page_with_job_posting_does_not_require_browser_fallback(
    scraper: IndeedScrapper,
) -> None:
    assert scraper.is_browser_fallback_required(soup_with_structured_data()) is False
    assert scraper.get_browser_ready_selector() == 'script[type="application/ld+json"]'


def test_find_job_metadata_reads_structured_data(scraper: IndeedScrapper) -> None:
    soup = soup_with_structured_data(
        title="Platform Engineer",
        hiringOrganization={"name": "Acme"},
        jobLocation={"address": {"addressLocality": "Madrid"}},
    )

    assert scraper.find_job_title(soup) == "Platform Engineer"
    assert scraper.find_job_company(soup) == "Acme"
    assert scraper.find_job_location(soup) == "Madrid"


def test_find_job_criteria_formats_structured_data(scraper: IndeedScrapper) -> None:
    soup = soup_with_structured_data(
        employmentType=["FULL_TIME"],
        baseSalary={"value": {"minValue": 40000, "maxValue": 50000}},
        jobLocationType="TELECOMMUTE",
        applicantLocationRequirements=[{"name": "Spain"}],
    )

    assert scraper.find_job_criteria(soup) == (
        "Employment type: Full-time\n"
        "Base salary:40000-50000\n"
        "Job location type: TELECOMMUTE\n"
        'Applicant location requirements: [{"name": "Spain"}]'
    )


def test_find_job_criteria_handles_missing_salary_bounds(
    scraper: IndeedScrapper,
) -> None:
    soup = soup_with_structured_data(
        employmentType=["UNKNOWN_TYPE"],
        baseSalary={"value": {"minValue": 40000}},
    )

    assert scraper.find_job_criteria(soup) == (
        "Employment type: Unknown\nBase salary:40000-Not specified"
    )


def test_find_job_data_without_json_returns_none(scraper: IndeedScrapper) -> None:
    soup = BeautifulSoup("<html></html>", "html.parser")

    assert scraper.find_job_description(soup) is None
    assert scraper.find_job_criteria(soup) is None
    assert scraper.find_job_title(soup) is None
    assert scraper.find_job_company(soup) is None
    assert scraper.find_job_location(soup) is None


def test_invalid_or_unrelated_json_ld_is_ignored(scraper: IndeedScrapper) -> None:
    soup = BeautifulSoup(
        """
        <script type="application/ld+json">not-json</script>
        <script type="application/ld+json">{"@type": "WebSite"}</script>
        """,
        "html.parser",
    )

    assert scraper.find_job_title(soup) is None
    assert scraper.is_browser_fallback_required(soup) is True
