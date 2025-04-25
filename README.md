# Job Offer Scrapper MCP

## Installation on VS Code

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
