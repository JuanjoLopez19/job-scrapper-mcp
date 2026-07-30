import pytest
from bs4 import BeautifulSoup
from pydantic_core import Url

from job_offer_scraper_mcp.scrapper.implementations.infojobs import InfoJobsScrapper


@pytest.fixture
def scraper() -> InfoJobsScrapper:
    return InfoJobsScrapper(Url("https://www.infojobs.net/madrid/backend/of-i123"))


def test_find_job_offer_info_returns_main_content_container(
    scraper: InfoJobsScrapper,
) -> None:
    soup = BeautifulSoup(
        """
        <div class="ij-Box ij-OfferDetailPage-mainContent-container">
            <article>Offer content</article>
        </div>
        """,
        "html.parser",
    )

    container = scraper.find_job_offer_info(soup)

    assert container is not None
    assert container.get_text(strip=True) == "Offer content"


def test_find_job_offer_info_without_main_content_returns_none(
    scraper: InfoJobsScrapper,
) -> None:
    assert scraper.find_job_offer_info(BeautifulSoup("", "html.parser")) is None


def test_find_job_description_extracts_normalized_text(
    scraper: InfoJobsScrapper,
) -> None:
    soup = BeautifulSoup(
        """
        <article><dl><dt>Experiencia mínima</dt><dd>2 años</dd></dl></article>
        <article>
            <div class="ij-Box mb-xl mt-l ij-EnrichedTextArea-paragraph">
                Build reliable APIs
            </div>
        </article>
        """,
        "html.parser",
    )

    assert scraper.find_job_description(soup) == "Build reliable APIs"


@pytest.mark.parametrize(
    "markup",
    [
        "",
        "<article>Only one article</article>",
        "<article></article><article>Missing description div</article>",
    ],
)
def test_find_job_description_with_incomplete_markup_returns_none(
    scraper: InfoJobsScrapper,
    markup: str,
) -> None:
    assert scraper.find_job_description(BeautifulSoup(markup, "html.parser")) is None


def test_find_job_criteria_combines_both_sections(
    scraper: InfoJobsScrapper,
) -> None:
    soup = BeautifulSoup(
        """
        <article>
            <dl>
                <dt>Estudios mínimos</dt><dd>Grado</dd>
                <dt>Conocimientos necesarios</dt>
                <dd><a>Python</a><a>REST</a></dd>
            </dl>
        </article>
        <article>
            <dl>
                <dt>Vacantes</dt><dd>2</dd>
                <dt>Salario</dt><dd>40.000€ - 50.000€ Bruto/año</dd>
            </dl>
        </article>
        """,
        "html.parser",
    )

    assert scraper.find_job_criteria(soup) == (
        "Estudios mínimos: Grado\n"
        "Conocimientos necesarios: Python, REST\n"
        "Vacantes: 2\n"
        "Salario: 40.000€ - 50.000€ Bruto/año"
    )


@pytest.mark.parametrize(
    "markup",
    [
        "",
        "<article><dl></dl></article>",
        "<article></article><article><dl></dl></article>",
        "<article><dl></dl></article><article></article>",
    ],
)
def test_find_job_criteria_with_incomplete_markup_returns_none(
    scraper: InfoJobsScrapper,
    markup: str,
) -> None:
    assert scraper.find_job_criteria(BeautifulSoup(markup, "html.parser")) is None


def test_find_job_title_and_location_extract_page_title(
    scraper: InfoJobsScrapper,
) -> None:
    soup = BeautifulSoup(
        "<title>Oferta de empleo: Backend Engineer en Madrid - InfoJobs</title>",
        "html.parser",
    )

    assert scraper.find_job_title(soup) == "Backend Engineer"
    assert scraper.find_job_location(soup) == "Madrid"


@pytest.mark.parametrize(
    "markup",
    ["", "<title>Unexpected page title</title>"],
)
def test_find_job_title_and_location_without_expected_title_return_none(
    scraper: InfoJobsScrapper,
    markup: str,
) -> None:
    soup = BeautifulSoup(markup, "html.parser")

    assert scraper.find_job_title(soup) is None
    assert scraper.find_job_location(soup) is None


def test_find_job_company_extracts_description_metadata(
    scraper: InfoJobsScrapper,
) -> None:
    soup = BeautifulSoup(
        '<meta name="description" content="Trabaja en la empresa Acme S.L. '
        'Consulta los requisitos.">',
        "html.parser",
    )

    assert scraper.find_job_company(soup) == "Acme S.L"


@pytest.mark.parametrize(
    "markup",
    [
        "",
        '<meta name="description">',
        '<meta name="description" content="Unexpected description">',
    ],
)
def test_find_job_company_without_expected_metadata_returns_none(
    scraper: InfoJobsScrapper,
    markup: str,
) -> None:
    assert scraper.find_job_company(BeautifulSoup(markup, "html.parser")) is None
