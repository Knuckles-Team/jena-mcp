"""PIPE-CONNSPEC-R130.4: Jena MCP rapid-delivery skill contract."""

from __future__ import annotations

import re
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "jena_mcp/skills/jena-mcp-development/SKILL.md"


def test_development_skill_binds_jena_contract_and_package_data() -> None:
    text = SKILL.read_text(encoding="utf-8")

    assert text.startswith("---\nname: jena-mcp-development\n")
    assert "## Rapid delivery: the 5-minute contract" in text
    assert "PIPE-CONNSPEC-R130.4" in text
    for reference in (
        "jena_mcp/api/api_client_jena.py",
        "jena_mcp/mcp/mcp_jena.py",
        "jena_mcp/auth.py",
        "jena_mcp/connector_sources.py",
        "APACHE_JENA_URL",
        "JENA_TLS_PROFILE",
    ):
        assert reference in text

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert "skills/**" in data["tool"]["setuptools"]["package-data"]["jena_mcp"]
    assert SKILL.is_file()
    assert not re.search(r"(?:sk-|ghp_|Bearer\s+)[A-Za-z0-9_./-]{12,}", text)
    assert data["project"]["name"] == "jena-mcp"


def test_legacy_mkdocs_publisher_is_absent() -> None:
    assert not (ROOT / ".github/workflows/docs.yml").exists()
