# Usage — API / CLI / MCP

`jena-mcp` exposes the same capability three ways: as **MCP tools** an agent calls,
as a **Python API** (`JenaApi`) the operator import, and as a **CLI**. The complete tool
surface is summarized in [Overview](overview.md).

## As an MCP server

Once [deployed](deployment.md), the server registers one typed tool per operation
that cover the SPARQL Protocol, the Graph Store Protocol, and Fuseki administration:

| Tool | Purpose |
|---|---|
| `jena_query` / `jena_update` | SPARQL SELECT/ASK/CONSTRUCT/DESCRIBE and INSERT/DELETE/LOAD/CLEAR |
| `jena_get_graph` / `jena_put_graph` / `jena_post_graph` / `jena_delete_graph` | Graph Store Protocol: read, replace, merge, delete |
| `jena_ping`, `jena_server_info`, `jena_stats`, `jena_metrics`, `jena_list_datasets`, `jena_dataset_info`, `jena_create_dataset`, `jena_delete_dataset`, `jena_set_dataset_state`, `jena_list_tasks`, `jena_task_info`, `jena_backup`, `jena_compact` | server administration |

Example agent prompts that map onto these tools:

- *"List the datasets on the Fuseki server"* → `jena_list_datasets`
- *"Run this SELECT query against dataset `ds`"* → `jena_query`
- *"Load this Turtle into the default graph of `ds`"* → `jena_post_graph`

## As a Python API

`JenaApi` (exported as `Api`) is a `requests`-based facade over a Fuseki endpoint,
organized by protocol.

```python
from jena_mcp.api_client import Api

api = Api(
    base_url="https://jena.example.invalid",
    username="admin",
    password="admin",
)

# SPARQL reads
results = api.query("ds", "SELECT * WHERE { ?s ?p ?o } LIMIT 10")

# Graph Store Protocol read (default graph as Turtle)
turtle = api.get_graph("ds")

# Server administration (read-only)
datasets = api.list_datasets()
info = api.server_info()
stats = api.stats("ds")
```

Build a client straight from the environment:

```python
from jena_mcp.auth import get_client
api = get_client()        # reads JENA_* from the environment / .env
```

### Writes

SPARQL updates and Graph Store writes mutate the dataset:

```python
api.update("ds", "INSERT DATA { <urn:a> <urn:knows> <urn:b> }")
api.put_graph("ds", "<urn:a> <urn:p> <urn:o> .", graph="urn:g")   # replace
api.post_graph("ds", "<urn:a> <urn:p> <urn:o2> .", graph="urn:g") # merge

# Administration writes
api.create_dataset("ds2", db_type="tdb2")
api.backup("ds")
api.compact("ds", delete_old=True)
```

## As a CLI

Run the MCP server directly with the `jena-mcp` console script (see
[Deployment](deployment.md) for transports), or invoke the package as a module:

```bash
jena-mcp --help
python -m jena_mcp
```

configuration.
