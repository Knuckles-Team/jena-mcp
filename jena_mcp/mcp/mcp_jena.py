"""Thin MCP wrappers around the Apache Jena Fuseki API client.

Each tool is a thin shim: it parses params, calls the corresponding
``JenaApi`` method, and returns the result. All API surface lives in
``jena_mcp.api`` — these tools add no business logic.
"""

import json
import os
from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from jena_mcp.auth import get_client


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
