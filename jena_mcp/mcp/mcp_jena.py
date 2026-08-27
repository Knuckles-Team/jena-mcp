"""Thin MCP wrappers around the Apache Jena Fuseki API client.

Each tool is a thin shim: it parses params, calls the corresponding
``JenaApi`` method, and returns the result. All API surface lives in
``jena_mcp.api`` — these tools add no business logic. The one deliberate
exception is the OWL-pack publish/verify/partition trio below (CA-45): the
digest-conflict and count-comparison logic is small enough, and specific
enough to this MCP surface, that it lives alongside the tool registration
rather than in the generic ``JenaApi`` client.
"""

import json
import os
from typing import Any

from agent_utilities.knowledge_graph.backends.sparql.source_partition import (
    SOURCE_GRAPH_PREFIX,
    graph_uri_for_source,
)
from fastmcp import FastMCP
from pydantic import Field

from jena_mcp.auth import get_client

# Reserved predicate used to stamp a content digest onto a published OWL-pack
# graph, tracked as a triple inside the graph itself (no external state).
PACK_DIGEST_PREDICATE = "urn:ca:digest"


class PackDigestConflictError(ValueError):
    """Raised when ``jena_publish_owl_pack`` is asked to publish a ``pack_iri``
    that already resolves to a graph carrying a *different* content digest.

    A typed conflict — never a silent overwrite of a different pack under the
    same IRI (DEC-CA-06).
    """


def _sparql_records(result: Any, *, max_records: int) -> list[dict[str, Any]]:
    """Normalize SPARQL JSON bindings into governed source records."""

    if not isinstance(result, dict):
        return []
    results = result.get("results")
    bindings = results.get("bindings") if isinstance(results, dict) else None
    if not isinstance(bindings, list):
        return []
    records: list[dict[str, Any]] = []
    for index, binding in enumerate(bindings[:max_records]):
        if not isinstance(binding, dict):
            continue
        values = {
            str(name): (
                value.get("value") if isinstance(value, dict) else value
            )
            for name, value in binding.items()
        }
        source_key = values.get("id") or values.get("s") or f"row-{index}"
        title = values.get("label") or values.get("title") or source_key
        records.append(
            {
                "source_key": str(source_key),
                "title": str(title),
                "text": json.dumps(values, sort_keys=True, default=str),
                "bindings": values,
            }
        )
    return records


def _sparql_bindings(result: Any) -> list[dict[str, Any]]:
    """Return the raw SPARQL JSON ``results.bindings`` list, or ``[]``."""
    if not isinstance(result, dict):
        return []
    results = result.get("results")
    bindings = results.get("bindings") if isinstance(results, dict) else None
    return bindings if isinstance(bindings, list) else []


def _escape_turtle_literal(value: str) -> str:
    """Escape a string for use inside a Turtle/SPARQL double-quoted literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _with_digest_triple(ttl_data: str, pack_iri: str, content_digest: str) -> str:
    """Append the reserved ``<pack_iri> <urn:ca:digest> "<digest>"`` triple to a
    Turtle payload, so the digest travels inside the published graph itself."""
    digest_triple = (
        f'\n<{pack_iri}> <{PACK_DIGEST_PREDICATE}> '
        f'"{_escape_turtle_literal(content_digest)}" .\n'
    )
    return ttl_data.rstrip("\n") + digest_triple


def _read_pack_digest(client: Any, dataset: str, pack_iri: str) -> str | None:
    """Return the stored digest for ``pack_iri``'s named graph, or ``None`` when
    the graph does not exist yet (or carries no digest triple)."""
    sparql = (
        f"SELECT ?digest WHERE {{ GRAPH <{pack_iri}> "
        f"{{ <{pack_iri}> <{PACK_DIGEST_PREDICATE}> ?digest }} }}"
    )
    result = client.query(dataset, sparql, accept="application/sparql-results+json")
    bindings = _sparql_bindings(result)
    if not bindings:
        return None
    digest_binding = bindings[0].get("digest")
    if not isinstance(digest_binding, dict):
        return None
    value = digest_binding.get("value")
    return str(value) if value is not None else None


def _publish_owl_pack(
    client: Any, pack_iri: str, ttl_data: str, content_digest: str, dataset: str
) -> dict[str, Any]:
    """Idempotent-by-digest OWL pack publish (CA-45 / DEC-CA-06).

    Publishes ``ttl_data`` into the named graph ``pack_iri`` via
    ``JenaApi.put_graph``. Never overwrites a graph already published under
    ``pack_iri`` with a *different* content digest — that raises
    :class:`PackDigestConflictError`. A republish with a *matching* digest is a
    no-op (idempotent), not a duplicate load.
    """
    existing_digest = _read_pack_digest(client, dataset, pack_iri)
    if existing_digest is not None:
        if existing_digest == content_digest:
            return {
                "status": "no-op",
                "pack_iri": pack_iri,
                "content_digest": content_digest,
                "published": False,
                "reason": "graph already published with a matching digest",
            }
        raise PackDigestConflictError(
            f"{pack_iri!r} is already published with digest {existing_digest!r}; "
            f"refusing to overwrite with a different digest {content_digest!r}. "
            "Publish under a new pack_iri, or resolve the conflict upstream."
        )
    payload = _with_digest_triple(ttl_data, pack_iri, content_digest)
    client.put_graph(dataset, payload, pack_iri, "text/turtle")
    return {
        "status": "published",
        "pack_iri": pack_iri,
        "content_digest": content_digest,
        "published": True,
    }


def _verify_pack_count(
    client: Any, pack_iri: str, dataset: str, expected_count: int
) -> dict[str, Any]:
    """Run ``SELECT (COUNT(*) AS ?n) FROM <pack_iri> { ?s ?p ?o }`` and compare
    against a caller-supplied ``expected_count`` (typically eg's own COUNT(*)
    over the same pack IRI — this tool does not call eg itself)."""
    sparql = f"SELECT (COUNT(*) AS ?n) FROM <{pack_iri}> WHERE {{ ?s ?p ?o }}"
    result = client.query(dataset, sparql, accept="application/sparql-results+json")
    bindings = _sparql_bindings(result)
    count = 0
    if bindings:
        n_binding = bindings[0].get("n")
        if isinstance(n_binding, dict) and n_binding.get("value") is not None:
            count = int(n_binding["value"])
    return {
        "count": count,
        "expected_count": expected_count,
        "matches": count == expected_count,
    }


def _partition_graph_list(client: Any, dataset: str) -> dict[str, Any]:
    """List existing ``urn:source:*`` partition graphs and their triple counts,
    per ``source_partition.py``'s canonical named-graph routing convention."""
    sparql = (
        "SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } "
        f'FILTER(STRSTARTS(STR(?g), "{SOURCE_GRAPH_PREFIX}")) }} GROUP BY ?g ORDER BY ?g'
    )
    result = client.query(dataset, sparql, accept="application/sparql-results+json")
    graphs: list[dict[str, Any]] = []
    for binding in _sparql_bindings(result):
        g = binding.get("g", {})
        n = binding.get("n", {})
        g_value = g.get("value") if isinstance(g, dict) else None
        if not g_value:
            continue
        n_value = n.get("value") if isinstance(n, dict) else None
        graphs.append({"graph": g_value, "count": int(n_value) if n_value else 0})
    return {"graphs": graphs}


def _partition_graph_apply(
    client: Any,
    dataset: str,
    source: str,
    pattern: str,
    from_graph: str | None,
) -> dict[str, Any]:
    """Move triples matching ``pattern`` from ``from_graph`` (or the default
    graph) into the canonical ``urn:source:<source>`` named graph.

    ``pattern`` is a SPARQL graph-pattern body binding ``?s ?p ?o`` (e.g.
    ``"?s ?p ?o . FILTER(?s = <urn:example:1>)"``) selecting exactly the
    triples to relocate. The DELETE/INSERT templates always move the plain
    ``?s ?p ?o`` triple — SPARQL Update forbids FILTER inside a
    modify-template, so any filter in ``pattern`` is confined to the WHERE
    clause, same as standard SPARQL Update usage.
    """
    target_graph = graph_uri_for_source(source)
    where_clause = f"GRAPH <{from_graph}> {{ {pattern} }}" if from_graph else pattern
    delete_template = f"GRAPH <{from_graph}> {{ ?s ?p ?o }}" if from_graph else "?s ?p ?o"
    sparql = (
        f"DELETE {{ {delete_template} }} "
        f"INSERT {{ GRAPH <{target_graph}> {{ ?s ?p ?o }} }} "
        f"WHERE {{ {where_clause} }}"
    )
    client.update(dataset, sparql)
    return {"source": source, "target_graph": target_graph, "from_graph": from_graph}


def register_jena_tools(mcp: FastMCP) -> None:
    """Register SPARQL, Graph Store, and admin tools for Apache Jena Fuseki."""

    @mcp.tool(tags={"sparql"})
    async def jena_sparql(
        action: str = Field(
            description=(
                "SPARQL action. One of: 'query' (SELECT/ASK/CONSTRUCT/DESCRIBE), "
                "'update' (INSERT/DELETE/LOAD/CLEAR)."
            )
        ),
        dataset: str = Field(description="Fuseki dataset name, e.g. 'ds'."),
        sparql: str = Field(description="The SPARQL query or update string."),
        accept: str = Field(
            default="application/sparql-results+json",
            description="Accept header for query results (e.g. text/turtle).",
        ),
    ) -> Any:
        """Execute a SPARQL query or update against a Fuseki dataset."""
        client = get_client()
        if action == "query":
            return client.query(dataset, sparql, accept=accept)
        if action == "update":
            return client.update(dataset, sparql)
        raise ValueError(f"Unknown action: {action!r} (use 'query' or 'update').")

    @mcp.tool(tags={"sparql", "source"})
    async def jena_source_records(
        dataset: str = Field(
            default="",
            description=(
                "Fuseki dataset name. When omitted, the environment-configured "
                "JENA_DATASET is used."
            ),
        ),
        sparql: str = Field(
            default="",
            description=(
                "Read-only SELECT query. The default returns a bounded triple sample; "
                "project ?id/?s and ?title/?label when available."
            ),
        ),
        max_records: int = Field(
            default=500,
            ge=1,
            le=10_000,
            description="Maximum normalized bindings returned to source ingestion.",
        ),
    ) -> dict[str, Any]:
        """List normalized, read-only SPARQL bindings for governed ingestion."""

        selected_dataset = dataset.strip() or os.getenv("JENA_DATASET", "").strip()
        if not selected_dataset:
            raise ValueError("a Jena dataset must be configured")
        selected_query = sparql.strip() or (
            "SELECT ?s ?p ?o WHERE { ?s ?p ?o } " f"LIMIT {max_records}"
        )
        normalized = selected_query.lstrip().upper()
        if not normalized.startswith("SELECT"):
            raise ValueError("source ingestion accepts read-only SELECT queries")
        result = get_client().query(
            selected_dataset,
            selected_query,
            accept="application/sparql-results+json",
        )
        records = _sparql_records(result, max_records=max_records)
        return {"records": records, "count": len(records)}

    @mcp.tool(tags={"data"})
    async def jena_graph(
        action: str = Field(
            description=(
                "Graph Store Protocol action. One of: 'get', 'put' (replace), "
                "'post' (merge), 'delete'."
            )
        ),
        dataset: str = Field(description="Fuseki dataset name, e.g. 'ds'."),
        graph: str = Field(
            default="default",
            description="Named graph URI, or 'default' for the default graph.",
        ),
        rdf_data: str = Field(
            default="",
            description="RDF payload (for put/post), serialized as content_type.",
        ),
        content_type: str = Field(
            default="text/turtle",
            description="RDF serialization of rdf_data (put/post).",
        ),
        accept: str = Field(
            default="text/turtle",
            description="Accept header for the returned graph (get).",
        ),
    ) -> Any:
        """Read or modify RDF graphs via the Graph Store Protocol."""
        client = get_client()
        graph_arg = None if graph in ("", "default") else graph
        if action == "get":
            return client.get_graph(dataset, graph_arg, accept=accept)
        if action == "put":
            return client.put_graph(dataset, rdf_data, graph_arg, content_type)
        if action == "post":
            return client.post_graph(dataset, rdf_data, graph_arg, content_type)
        if action == "delete":
            return client.delete_graph(dataset, graph_arg)
        raise ValueError(
            f"Unknown action: {action!r} (use get/put/post/delete)."
        )

    @mcp.tool(tags={"admin"})
    async def jena_admin(
        action: str = Field(
            description=(
                "Admin action. One of: 'ping', 'server_info', 'stats', 'metrics', "
                "'list_datasets', 'dataset_info', 'create_dataset', "
                "'delete_dataset', 'set_dataset_state', 'list_tasks', 'task_info', "
                "'backup', 'compact'."
            )
        ),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON of arguments for the action, e.g. "
                '{"name": "ds", "db_type": "tdb2"} for create_dataset, '
                '{"dataset": "ds"} for stats/backup/compact, '
                '{"name": "ds", "state": "offline"} for set_dataset_state, '
                '{"task_id": "1"} for task_info.'
            ),
        ),
    ) -> Any:
        """Administer the Fuseki server: datasets, stats, tasks, backup, compact."""
        client = get_client()
        p = json.loads(params_json) if params_json else {}
        if action == "ping":
            return client.ping()
        if action == "server_info":
            return client.server_info()
        if action == "stats":
            return client.stats(p.get("dataset"))
        if action == "metrics":
            return client.metrics()
        if action == "list_datasets":
            return client.list_datasets()
        if action == "dataset_info":
            return client.dataset_info(p["name"])
        if action == "create_dataset":
            return client.create_dataset(p["name"], p.get("db_type", "tdb2"))
        if action == "delete_dataset":
            return client.delete_dataset(p["name"])
        if action == "set_dataset_state":
            return client.set_dataset_state(p["name"], p["state"])
        if action == "list_tasks":
            return client.list_tasks()
        if action == "task_info":
            return client.task_info(p["task_id"])
        if action == "backup":
            return client.backup(p["dataset"])
        if action == "compact":
            return client.compact(p["dataset"], p.get("delete_old", False))
        raise ValueError(f"Unknown admin action: {action!r}.")

    @mcp.tool(tags={"admin", "kg"})
    async def jena_publish_owl_pack(
        pack_iri: str = Field(
            description=(
                "Named graph IRI to publish the OWL pack into. Never inferred "
                "from a filename — the caller must supply it explicitly."
            )
        ),
        ttl_data: str = Field(
            description="The compiled, SHACL-gated OWL pack, serialized as Turtle."
        ),
        content_digest: str = Field(
            description=(
                "Content digest of ttl_data (e.g. sha256 hex) used for "
                "idempotency-by-digest: a republish with a matching digest is a "
                "no-op, a mismatched digest is refused as a typed conflict."
            )
        ),
        dataset: str = Field(description="Fuseki dataset name, e.g. 'ds'."),
    ) -> dict[str, Any]:
        """Publish a SHACL-gated OWL pack into a Fuseki named graph.

        Idempotent by ``(pack_iri, content_digest)``: a fresh ``pack_iri``
        publishes; a republish with a matching digest is a no-op; a republish
        with a *different* digest raises :class:`PackDigestConflictError`
        rather than silently overwriting a different pack under the same IRI.
        Assumes the caller already ran the SHACL gate — publish-before-validate
        is the failure mode this tool must never enable (DEC-CA-06).
        """
        return _publish_owl_pack(get_client(), pack_iri, ttl_data, content_digest, dataset)

    @mcp.tool(tags={"admin"})
    async def jena_verify_pack_count(
        pack_iri: str = Field(description="Named graph IRI of the published pack."),
        dataset: str = Field(description="Fuseki dataset name, e.g. 'ds'."),
        expected_count: int = Field(
            description=(
                "Triple count to compare against (typically eg's own COUNT(*) "
                "over the same pack IRI). This tool does not call eg itself — "
                "the caller supplies both numbers for comparison."
            )
        ),
    ) -> dict[str, Any]:
        """Count the triples in a published pack's named graph and compare
        against a caller-supplied expected count. A pure read, always safe to
        retry."""
        return _verify_pack_count(get_client(), pack_iri, dataset, expected_count)

    @mcp.tool(tags={"admin", "data"})
    async def jena_partition_graph(
        action: str = Field(
            description="Partition action. One of: 'list', 'apply'."
        ),
        dataset: str = Field(description="Fuseki dataset name, e.g. 'ds'."),
        source: str = Field(
            default="",
            description=(
                "System source id (e.g. 'leanix') for 'apply' — routed to the "
                "canonical urn:source:<source> named graph via "
                "source_partition.py's make_source_id/graph_uri_for_source."
            ),
        ),
        pattern: str = Field(
            default="",
            description=(
                "SPARQL graph-pattern body selecting triples to relocate for "
                "'apply', e.g. '?s ?p ?o . FILTER(?s = <urn:example:1>)'."
            ),
        ),
        from_graph: str = Field(
            default="",
            description=(
                "Named graph to move triples FROM for 'apply'; empty targets "
                "the default graph."
            ),
        ),
    ) -> dict[str, Any]:
        """List existing ``urn:source:*`` partition graphs, or move triples
        matching a pattern into a source's canonical partition graph.

        Reuses ``backends/sparql/source_partition.py``'s existing
        ``urn:source:<system>`` named-graph routing convention (read-only
        reference; not modified here).
        """
        client = get_client()
        if action == "list":
            return _partition_graph_list(client, dataset)
        if action == "apply":
            if not source or not pattern:
                raise ValueError("'apply' requires both 'source' and 'pattern'.")
            return _partition_graph_apply(
                client, dataset, source, pattern, from_graph or None
            )
        raise ValueError(f"Unknown partition action: {action!r} (use list/apply).")
