from importlib.metadata import distribution


def main() -> None:
    from job_offer_scraper_mcp.server import app

    package = distribution("job-offer-scraper-mcp")
    commands = {
        entry_point.name
        for entry_point in package.entry_points
        if entry_point.group == "console_scripts"
    }

    assert app.name == "Job offer Scrapper"
    assert "job-offer-scraper-mcp" in commands
    assert package.read_text("METADATA") is not None


if __name__ == "__main__":
    main()
