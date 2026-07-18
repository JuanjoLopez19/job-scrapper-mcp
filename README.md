# Job Offer Scraper MCP

An MCP server that extracts job descriptions and criteria from job offer pages.

## Supported sites

| Site | Status |
| --- | --- |
| LinkedIn | Implemented |
| TecnoEmpleo | Implemented |
| InfoEmpleo | Implemented |
| Indeed | In progress |

## Run without cloning

Once the package is published on PyPI:

```bash
uvx job-offer-scraper-mcp
```

It can also be executed directly from GitHub without manually cloning the repository:

```bash
uvx --from git+https://github.com/JuanjoLopez19/job-scrapper-mcp.git job-offer-scraper-mcp
```

`uvx` creates an isolated environment and caches the package and its dependencies.

## MCP client configuration

Example configuration for clients that accept a command and argument list:

```json
{
  "servers": {
    "job-offer-scraper": {
      "command": "uvx",
      "args": ["job-offer-scraper-mcp"]
    }
  }
}
```

Before the first PyPI release, use the GitHub source explicitly:

```json
{
  "servers": {
    "job-offer-scraper": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/JuanjoLopez19/job-scrapper-mcp.git",
        "job-offer-scraper-mcp"
      ]
    }
  }
}
```

## Local development

Requirements:

- Python 3.11 or newer
- `uv`

Install dependencies and run the quality suite:

```bash
uv sync
uv run pre-commit run --all-files
```

Run the MCP server from the working tree:

```bash
uv run job-offer-scraper-mcp
```

Build and smoke-test the distribution:

```bash
uv build --no-sources
uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py
```

## Publishing

Releases are published to PyPI by `.github/workflows/release.yml` when a tag beginning with `v` is pushed. The `pypi` GitHub environment and a matching PyPI Trusted Publisher must be configured before the first release.

## License

[MIT](LICENSE)
