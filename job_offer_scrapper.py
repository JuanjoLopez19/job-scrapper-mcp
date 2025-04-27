import logging
from typing import Any, Dict

from mcp.server import FastMCP as Server
from pydantic import ValidationError
from pydantic_core import Url

from shared.constants import ScrapperSelectionError
from shared.utils import get_url_content

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Inicializar servidor MCP
app = Server(
    name="Job Offer Scrapper",
    description="A server for scraping job offers from various job portals",
    version="1.0.0",
)


@app.tool(
    name="get_job_offer_info", description="Scrap the job offer from the given URL"
)
def get_job_offer(url: str) -> Dict[str, Any]:
    """
    Scrapes job offer information from a given URL, extracting description and criteria.

    This function attempts to parse a job posting using the appropriate scraper based on the
    URL's domain. If the domain is not supported, it falls back to returning the raw HTML content.

    Args:
        url (str): The URL of the job offer to scrape.

    Returns:
        Dict[str, Any]: A dictionary containing the job offer information with these possible keys:
            - description: The job description text if successfully extracted
            - criteria: The job criteria text if successfully extracted
            - content: Raw HTML content (fallback if scraper not available)
            - error: Error message if scraping failed
            - url: The original URL that was processed
            - supported_domains: List of domains that have dedicated scrapers
    """
    from scrapper.factory import FactoryScrapper

    response: Dict[str, Any] = {"url": url}

    logger.info(f"Processing job offer URL: {url}")

    try:
        # Validate URL
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")

        # Convert to Url object
        url_obj = Url(url)

        try:
            # Try to use dedicated scraper
            scrapper = FactoryScrapper.get_scrapper(url_obj)
            extraction_successful = scrapper.extract()

            if extraction_successful:
                logger.info(f"Successfully extracted job offer from {url}")
                # Use the get_extraction_result method if available, otherwise fall back to individual getters
                if hasattr(scrapper, "get_extraction_result"):
                    response.update(scrapper.get_extraction_result())
                else:
                    response.update(
                        {
                            "description": scrapper.get_job_description(),
                            "criteria": scrapper.get_job_criteria(),
                        }
                    )
            else:
                logger.warning(
                    f"Extraction process completed but no data was extracted from {url}"
                )
                response["warning"] = (
                    "Extraction process completed but no data was found"
                )

        except ScrapperSelectionError as e:
            # Domain not supported, fall back to raw content
            logger.info(
                f"No dedicated scraper for {url}, falling back to raw content: {str(e)}"
            )
            response["supported_domains"] = FactoryScrapper.get_supported_domains()

            try:
                content = get_url_content(url)
                response["content"] = content
                response["warning"] = (
                    f"No dedicated scraper available for this URL. Supported domains: {', '.join(response['supported_domains'])}"
                )
            except Exception as content_error:
                logger.error(f"Error fetching raw content: {content_error}")
                response["error"] = f"Failed to fetch content: {str(content_error)}"

    except ValidationError as e:
        # URL validation error
        logger.error(f"Invalid URL format: {e}")
        response["error"] = f"Invalid URL format: {str(e)}"

    except Exception as e:
        # General error
        logger.error(f"Error processing job offer: {e}", exc_info=True)

        response["error"] = f"An error occurred while scraping the job offer: {str(e)}"

    return response


@app.tool(
    name="SupportedSites",
    description="Get a list of job sites that have dedicated scrapers",
)
def get_supported_sites() -> Dict[str, Any]:
    """
    Returns a list of job sites that have dedicated scrapers implemented.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - supported_domains: List of domains with dedicated scrapers
            - count: Number of supported domains
    """
    from scrapper.factory import FactoryScrapper

    domains = FactoryScrapper.get_supported_domains()
    return {"supported_domains": domains, "count": len(domains)}


def main():
    """
    Main entry point to run the MCP server.
    """
    logger.info("Starting Job Offer Scrapper MCP server")
    app.run()


if __name__ == "__main__":
    main()
