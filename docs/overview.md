# Overview — jena-mcp

server. It exposes three protocols through one connector: the SPARQL Protocol, the
Graph Store Protocol (GSP), and the Fuseki administration API.

## Tool surface

The MCP server registers three action-dispatch tools:

| Tool | Tag | Actions |
|---|---|---|
| `jena_query`, `jena_update` | `sparql` | SPARQL query and update |
| `jena_get_graph`, `jena_put_graph`, `jena_post_graph`, `jena_delete_graph` | `data` | Graph Store Protocol |
| `jena_ping`, `jena_list_datasets`, `jena_create_dataset`, ... | `admin` | server administration |

Each tool dispatches to a method on the **`JenaApi`** client. All business logic
lives in the API layer; the MCP wrappers add none.

## Components

- **`JenaApi`** (`jena_mcp/api/api_client_jena.py`) — a `requests`-based REST facade
  over a Fuseki endpoint, organized by protocol. Exported as `Api`
  (`jena_mcp/api_client.py`).
- **MCP tools** (`jena_mcp/mcp/mcp_jena.py`) — thin FastMCP wrappers registered by
  `register_jena_tools`.
  (`jena-agent`) that runs graph-orchestrated workflows over the tool surface.
- **`get_client`** (`jena_mcp/auth.py`) — builds a `JenaApi` from `JENA_*`
  environment variables.

## Endpoints exercised

| Protocol | Path | Used by |
|---|---|---|
| SPARQL query | `POST {dataset}/sparql` | `jena_query` |
| SPARQL update | `POST {dataset}/update` | `jena_update` |
| Graph Store | `{dataset}/data` | `jena_get_graph`, `jena_put_graph`, `jena_post_graph`, `jena_delete_graph` |
| Administration | `/$/datasets`, `/$/stats`, `/$/ping`, `/$/tasks`, … | the `jena_*` admin tools |

See [Usage](usage.md) for examples and [Deployment](deployment.md) for the
environment configuration.
