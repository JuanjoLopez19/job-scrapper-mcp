from mcp.server import FastMCP as Server
from pydantic_core import Url

from shared.constants import ScrapperSelectionError
from shared.utils import get_url_content

app = Server(
    name="Job offer Scrapper",
)


@app.tool(name="Scrapper", description="Scrap the job offer from the given URL")
def get_job_offer(url: str) -> dict:
    """
    Scraps the job offer from the given URL.
    Args:
        url (str): The URL of the job offer to scrap.
    Returns:
        dict: A dictionary containing the job offer information.
    """
    from scrapper.factory import FactoryScrapper

    try:
        scrapper = FactoryScrapper.get_scrapper(Url(url))
        scrapper.extract()
        return {
            "description": scrapper.get_job_description(),
            "criteria": scrapper.get_job_criteria(),
        }
    except ScrapperSelectionError:
        try:
            content = get_url_content(url)
            return {
                "content": content,
            }
        except Exception as e:
            return {
                "error": str(e),
            }
    except Exception as e:
        return {
            "error": f"An error occurred while scrapping the job offer: {str(e)}",
        }


def main():
    app.run()


if __name__ == "__main__":
    main()
