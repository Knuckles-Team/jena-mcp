from __future__ import annotations

from jena_mcp.mcp.mcp_jena import _sparql_records


def test_sparql_bindings_become_bounded_source_records() -> None:
    result = {
        "results": {
            "bindings": [
                {
                    "s": {"type": "uri", "value": "urn:fixture:resource"},
                    "label": {"type": "literal", "value": "Fixture resource"},
                },
                {"s": {"type": "uri", "value": "urn:fixture:ignored"}},
            ]
        }
    }

    records = _sparql_records(result, max_records=1)

    assert records == [
        {
            "source_key": "urn:fixture:resource",
            "title": "Fixture resource",
            "text": (
                '{"label": "Fixture resource", '
                '"s": "urn:fixture:resource"}'
            ),
            "bindings": {
                "s": "urn:fixture:resource",
                "label": "Fixture resource",
            },
        }
    ]
