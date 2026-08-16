import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


def test_portable_plugin_manifest_uses_agent_plugins_v1_layout() -> None:
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))

    assert manifest["$schema"] == PLUGIN_SCHEMA
    assert manifest["name"] == "job-offer-application"
    assert not ({"skills", "mcpServers"} & manifest.keys())
    assert (ROOT / "skills").is_dir()
    assert (ROOT / "mcp.json").is_file()


def test_all_immediate_skill_directories_have_matching_manifests() -> None:
    skill_names = set()

    for skill_dir in (ROOT / "skills").iterdir():
        if not skill_dir.is_dir():
            continue

        skill_manifest = skill_dir / "SKILL.md"
        assert skill_manifest.is_file()
        contents = skill_manifest.read_text(encoding="utf-8")
        assert f"name: {skill_dir.name}" in contents.split("---", maxsplit=2)[1]
        skill_names.add(skill_dir.name)

    assert skill_names == {"tailor-latex-cv", "write-cover-letter"}


def test_mcp_config_declares_the_published_stdio_server() -> None:
    config = json.loads((ROOT / "mcp.json").read_text(encoding="utf-8"))

    assert config["$schema"] == MCP_SCHEMA
    assert set(config) == {"$schema", "mcpServers"}
    assert config["mcpServers"] == {
        "job-offer-scraper": {
            "type": "stdio",
            "command": "uvx",
            "args": ["job-offer-scraper-mcp"],
        }
    }
