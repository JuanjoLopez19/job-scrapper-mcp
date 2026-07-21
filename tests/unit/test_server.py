from unittest.mock import Mock

from pydantic_core import Url

from job_offer_scraper_mcp import server
from job_offer_scraper_mcp.scrapper.factory import FactoryScrapper
from job_offer_scraper_mcp.shared.constants import JobOfferInfo, ScrapperSelectionError
from job_offer_scraper_mcp.shared.url_validation import UnsafeUrlError


def test_get_job_offer_for_supported_site_returns_extracted_fields(
    monkeypatch,
) -> None:
    scraper = Mock()
    job_offer = JobOfferInfo(
        url=Url("https://linkedin.com/jobs/view/1"),
        title="Senior Backend Engineer",
        company_name="Example Company",
        location="Madrid",
        description="Build reliable services",
        criteria="type: Full-time",
    )
    scraper.get_job_offer_info.return_value = job_offer
    monkeypatch.setattr(FactoryScrapper, "get_scrapper", Mock(return_value=scraper))

    result = server.get_job_offer("https://linkedin.com/jobs/view/1")

    scraper.extract.assert_called_once_with()
    scraper.get_job_offer_info.assert_called_once_with()
    assert result == job_offer


def test_get_job_offer_for_unsupported_site_returns_raw_content(monkeypatch) -> None:
    monkeypatch.setattr(
        FactoryScrapper,
        "get_scrapper",
        Mock(side_effect=ScrapperSelectionError("unsupported")),
    )
    get_content = Mock(return_value="raw page")
    monkeypatch.setattr(server, "get_url_content", get_content)

    result = server.get_job_offer("https://example.com/job/1")

    get_content.assert_called_once()
    assert result == {"content": "raw page"}


def test_get_job_offer_when_scraper_fails_returns_contextual_error(monkeypatch) -> None:
    monkeypatch.setattr(
        FactoryScrapper,
        "get_scrapper",
        Mock(side_effect=RuntimeError("parser changed")),
    )

    result = server.get_job_offer("https://linkedin.com/jobs/view/1")

    assert result == {
        "error": {
            "code": "extraction_failed",
            "message": "The job offer could not be extracted.",
        }
    }


def test_get_job_offer_when_fallback_fails_returns_original_error(monkeypatch) -> None:
    monkeypatch.setattr(
        FactoryScrapper,
        "get_scrapper",
        Mock(side_effect=ScrapperSelectionError("unsupported")),
    )
    monkeypatch.setattr(
        server,
        "get_url_content",
        Mock(side_effect=TimeoutError("timed out")),
    )

    result = server.get_job_offer("https://example.com/job/1")

    assert result == {
        "error": {
            "code": "internal_error",
            "message": "The job offer could not be processed.",
        }
    }


def test_get_job_offer_when_fallback_is_private_returns_safe_error(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        FactoryScrapper,
        "get_scrapper",
        Mock(side_effect=ScrapperSelectionError("unsupported")),
    )
    monkeypatch.setattr(
        server,
        "get_url_content",
        Mock(side_effect=UnsafeUrlError("private address 127.0.0.1")),
    )

    result = server.get_job_offer("http://127.0.0.1/admin")

    assert result == {
        "error": {
            "code": "unsafe_url",
            "message": (
                "The URL is not allowed because it targets a non-public resource."
            ),
        }
    }
