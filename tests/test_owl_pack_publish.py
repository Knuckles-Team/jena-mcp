"""Idempotency/conflict unit tests for the CA-45 OWL-pack publish/verify/
partition tools (jena_publish_owl_pack / jena_verify_pack_count /
jena_partition_graph). All exercised against a fake client — no live Fuseki
writes required (mocked/unit-level proof per CA-45's scope)."""

from __future__ import annotations

from typing import Any

import pytest

from jena_mcp.mcp.mcp_jena import (
    PACK_DIGEST_PREDICATE,
    PackDigestConflictError,
    _partition_graph_apply,
    _partition_graph_list,
    _publish_owl_pack,
    _verify_pack_count,
    _with_digest_triple,
)


def _bindings_result(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"results": {"bindings": rows}}


def _digest_binding(digest: str) -> dict[str, Any]:
    return _bindings_result([{"digest": {"type": "literal", "value": digest}}])


class _FakeJenaClient:
    """A minimal stand-in for JenaApi: an in-memory map of graph -> triples,
    tracked as (subject, predicate, object) tuples, addressable by the same
    query()/update()/put_graph() surface the real client exposes."""

    def __init__(self) -> None:
        self.graphs: dict[str, list[tuple[str, str, str]]] = {}
        self.put_graph_calls: list[tuple[str, str, str, str]] = []
        self.update_calls: list[tuple[str, str]] = []

    def query(self, dataset: str, sparql: str, accept: str = "") -> dict[str, Any]:
        del dataset, accept
        if "GROUP BY ?g" in sparql:
            rows = []
            for graph_iri, triples in self.graphs.items():
                if graph_iri.startswith("urn:source:"):
                    rows.append(
                        {
                            "g": {"type": "uri", "value": graph_iri},
                            "n": {"type": "literal", "value": str(len(triples))},
                        }
                    )
            return _bindings_result(rows)
        if "?digest" in sparql:
            # Extract the graph IRI the digest lookup targets.
            start = sparql.index("GRAPH <") + len("GRAPH <")
            end = sparql.index(">", start)
            graph_iri = sparql[start:end]
            for s, p, o in self.graphs.get(graph_iri, []):
                if s == graph_iri and p == PACK_DIGEST_PREDICATE:
                    return _digest_binding(o)
            return _bindings_result([])
        if "COUNT(*)" in sparql:
            start = sparql.index("FROM <") + len("FROM <")
            end = sparql.index(">", start)
            graph_iri = sparql[start:end]
            count = len(self.graphs.get(graph_iri, []))
            return _bindings_result(
                [{"n": {"type": "literal", "value": str(count)}}]
            )
        raise AssertionError(f"unexpected query: {sparql!r}")

    def update(self, dataset: str, sparql: str) -> Any:
        self.update_calls.append((dataset, sparql))
        return {"status": "success"}

    def put_graph(
        self, dataset: str, rdf_data: str, graph: str | None, content_type: str
    ) -> Any:
        self.put_graph_calls.append((dataset, rdf_data, graph or "", content_type))
        triples: list[tuple[str, str, str]] = []
        for line in rdf_data.splitlines():
            line = line.strip()
            if not line or not line.startswith("<"):
                continue
            body = line.rstrip(" .")
            s, p, o = body.split(" ", 2)
            s = s.strip("<>")
            p = p.strip("<>")
            o = o.strip().strip('"')
            triples.append((s, p, o))
        self.graphs[graph] = triples
        return {"status": "success"}


# --------------------------------------------------------------------------
# jena_publish_owl_pack — idempotency / conflict
# --------------------------------------------------------------------------


def test_publish_fresh_iri_creates_graph_with_digest_triple() -> None:
    client = _FakeJenaClient()

    result = _publish_owl_pack(
        client,
        pack_iri="urn:ca:pack:alpha",
        ttl_data='<urn:ca:pack:alpha> <urn:ca:label> "Alpha" .',
        content_digest="sha256:aaa",
        dataset="ds",
    )

    assert result == {
        "status": "published",
        "pack_iri": "urn:ca:pack:alpha",
        "content_digest": "sha256:aaa",
        "published": True,
    }
    assert len(client.put_graph_calls) == 1
    _, rdf_data, graph, content_type = client.put_graph_calls[0]
    assert graph == "urn:ca:pack:alpha"
    assert content_type == "text/turtle"
    assert f"<urn:ca:pack:alpha> <{PACK_DIGEST_PREDICATE}> \"sha256:aaa\" ." in rdf_data


def test_publish_matching_digest_is_a_noop() -> None:
    client = _FakeJenaClient()
    _publish_owl_pack(
        client,
        pack_iri="urn:ca:pack:beta",
        ttl_data='<urn:ca:pack:beta> <urn:ca:label> "Beta" .',
        content_digest="sha256:bbb",
        dataset="ds",
    )
    assert len(client.put_graph_calls) == 1

    result = _publish_owl_pack(
        client,
        pack_iri="urn:ca:pack:beta",
        ttl_data='<urn:ca:pack:beta> <urn:ca:label> "Beta" .',
        content_digest="sha256:bbb",
        dataset="ds",
    )

    assert result["status"] == "no-op"
    assert result["published"] is False
    # No second PUT — idempotent, not a duplicate load.
    assert len(client.put_graph_calls) == 1


def test_publish_conflicting_digest_refuses_with_typed_conflict() -> None:
    client = _FakeJenaClient()
    _publish_owl_pack(
        client,
        pack_iri="urn:ca:pack:gamma",
        ttl_data='<urn:ca:pack:gamma> <urn:ca:label> "Gamma" .',
        content_digest="sha256:ccc",
        dataset="ds",
    )
    assert len(client.put_graph_calls) == 1

    with pytest.raises(PackDigestConflictError):
        _publish_owl_pack(
            client,
            pack_iri="urn:ca:pack:gamma",
            ttl_data='<urn:ca:pack:gamma> <urn:ca:label> "Gamma v2" .',
            content_digest="sha256:different",
            dataset="ds",
        )

    # The conflicting publish must never have overwritten the graph.
    assert len(client.put_graph_calls) == 1


def test_with_digest_triple_appends_a_single_reserved_triple() -> None:
    ttl = '<urn:ca:pack:delta> <urn:ca:label> "Delta" .\n'
    out = _with_digest_triple(ttl, "urn:ca:pack:delta", "sha256:ddd")
    assert ttl.strip() in out
    assert f'<urn:ca:pack:delta> <{PACK_DIGEST_PREDICATE}> "sha256:ddd" .' in out


# --------------------------------------------------------------------------
# jena_verify_pack_count
# --------------------------------------------------------------------------


def test_verify_pack_count_matches() -> None:
    client = _FakeJenaClient()
    _publish_owl_pack(
        client,
        pack_iri="urn:ca:pack:epsilon",
        ttl_data=(
            '<urn:ca:pack:epsilon> <urn:ca:label> "Epsilon" .\n'
            '<urn:ca:pack:epsilon> <urn:ca:kind> "pack" .'
        ),
        content_digest="sha256:eee",
        dataset="ds",
    )

    result = _verify_pack_count(client, "urn:ca:pack:epsilon", "ds", expected_count=3)

    # 2 real triples + 1 reserved digest triple = 3, per the literal
    # `SELECT (COUNT(*) AS ?n) FROM <pack_iri> { ?s ?p ?o }` spec.
    assert result == {"count": 3, "expected_count": 3, "matches": True}


def test_verify_pack_count_mismatch() -> None:
    client = _FakeJenaClient()
    _publish_owl_pack(
        client,
        pack_iri="urn:ca:pack:zeta",
        ttl_data='<urn:ca:pack:zeta> <urn:ca:label> "Zeta" .',
        content_digest="sha256:fff",
        dataset="ds",
    )

    result = _verify_pack_count(client, "urn:ca:pack:zeta", "ds", expected_count=99)

    assert result["matches"] is False
    assert result["expected_count"] == 99


# --------------------------------------------------------------------------
# jena_partition_graph
# --------------------------------------------------------------------------


def test_partition_graph_list_returns_urn_source_graphs() -> None:
    client = _FakeJenaClient()
    client.graphs["urn:source:leanix"] = [("s1", "p1", "o1"), ("s2", "p2", "o2")]
    client.graphs["urn:ca:pack:not-a-source"] = [("s3", "p3", "o3")]

    result = _partition_graph_list(client, "ds")

    assert result == {"graphs": [{"graph": "urn:source:leanix", "count": 2}]}


def test_partition_graph_apply_routes_to_canonical_source_graph() -> None:
    client = _FakeJenaClient()

    result = _partition_graph_apply(
        client,
        dataset="ds",
        source="leanix",
        pattern="?s ?p ?o . FILTER(?s = <urn:example:1>)",
        from_graph=None,
    )

    assert result["target_graph"] == "urn:source:leanix"
    assert len(client.update_calls) == 1
    _, sparql = client.update_calls[0]
    assert "GRAPH <urn:source:leanix>" in sparql
    assert "DELETE" in sparql and "INSERT" in sparql
