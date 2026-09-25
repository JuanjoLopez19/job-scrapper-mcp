"""Console entry point for the optional MCP server."""


def main() -> None:
    """Start the MCP server or explain how to install its optional dependencies."""
    try:
        from job_offer_scraper_mcp.server import main as run_server
    except ModuleNotFoundError as error:
        if error.name != "mcp":
            raise
        raise SystemExit(
            "MCP support is not installed. Run with "
            "`uvx 'job-offer-scraper-mcp[mcp]'` or install "
            "`job-offer-scraper-mcp[mcp]`."
        ) from error

    run_server()
