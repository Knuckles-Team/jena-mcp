# Overview — jena-mcp

`jena-mcp` is the **API + MCP server + A2A agent** for an Apache Jena **Fuseki**
server. It exposes three protocols through one connector: the SPARQL Protocol, the
Graph Store Protocol (GSP), and the Fuseki administration API.

## Tool surface

The MCP server registers three action-dispatch tools:

| Tool | Tag | Actions |
|---|---|---|
| `jena_sparql` | `sparql` | `query`, `update` |
| `jena_graph` | `data` | `get`, `put`, `post`, `delete` |
| `jena_admin` | `admin` | `ping`, `server_info`, `stats`, `metrics`, `list_datasets`, `dataset_info`, `create_dataset`, `delete_dataset`, `set_dataset_state`, `list_tasks`, `task_info`, `backup`, `compact` |

Each tool dispatches to a method on the **`JenaApi`** client. All business logic
lives in the API layer; the MCP wrappers add none.

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
| SPARQL query | `POST {dataset}/sparql` | `jena_sparql` (`query`) |
| SPARQL update | `POST {dataset}/update` | `jena_sparql` (`update`) |
| Graph Store | `{dataset}/data` | `jena_graph` |
| Administration | `/$/datasets`, `/$/stats`, `/$/ping`, `/$/tasks`, … | `jena_admin` |

See [Usage](usage.md) for examples and [Deployment](deployment.md) for the
environment configuration.
