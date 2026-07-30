import pytest
from pydantic_core import Url

from job_offer_scraper_mcp.scrapper.factory import FactoryScrapper
from job_offer_scraper_mcp.scrapper.implementations.indeed import IndeedScrapper
from job_offer_scraper_mcp.scrapper.implementations.info_empleo import (
    InfoEmpleoScrapper,
)
from job_offer_scraper_mcp.scrapper.implementations.infojobs import InfoJobsScrapper
from job_offer_scraper_mcp.scrapper.implementations.linkedin import LinkedinScrapper
from job_offer_scraper_mcp.scrapper.implementations.tecnoempleo import (
    TecnoEmpleoScrapper,
)
from job_offer_scraper_mcp.shared.constants import ScrapperSelectionError


@pytest.mark.parametrize(
    ("url", "expected_type"),
    [
        ("https://www.linkedin.com/jobs/view/1", LinkedinScrapper),
        ("https://www.infoempleo.com/ofertasdetrabajo/example", InfoEmpleoScrapper),
        ("https://www.tecnoempleo.com/example", TecnoEmpleoScrapper),
        ("https://es.indeed.com/viewjob?jk=1", IndeedScrapper),
        ("https://www.infojobs.net/madrid/backend/of-i123", InfoJobsScrapper),
        ("https://www.infojobs.com/madrid/backend/of-i123", InfoJobsScrapper),
    ],
)
def test_get_scrapper_for_supported_domain_returns_matching_implementation(
    url: str, expected_type: type
) -> None:
    scraper = FactoryScrapper.get_scrapper(Url(url))

    assert isinstance(scraper, expected_type)
    assert str(scraper.url) == url


def test_get_scrapper_for_unsupported_domain_raises_selection_error() -> None:
    with pytest.raises(ScrapperSelectionError, match="Unsupported domain: example.com"):
        FactoryScrapper.get_scrapper(Url("https://example.com/job/1"))


@pytest.mark.parametrize(
    "url",
    [
        "https://linkedin.com.evil.example/jobs/view/1",
        "https://fakeinfoempleo.com/job/1",
        "https://indeed.com.attacker.example/viewjob/1",
        "https://infojobs.net.attacker.example/madrid/backend/of-i123",
    ],
)
def test_get_scrapper_rejects_domains_that_only_contain_supported_name(
    url: str,
) -> None:
    with pytest.raises(ScrapperSelectionError):
        FactoryScrapper.get_scrapper(Url(url))


def test_get_scrapper_for_url_without_domain_raises_value_error() -> None:
    with pytest.raises(ValueError, match="No domain found"):
        FactoryScrapper.get_scrapper(Url("mailto:jobs@example.com"))
