<div align="center">

# 🔎 Job Offer Scraper MCP

**Structured job-offer extraction for AI agents — plus truthful, verified LaTeX CV tailoring.**

[![CI](https://github.com/JuanjoLopez19/job-scrapper-mcp/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/JuanjoLopez19/job-scrapper-mcp/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/Model_Context_Protocol-server-6F42C1)
![uv](https://img.shields.io/badge/managed_with-uv-DE5FE9)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

`job-offer-scraper-mcp` exposes a read-only MCP tool that turns public job URLs
into structured descriptions and criteria. This repository also ships the
remotely installable `tailor-latex-cv` Codex skill, which adapts a real LaTeX CV
to an offer, compiles it with a verified Tectonic binary, and checks that the PDF
remains machine-readable.

## ✨ Highlights

| Capability           | What it provides                                                                       |
| -------------------- | -------------------------------------------------------------------------------------- |
| 🔗 Job extraction    | One MCP tool for LinkedIn, TecnoEmpleo, InfoEmpleo, Indeed, InfoJobs, and generic pages |
| 🧱 Structured output | Job description and employment criteria ready for agent workflows                      |
| 🛡️ Safer fetching    | Public-URL validation, read-only annotations, and explicit error responses             |
| 📝 CV tailoring      | Evidence-based LaTeX rewriting without fabricated experience or hidden keywords        |
| ✅ PDF verification  | Pinned Tectonic download, SHA-256 validation, compilation, and extractable-text checks |
| 📦 Zero-clone usage  | Run the MCP with `uvx` and install the skill directly from GitHub                      |

## 🚀 Quick start

Run the published package in an isolated UV environment:

```bash
uvx job-offer-scraper-mcp
```

Or run directly from GitHub:

```bash
uvx --from git+https://github.com/JuanjoLopez19/job-scrapper-mcp.git job-offer-scraper-mcp
```

### MCP client configuration

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

To use the GitHub source before or instead of a PyPI release:

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

## 🌐 Supported job sites

| Site               | Status         | Strategy                                      |
| ------------------ | -------------- | --------------------------------------------- |
| LinkedIn           | ✅ Implemented | Dedicated extractor                           |
| TecnoEmpleo        | ✅ Implemented | Dedicated extractor                           |
| InfoEmpleo         | ✅ Implemented | Dedicated extractor                           |
| Indeed             | ✅ Implemented | Dedicated extractor with JSON data extraction |
| InfoJobs           | ✅ Implemented | Dedicated extractor                           |
| Other public sites | ✅ Fallback    | Generic safe HTML retrieval                   |

The MCP exposes:

```text
get_job_offer_details(url: string)
```

Successful responses contain `description` and `criteria`, or generic page
`content`. Failures use a structured `error` object with a stable code.

## 🧩 Install the LaTeX CV tailoring skill

Ask Codex to install the skill from this GitHub path:

```text
https://github.com/JuanjoLopez19/job-scrapper-mcp/tree/master/skills/tailor-latex-cv
```

The skill and MCP server are separate components: install the skill from GitHub,
then register the MCP server with `uvx` using the configuration above.

### Workflow

```mermaid
flowchart LR
    A[LaTeX CV + job URL] --> B{Job Offer MCP}
    B -->|Success| E[Evidence-based match]
    B -->|Unavailable| C[Web fallback]
    C -->|Unavailable| D[Ask user for offer text]
    C --> E
    D --> E
    E --> F[Truthful visible tailoring]
    F --> G[Tectonic compilation]
    G --> H[pypdf text verification]
    H --> I[Atomic PDF publication]
    I --> J[Tailored .tex + verified PDF]
```

The workflow preserves the original CV, integrates only supported keywords in
visible recruiter-readable text, and reports material requirements that the CV
does not substantiate.

## 🧪 Compile and verify a tailored CV

The skill includes a portable Python utility managed by UV:

```bash
uv run skills/tailor-latex-cv/scripts/compile_latex.py cv-tailored.tex \
  --install-tectonic \
  --expected-keyword Python \
  --expected-keyword "REST APIs"
```

On first use, `--install-tectonic` downloads the pinned official Tectonic 0.16.9
binary for the current platform and verifies its SHA-256 digest. Compilation
runs in Tectonic's untrusted mode using a pinned direct official resource bundle
URL. The generated PDF is then opened with `pypdf`, which verifies page count,
extractable text, and requested keywords. Only after those checks pass, the
utility atomically publishes the final PDF beside the tailored `.tex`.

Omit `--install-tectonic` to prohibit compiler downloads. Use
`--forbidden-keyword` to fail verification if an unsupported requirement appears
in the generated PDF. Use `--final-pdf <path>` to select another deliverable
location. Existing PDFs are preserved with a numbered suffix unless
`--overwrite-final` is explicitly supplied.

> [!NOTE]
> On Windows, replace decorative `fontawesome5` icons with visible contact
> labels in the tailored copy. The verifier detects this package before
> compilation because the pinned Windows Tectonic build cannot load it reliably.

## 🛡️ Integrity and security

- The MCP accepts only public HTTP(S) targets and blocks unsafe local resources.
- The MCP tool is annotated as read-only, idempotent, and non-destructive.
- Job-page content is treated as untrusted input rather than agent instructions.
- CV tailoring never invents experience or inserts invisible ATS keywords.
- Tectonic release archives are pinned and hash-verified before execution.
- LaTeX compilation uses `--untrusted` to disable known-insecure engine features.

## 🛠️ Development

Requirements:

- Python 3.11 or newer
- [UV](https://docs.astral.sh/uv/)

Install dependencies and enable the quality hooks:

```bash
uv sync
uv run pre-commit install
```

Run the complete quality suite:

```bash
uv run pre-commit run --all-files
```

Run the MCP from the working tree:

```bash
uv run job-offer-scraper-mcp
```

Build and smoke-test the distribution:

```bash
uv build --no-sources
uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py
```

## 📁 Project layout

```text
├── src/job_offer_scraper_mcp/   # MCP server and scraper implementations
├── skills/tailor-latex-cv/      # Remotely installable Codex skill
│   ├── agents/openai.yaml
│   ├── references/
│   ├── scripts/compile_latex.py
│   └── SKILL.md
├── tests/                       # Unit, integration, and smoke tests
├── pyproject.toml               # UV project and quality configuration
└── .pre-commit-config.yaml      # Ruff, Pyrefly, and pytest hooks
```

## 📦 Publishing

Tags beginning with `v` trigger `.github/workflows/release.yml`, which builds,
smoke-tests, and publishes the package to PyPI through Trusted Publishing.

## 📄 License

Distributed under the [MIT License](LICENSE).
