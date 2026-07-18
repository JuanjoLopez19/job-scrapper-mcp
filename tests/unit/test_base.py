from unittest.mock import Mock, patch

from bs4 import BeautifulSoup
from pydantic_core import Url
from requests import exceptions

from job_offer_scraper_mcp.scrapper.implementations.linkedin import LinkedinScrapper


def test_extract_from_http_response_populates_description_and_criteria(
    monkeypatch,
) -> None:
    response = Mock()
    response.status_code = 200
    response.text = """
        <section class="core-section-container">
          <div class="show-more-less-html__markup"> Build APIs </div>
          <ul class="description__job-criteria-list">
            <li><h3>Seniority level</h3><span>Mid-Senior</span></li>
          </ul>
        </section>
    """
    session = Mock()
    session.get.return_value = response
    monkeypatch.setattr(
        "job_offer_scraper_mcp.shared.utils.validate_public_http_url", Mock()
    )
    scraper = LinkedinScrapper(
        Url("https://www.linkedin.com/jobs/view/1"),
        session=session,
    )

    scraper.extract()

    session.get.assert_called_once_with(
        str(scraper.url),
        headers=scraper.headers,
        timeout=10,
        allow_redirects=False,
    )
    response.raise_for_status.assert_called_once_with()
    assert scraper.get_job_description() == "Build APIs"
    assert scraper.get_job_criteria() == "level: Mid-Senior"


def test_extract_when_http_fails_uses_selenium_fallback(monkeypatch) -> None:
    session = Mock()
    session.get.side_effect = exceptions.ConnectionError("offline")
    fallback_html = BeautifulSoup(
        '<section class="core-section-container">'
        '<div class="show-more-less-html__markup">Fallback description</div>'
        "</section>",
        "html.parser",
    )
    fallback = Mock(return_value=fallback_html)
    monkeypatch.setattr(
        "job_offer_scraper_mcp.shared.utils.validate_public_http_url", Mock()
    )
    monkeypatch.setattr(
        LinkedinScrapper,
        "_JobOfferExtractor__extract_html_selenium",
        fallback,
    )
    scraper = LinkedinScrapper(
        Url("https://www.linkedin.com/jobs/view/1"),
        session=session,
    )

    scraper.extract()

    fallback.assert_called_once_with()
    assert scraper.get_job_description() == "Fallback description"
    assert scraper.get_job_criteria() is None


def test_extract_when_offer_container_is_absent_leaves_empty_result(
    monkeypatch,
) -> None:
    response = Mock(text="<html></html>")
    response.status_code = 200
    session = Mock()
    session.get.return_value = response
    monkeypatch.setattr(
        "job_offer_scraper_mcp.shared.utils.validate_public_http_url", Mock()
    )
    scraper = LinkedinScrapper(
        Url("https://www.linkedin.com/jobs/view/1"),
        session=session,
    )

    result = scraper.extract()

    assert result is None
    assert scraper.get_job_description() is None
    assert scraper.get_job_criteria() is None


def test_each_extractor_has_its_own_http_session() -> None:
    first = LinkedinScrapper(Url("https://linkedin.com/jobs/view/1"))
    second = LinkedinScrapper(Url("https://linkedin.com/jobs/view/2"))

    assert first.session is not second.session


@patch("seleniumbase.Driver")
def test_selenium_driver_is_closed_when_navigation_fails(
    driver_factory: Mock,
    monkeypatch,
) -> None:
    driver = Mock()
    driver.get.side_effect = RuntimeError("browser failed")
    driver_factory.return_value = driver
    monkeypatch.setattr(
        "job_offer_scraper_mcp.scrapper.base.validate_public_http_url", Mock()
    )
    monkeypatch.setattr(
        "job_offer_scraper_mcp.shared.utils.validate_public_http_url", Mock()
    )
    session = Mock()
    session.get.side_effect = exceptions.ConnectionError("offline")
    scraper = LinkedinScrapper(
        Url("https://linkedin.com/jobs/view/1"),
        session=session,
    )

    result = scraper.extract()

    assert result is None
    driver.quit.assert_called_once_with()
