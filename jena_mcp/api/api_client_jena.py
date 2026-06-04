"""Apache Jena Fuseki API wrapper.

Covers the three HTTP surfaces Fuseki exposes:

* **SPARQL Protocol** — query (SELECT/ASK/CONSTRUCT/DESCRIBE) and update
  (INSERT/DELETE) per dataset.
* **Graph Store Protocol (GSP)** — read/replace/merge/drop RDF graphs.
* **Admin API** (``/$/``) — ping, server info, statistics, dataset
  lifecycle (create/list/delete/state), async tasks, backup, compact, metrics.
"""

from typing import Any

from jena_mcp.api.api_client_base import ApiClientBase


class JenaApi(ApiClientBase):
    """Full client for an Apache Jena Fuseki server."""

    # ------------------------------------------------------------------ #
    # SPARQL Protocol
    # ------------------------------------------------------------------ #
    def query(
        self,
        dataset: str,
        sparql: str,
        accept: str = "application/sparql-results+json",
    ) -> Any:
        """Run a SPARQL read query (SELECT/ASK/CONSTRUCT/DESCRIBE)."""
        return self.request(
            "POST",
            f"{dataset.strip('/')}/sparql",
            data=sparql,
            content_type="application/sparql-query",
            accept=accept,
        )

    def update(self, dataset: str, sparql: str) -> Any:
        """Run a SPARQL update (INSERT/DELETE/LOAD/CLEAR)."""
        return self.request(
            "POST",
            f"{dataset.strip('/')}/update",
            data=sparql,
            content_type="application/sparql-update",
        )

    # ------------------------------------------------------------------ #
    # Graph Store Protocol (GSP)
    # ------------------------------------------------------------------ #
    def _gsp_params(self, graph: str | None) -> dict[str, str]:
        return {"graph": graph} if graph and graph != "default" else {"default": ""}

    def get_graph(
        self, dataset: str, graph: str | None = None, accept: str = "text/turtle"
    ) -> Any:
        """Fetch an RDF graph (named or default) as text."""
        return self.request(
            "GET",
            f"{dataset.strip('/')}/data",
            params=self._gsp_params(graph),
            accept=accept,
        )

    def put_graph(
        self,
        dataset: str,
        rdf_data: str,
        graph: str | None = None,
        content_type: str = "text/turtle",
    ) -> Any:
        """Replace a graph with the supplied RDF."""
        return self.request(
            "PUT",
            f"{dataset.strip('/')}/data",
            params=self._gsp_params(graph),
            data=rdf_data,
            content_type=content_type,
        )

    def post_graph(
        self,
        dataset: str,
        rdf_data: str,
        graph: str | None = None,
        content_type: str = "text/turtle",
    ) -> Any:
        """Merge the supplied RDF into a graph."""
        return self.request(
            "POST",
            f"{dataset.strip('/')}/data",
            params=self._gsp_params(graph),
            data=rdf_data,
            content_type=content_type,
        )

    def delete_graph(self, dataset: str, graph: str | None = None) -> Any:
        """Drop a graph (named or default)."""
        return self.request(
            "DELETE",
            f"{dataset.strip('/')}/data",
            params=self._gsp_params(graph),
        )

    # ------------------------------------------------------------------ #
    # Admin API (/$/)
    # ------------------------------------------------------------------ #
    def ping(self) -> Any:
        """Server liveness check."""
        return self.request("GET", "$/ping", accept="text/plain")

    def server_info(self) -> Any:
        """Server build info and the list of mounted datasets/services."""
        return self.request("GET", "$/server", accept="application/json")

    def stats(self, dataset: str | None = None) -> Any:
        """Server-wide or per-dataset request statistics."""
        endpoint = "$/stats" + (f"/{dataset.strip('/')}" if dataset else "")
        return self.request("GET", endpoint, accept="application/json")

    def metrics(self) -> Any:
        """Prometheus metrics exposition."""
        return self.request("GET", "$/metrics", accept="text/plain")

    def list_datasets(self) -> Any:
        """List datasets and their state."""
        return self.request("GET", "$/datasets", accept="application/json")

    def dataset_info(self, name: str) -> Any:
        """Detail for a single dataset."""
        return self.request(
            "GET", f"$/datasets/{name.strip('/')}", accept="application/json"
        )

    def create_dataset(self, name: str, db_type: str = "tdb2") -> Any:
        """Create a dataset. ``db_type`` is one of ``tdb2``, ``tdb``, ``mem``."""
        return self.request(
            "POST",
            "$/datasets",
            params={"dbName": name, "dbType": db_type},
            content_type="application/x-www-form-urlencoded",
        )

    def delete_dataset(self, name: str) -> Any:
        """Remove a dataset (and its configuration)."""
        return self.request("DELETE", f"$/datasets/{name.strip('/')}")

    def set_dataset_state(self, name: str, state: str) -> Any:
        """Set a dataset ``active`` (online) or ``offline``."""
        return self.request(
            "POST",
            f"$/datasets/{name.strip('/')}",
            params={"state": state},
            content_type="application/x-www-form-urlencoded",
        )

    def list_tasks(self) -> Any:
        """List async admin tasks (backup/compact)."""
        return self.request("GET", "$/tasks", accept="application/json")

    def task_info(self, task_id: str) -> Any:
        """Detail for a single async task."""
        return self.request("GET", f"$/tasks/{task_id}", accept="application/json")

    def backup(self, dataset: str) -> Any:
        """Trigger an async backup of a dataset; returns a task handle."""
        return self.request("POST", f"$/backup/{dataset.strip('/')}")

    def compact(self, dataset: str, delete_old: bool = False) -> Any:
        """Trigger an async TDB2 compaction; returns a task handle."""
        params = {"deleteOld": "true"} if delete_old else None
        return self.request("POST", f"$/compact/{dataset.strip('/')}", params=params)
