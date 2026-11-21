"""CONN-JENA-MCP-CONNECTOR-CONTENT-R002: the pack extends only the core ontology."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.spec("CONN-JENA-MCP-CONNECTOR-CONTENT-R002")

TURTLE = Path(__file__).resolve().parents[1] / "jena_mcp/ontology/jena.ttl"
CORE_NAMES = ("RdfGraph", "tripleCount")
CORE_REFERENCES = ("core:RdfGraph",)


def test_pack_declares_no_core_term() -> None:
    text = TURTLE.read_text()
    for name in CORE_NAMES:
        assert not re.search(rf"^:{name}\s", text, re.M), (
            f"pack redeclares core term {name}"
        )
        assert not re.search(rf"(?<![\w:]):{name}(?![\w-])", text), (
            f"pack references :{name}"
        )
    for reference in CORE_REFERENCES:
        assert reference in text, f"pack does not reference {reference}"
