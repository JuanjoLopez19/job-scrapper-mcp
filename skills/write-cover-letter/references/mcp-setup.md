# MCP setup

When this skill is installed as part of the Agent Plugin, the root `mcp.json` declares the `job-offer-scraper` server automatically for compatible clients.

For a standalone skill installation, configure a client that accepts a command and argument list with:

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

To run from the repository source before a compatible package release is available, use:

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

Reload the MCP client after changing its configuration. If the tool is still unavailable, continue with public web retrieval instead of blocking the letter workflow.
