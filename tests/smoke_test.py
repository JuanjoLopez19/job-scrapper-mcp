from importlib.metadata import distribution


def main() -> None:
    from job_offer_scraper_mcp.cli import main as cli_main

    package = distribution("job-offer-scraper-mcp")
    commands = {
        entry_point.name: entry_point
        for entry_point in package.entry_points
        if entry_point.group == "console_scripts"
    }

    assert callable(cli_main)
    assert commands["job-offer-scraper-mcp"].value == "job_offer_scraper_mcp.cli:main"
    assert package.read_text("METADATA") is not None


if __name__ == "__main__":
    main()
