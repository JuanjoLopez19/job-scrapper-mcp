# MCP setup

The skill expects an MCP server exposing the read-only tool `get_job_offer_details`.

## Published package

Configure clients that accept a command and argument list with:

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

## GitHub source

Before a usable package release is available, configure:

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

Restart or reload the MCP client after changing its configuration. Do not launch the stdio server as an unattended shell process and assume its tools are registered; the client must manage the MCP process.

If the tool remains unavailable, continue with the skill's web-retrieval fallback rather than blocking CV tailoring setup indefinitely.
