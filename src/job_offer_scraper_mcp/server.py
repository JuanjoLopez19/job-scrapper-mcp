import logging

from mcp.server import FastMCP
from mcp.types import ToolAnnotations
from pydantic_core import Url
from requests import RequestException

from job_offer_scraper_mcp.shared.constants import JobOfferInfo, ScrapperSelectionError
from job_offer_scraper_mcp.shared.url_validation import UnsafeUrlError
from job_offer_scraper_mcp.shared.utils import get_url_content

logger = logging.getLogger(__name__)


def _error_response(code: str, message: str) -> dict[str, object]:
    return {"error": {"code": code, "message": message}}


app = FastMCP(
    name="Job Offer Scraper",
    instructions=(
        "Extract structured descriptions and employment criteria from job-offer "
        "URLs. Supports LinkedIn, InfoEmpleo, TecnoEmpleo, Indeed and InfoJobs."
    ),
    website_url="https://github.com/JuanjoLopez19/job-scrapper-mcp",
)


@app.tool(
    name="get_job_offer_details",
    description=(
        "Extract the description and employment criteria from a public job-offer URL."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
def get_job_offer(url: str) -> JobOfferInfo | dict[str, object]:
    """
    Scraps the job offer from the given URL.
    Args:
        url (str): The URL of the job offer to scrap.
    Returns:
        dict: A dictionary containing the job offer information.
    """
    from job_offer_scraper_mcp.scrapper.factory import FactoryScrapper

    try:
        scraper = FactoryScrapper.get_scrapper(Url(url))
        scraper.extract()
        return scraper.get_job_offer_info()
    except ScrapperSelectionError:
        try:
            content = get_url_content(url)
            return {
                "content": content,
            }
        except UnsafeUrlError:
            logger.warning("Blocked unsafe fallback URL")
            return _error_response(
                "unsafe_url",
                "The URL is not allowed because it targets a non-public resource.",
            )
        except RequestException:
            logger.exception("Unable to fetch unsupported job site")
            return _error_response(
                "fetch_failed",
                "The page could not be downloaded.",
            )
        except Exception:
            logger.exception("Unexpected fallback extraction error")
            return _error_response(
                "internal_error",
                "The job offer could not be processed.",
            )
    except UnsafeUrlError:
        logger.warning("Blocked unsafe scraper URL")
        return _error_response(
            "unsafe_url",
            "The URL is not allowed because it targets a non-public resource.",
        )
    except (ValueError, RequestException):
        logger.warning("Invalid or unreachable job offer URL")
        return _error_response(
            "invalid_url",
            "The provided job offer URL is invalid or unreachable.",
        )
    except Exception:
        logger.exception("Unexpected job offer extraction error")
        return _error_response(
            "extraction_failed",
            "The job offer could not be extracted.",
        )


def main():
    app.run()


if __name__ == "__main__":
    main()
