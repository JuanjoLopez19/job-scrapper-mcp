import logging

from pydantic_core import Url
from requests import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_url_content(url: Url):
    try:
        session = Session()
        response = session.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
        return response.text
    except Exception as e:
        logger.error(f"Error fetching URL content: {e}")
        raise e
