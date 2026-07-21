from bs4 import BeautifulSoup
from pydantic_core import Url

from job_offer_scraper_mcp.scrapper.implementations.indeed import IndeedScrapper


def test_find_job_description_extracts_normalized_text() -> None:
    scraper = IndeedScrapper(Url("https://indeed.com/viewjob?jk=1"))
    soup = BeautifulSoup(
        '<div class="jobsearch-JobComponent-description">'
        '<div id="jobDescriptionText"> Platform engineer </div></div>',
        "html.parser",
    )

    assert scraper.find_job_description(soup) == "Platform engineer"
