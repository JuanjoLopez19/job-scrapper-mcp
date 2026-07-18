from unittest.mock import Mock

import pytest
from requests import exceptions

from job_offer_scraper_mcp.shared.url_validation import UnsafeUrlError
from job_offer_scraper_mcp.shared.utils import fetch_url_response, get_url_content


def test_get_url_content_returns_response_text(monkeypatch) -> None:
    response = Mock(text="page content")
    response.status_code = 200
    session = Mock()
    session.get.return_value = response
    validator = Mock()
    monkeypatch.setattr(
        "job_offer_scraper_mcp.shared.utils.validate_public_http_url", validator
    )

    result = get_url_content("https://example.com/job/1", session=session)

    session.get.assert_called_once_with(
        "https://example.com/job/1",
        headers=None,
        timeout=10,
        allow_redirects=False,
    )
    validator.assert_called_once_with("https://example.com/job/1")
    response.raise_for_status.assert_called_once_with()
    assert result == "page content"


def test_get_url_content_propagates_request_error(monkeypatch) -> None:
    error = exceptions.Timeout("timed out")
    session = Mock()
    session.get.side_effect = error
    monkeypatch.setattr(
        "job_offer_scraper_mcp.shared.utils.validate_public_http_url", Mock()
    )

    with pytest.raises(exceptions.Timeout, match="timed out"):
        get_url_content("https://example.com/job/1", session=session)


def test_fetch_url_response_validates_redirect_before_following(monkeypatch) -> None:
    redirect = Mock(
        status_code=302,
        headers={"Location": "http://127.0.0.1/admin"},
    )
    session = Mock()
    session.get.return_value = redirect
    validator = Mock(
        side_effect=[
            "https://example.com/job/1",
            UnsafeUrlError("private address"),
        ]
    )
    monkeypatch.setattr(
        "job_offer_scraper_mcp.shared.utils.validate_public_http_url", validator
    )

    with pytest.raises(UnsafeUrlError, match="private address"):
        fetch_url_response(session, "https://example.com/job/1")

    session.get.assert_called_once()
