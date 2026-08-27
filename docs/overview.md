# Overview — jena-mcp

`jena-mcp` is the **API + MCP server + A2A agent** for an Apache Jena **Fuseki**
server. It exposes three protocols through one connector: the SPARQL Protocol, the
Graph Store Protocol (GSP), and the Fuseki administration API.

## Tool surface

The MCP server registers action-dispatch tools plus a `source`-tagged read tool and
the CA-45 OWL-pack publish/verify/partition trio:

| Tool | Tag | Actions |
|---|---|---|
| `jena_sparql` | `sparql` | `query`, `update` |
| `jena_source_records` | `sparql`, `source` | (read-only SELECT bindings for governed ingestion) |
| `jena_graph` | `data` | `get`, `put`, `post`, `delete` |
| `jena_admin` | `admin` | `ping`, `server_info`, `stats`, `metrics`, `list_datasets`, `dataset_info`, `create_dataset`, `delete_dataset`, `set_dataset_state`, `list_tasks`, `task_info`, `backup`, `compact` |
| `jena_publish_owl_pack` | `admin`, `kg` | idempotent-by-digest OWL pack publish into a named graph |
| `jena_verify_pack_count` | `admin` | `COUNT(*)` over a pack's named graph vs. a caller-supplied expected count |
| `jena_partition_graph` | `admin`, `data` | `list`, `apply` — `urn:source:<system>` named-graph routing |

Each tool dispatches to a method on the **`JenaApi`** client (the CA-45 trio adds a
small amount of digest-conflict / count-comparison logic alongside the dispatch,
documented in `jena_mcp/mcp/mcp_jena.py`). All other business logic lives in the API
layer; the MCP wrappers add none.

## Components

- **`JenaApi`** (`jena_mcp/api/api_client_jena.py`) — a `requests`-based REST facade
  over a Fuseki endpoint, organized by protocol. Exported as `Api`
  (`jena_mcp/api_client.py`).
- **MCP tools** (`jena_mcp/mcp/mcp_jena.py`) — thin FastMCP wrappers registered by
  `register_jena_tools`.
- **Agent server** (`jena_mcp/agent_server.py`) — a Pydantic-AI A2A agent
  (`jena-agent`) that runs graph-orchestrated workflows over the tool surface.
- **`get_client`** (`jena_mcp/auth.py`) — builds a `JenaApi` from `JENA_*`
  environment variables.

## Endpoints exercised

| Protocol | Path | Used by |
|---|---|---|
| SPARQL query | `POST {dataset}/sparql` | `jena_sparql` (`query`), `jena_verify_pack_count`, `jena_partition_graph` (`list`) |
| SPARQL update | `POST {dataset}/update` | `jena_sparql` (`update`), `jena_partition_graph` (`apply`) |
| Graph Store | `{dataset}/data` | `jena_graph`, `jena_publish_owl_pack` |
| Administration | `/$/datasets`, `/$/stats`, `/$/ping`, `/$/tasks`, … | `jena_admin` |

See [Usage](usage.md) for examples and [Deployment](deployment.md) for the
environment configuration.
