# Job Offer Scraper MCP

## Overview

This is an implementation of the Model Context Protocol (MCP) that allows VS Code users to search for job offers from popular job sites in Spain. The tool uses web scraping techniques to extract detailed information from job listings.

## Supported Job Sites

| Site        | Status         |
| ----------- | -------------- |
| LinkedIn    | ✅ Implemented |
| TecnoEmpleo | ✅ Implemented |
| InfoEmpleo  | ✅ Implemented |
| Indeed      | 🔄 In Progress |
| InfoJobs    | 📝 Planned     |

## Features

- Extract job descriptions from supported job sites
- Parse job criteria and requirements when available
- Simple API for integrating with VS Code via MCP

## Installation and Setup

### Prerequisites

- Python 3.13 or higher
- VS Code with MCP support
- `uv` package manager

### VS Code Configuration

Add the following to your VS Code settings:

```json
"mcp": {
    "inputs": [],
    "servers": {
        "job-offer-scrapper": {
            "command": "uv",
            "args": [
                "--directory",
                "${env:USERPROFILE}/Documents/GitHub/mcp-python", // Configure this path to your local mcp-python repository
                "run",
                "python",
                "-m",
                "job_offer_scrapper"
            ],
        },
        "filesystem": {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                "${env:USERPROFILE}/Desktop", // Configure the paths you want to expose to the MCP server
            ]
        }
    }
},
```

## Usage

After configuring the MCP server in VS Code, you can use it with compatible AI assistants to get information about job offers by providing URLs from supported job sites.

## Development

To contribute or extend this project:

1. Clone the repository
2. Install dependencies with `uv sync`
3. Implement new scrapers in the `src/scrapper` directory
4. Update the factory to support new job sites

## License

[MIT License](LICENSE)
