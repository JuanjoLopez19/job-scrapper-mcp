# mcp_tools/internet_search_tool.py
import logging
import requests
from mcp.server.fastmcp import FastMCP
from urllib.parse import quote_plus

# load environment variables from .env
from dotenv import load_dotenv
import os
load_dotenv()


logger = logging.getLogger(__name__)

class InternetSearchTool:
    def __init__(self):
        self.mcp = FastMCP(name="Internet Search Tool")
        self.register_tools()
        
    def register_tools(self):
        @self.mcp.tool(name="InternetSearch", description="Search for information on the internet")
        def search_internet(query: str) -> dict:
            """
            Performs an internet search for the given query.
            
            Args:
                query (str): The search query.
                
            Returns:
                dict: A dictionary containing search results or an error message.
            """
            try:
                return self._perform_search(query)
            except Exception as e:
                logger.error(f"Error performing search: {e}", exc_info=True)
                return {"error": f"Error performing search: {str(e)}"}
    
    def _perform_search(self, query: str) -> dict:
        """Search implementation using Brave Search API"""
        try:
            if (SEARCH_PROVIDER == "brave"):
                return self._brave_search(query)

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"error": f"Search error: {str(e)}"}
    
    def _brave_search(self, query: str) -> dict:
        """Perform search using Brave Search API"""
        if not BRAVE_SEARCH_API_KEY:
            logger.warning("Brave Search API key not configured")
            return {"error": "Brave Search API key not configured"}
        
        try:
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": BRAVE_SEARCH_API_KEY
            }
            
            url = f"https://api.search.brave.com/res/v1/web/search?q={quote_plus(query)}&count=5"
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant information from the response
            results = {
                "web_pages": [],
                "query": query,
                "abstract": ""
            }
            
            # Extract the first result's description as an abstract if available
            if data.get("web", {}).get("results") and len(data["web"]["results"]) > 0:
                results["abstract"] = data["web"]["results"][0].get("description", "")
            
            # Get web results
            for item in data.get("web", {}).get("results", []):
                results["web_pages"].append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", "")
                })
            
            return results
        except Exception as e:
            logger.error(f"Brave Search error: {e}")
            return {"error": f"Brave Search error: {str(e)}"}
    
    def run(self):
        self.mcp.run()

if __name__ == "__main__":
    # Load environment variables
    BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")
    SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "brave")  # Default to Brave Search
    
    # Initialize and run the tool
    internet_search_tool = InternetSearchTool()
    internet_search_tool.run()