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
            str(name): (value.get("value") if isinstance(value, dict) else value)
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
    """Register the source-records tool; every client operation is its own tool."""

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
            f"SELECT ?s ?p ?o WHERE {{ ?s ?p ?o }} LIMIT {max_records}"
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
