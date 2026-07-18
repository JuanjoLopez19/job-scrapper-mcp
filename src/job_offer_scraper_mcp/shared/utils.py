import logging
from urllib.parse import urljoin

from pydantic_core import Url
from requests import Response, Session, TooManyRedirects

from job_offer_scraper_mcp.shared.url_validation import validate_public_http_url

logger = logging.getLogger(__name__)

MAX_REDIRECTS = 5
REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


def fetch_url_response(
    session: Session,
    url: str | Url,
    *,
    headers: dict[str, str] | None = None,
) -> Response:
    """Fetch a public URL while validating every redirect target."""
    current_url = str(url)
    for redirect_count in range(MAX_REDIRECTS + 1):
        validate_public_http_url(current_url)
        response = session.get(
            current_url,
            headers=headers,
            timeout=10,
            allow_redirects=False,
        )
        if response.status_code not in REDIRECT_STATUS_CODES:
            response.raise_for_status()
            return response

        location = response.headers.get("Location")
        if location is None:
            response.raise_for_status()
            return response
        if redirect_count == MAX_REDIRECTS:
            raise TooManyRedirects(f"Exceeded {MAX_REDIRECTS} redirects.")
        current_url = urljoin(current_url, location)

    raise TooManyRedirects(f"Exceeded {MAX_REDIRECTS} redirects.")


def get_url_content(url: str | Url, session: Session | None = None) -> str:
    """Return the contents of a public URL without exposing internal networks."""
    active_session = session or Session()
    try:
        return fetch_url_response(active_session, url).text
    except Exception:
        logger.exception("Unable to fetch URL content")
        raise
