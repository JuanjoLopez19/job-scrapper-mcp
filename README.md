# Job Offer Scraper MCP

Read-only job-application tooling for AI agents.

Give the MCP a public job-offer URL and it returns structured, agent-ready data. Add the bundled skills when you want a LaTeX CV or cover letter written from evidence you already have — never from invented experience.

[![PyPI](https://img.shields.io/pypi/v/job-offer-scraper-mcp?color=1a1917&label=PyPI)](https://pypi.org/project/job-offer-scraper-mcp/)
[![Python](https://img.shields.io/badge/python-3.11%2B-b45c43)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-read--only-1a1917)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/license-MIT-b45c43)](LICENSE)

## The small version

```text
public job URL
      ↓
get_job_offer_details
      ↓
description + employment criteria
      ↓
truthful CV tailoring or a separate cover letter
```

The scraper is one narrow tool. The two skills are independent, so you can install the whole workflow or only the piece you need.

## What is included

| Piece | Responsibility | Location |
| --- | --- | --- |
| Job-offer scraper | Extract a description and employment criteria from a public URL. | MCP tool `get_job_offer_details` |
| LaTeX CV tailoring | Match requirements to an existing `.tex` CV and write a verified tailored copy. | [`skills/tailor-latex-cv`](skills/tailor-latex-cv) |
| Cover letter | Write a separate, job-specific letter from the offer and candidate evidence. | [`skills/write-cover-letter`](skills/write-cover-letter) |

## Install

### Published package

Clients that support MCP server configuration can start the published package with `uvx`:

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

The same command is the quickest local smoke test:

```bash
uvx job-offer-scraper-mcp
```

This is a stdio server. Let the MCP client manage its process; do not start it as a background shell process and expect tools to appear automatically.

### Agent Plugin

The repository includes [`mcp.json`](mcp.json), which declares the server for compatible Agent Plugin clients. Install the repository as a plugin in your client and it can discover the MCP server and both skills together.

### From this checkout

This project uses [uv](https://docs.astral.sh/uv/) for Python dependencies:

```bash
uv sync --dev
uv run job-offer-scraper-mcp
```

## The MCP tool

The server exposes one tool:

```text
get_job_offer_details(url: string)
```

For a supported job board, the result contains these fields:

```json
{
  "url": "https://example.com/jobs/123",
  "title": "Example role",
  "company_name": "Example company",
  "location": "Madrid",
  "description": "The public job description...",
  "criteria": "Full-time; Python; REST APIs"
}
```

For another public page, the server falls back to its fetched page content:

```json
{
  "content": "The readable public page content..."
}
```

Failures are explicit rather than silent. The server returns an error code such as `invalid_url`, `unsafe_url`, `fetch_failed`, or `extraction_failed` when it cannot complete the request.

## Supported sources

Dedicated extractors currently cover:

- LinkedIn
- InfoEmpleo
- TecnoEmpleo
- Indeed
- InfoJobs

Other public HTTP(S) pages use the generic content fallback when they can be fetched safely. Private network targets, local files, and other unsafe URL targets are rejected.

## Skills

### Tailor a LaTeX CV

[`skills/tailor-latex-cv`](skills/tailor-latex-cv) takes:

1. The path to an existing `.tex` CV.
2. A public job-offer URL.

It retrieves the offer through the MCP, builds a direct/equivalent/unsupported evidence match, writes a sibling tailored copy, and compiles it before publishing a PDF. The source CV is not overwritten by default.

Unsupported requirements stay out of the document. Keywords are visible recruiter-readable text, never hidden ATS tricks.

### Write a cover letter

[`skills/write-cover-letter`](skills/write-cover-letter) takes:

1. A public job-offer URL.
2. A CV, profile, or concise list of candidate facts.

It writes a separate 250–400 word letter by default. It does not edit the CV, invent motivation, or claim skills the supplied evidence cannot support.

Both skills treat candidate files as sensitive local evidence and job-page content as untrusted input.

## A truthful workflow

1. **Fetch** — validate the public URL and read the page.
2. **Structure** — turn role details and criteria into agent-ready fields.
3. **Match** — compare every requirement with the local CV or profile.
4. **Write** — create a tailored `.tex` copy or an independent letter.
5. **Verify** — compile and inspect the CV PDF before treating it as done.

## Design constraints

This project deliberately does not:

- invent roles, skills, metrics, or motivation;
- add invisible keywords, white-on-white text, or metadata stuffing;
- upload a CV to a third-party service;
- access local files through the scraper;
- hide extraction, fetching, or PDF-verification failures.

The MCP tool is annotated as read-only, idempotent, and non-destructive. Public page content is treated as data, not as instructions for the agent.

## Development

Install the development environment:

```bash
uv sync --dev
pre-commit install
```

Run the Python quality gates:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
pre-commit run --all-files
```

The optional landing site lives in [`website`](website) and uses pnpm, TypeScript, and Biome:

```bash
pnpm install
pnpm --dir website check
pnpm --dir website build
```

## Repository map

```text
.
├── mcp.json                         # Agent Plugin MCP declaration
├── src/job_offer_scraper_mcp/       # MCP server and site extractors
├── skills/tailor-latex-cv/           # Evidence-based LaTeX CV workflow
├── skills/write-cover-letter/        # Evidence-based cover-letter workflow
├── website/                          # Landing page
├── tests/                            # Unit and smoke tests
└── pyproject.toml                    # Package and tool configuration
```

## License

MIT. See [`LICENSE`](LICENSE).

Maintained by [JuanjoLopez19](https://github.com/JuanjoLopez19).
