# jena-mcp

A Model Context Protocol (MCP) server, A2A agent, and API client for Apache Jena
(Fuseki) integration.

![PyPI - Version](https://img.shields.io/pypi/v/jena-mcp)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
![PyPI - License](https://img.shields.io/pypi/l/jena-mcp)
![GitHub](https://img.shields.io/github/license/Knuckles-Team/jena-mcp)

> **Documentation** — Installation, deployment, usage across the API, CLI, and MCP
> interfaces, and guidance for provisioning the Apache Jena Fuseki platform are
> maintained in the [official documentation](https://knuckles-team.github.io/jena-mcp/).

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [MCP Tools](#mcp-tools)
- [Documentation](#documentation)

## Overview
jena-mcp exposes a standardized interface to interact with an Apache Jena Fuseki
server using the Model Context Protocol — SPARQL query/update, the Graph Store
Protocol, and Fuseki server administration — plus an optional Pydantic-AI agent
server.

## Installation

Pick the extra that matches what you want to run:

| Extra | Installs | Use when |
|-------|----------|----------|
| `jena-mcp[mcp]` | Slim MCP server only (`agent-utilities[mcp]` — FastMCP/FastAPI) | You only run the **MCP server** (smallest install / image) |
| `jena-mcp[agent]` | Full agent runtime (`agent-utilities[agent,logfire]` — Pydantic AI + the epistemic-graph engine) | You run the **integrated A2A agent** |
| `jena-mcp[all]` | Everything (`mcp` + `agent` + `logfire`) | Development / both surfaces |

```bash
# MCP server only (recommended for tool hosting — slim deps)
uv pip install "jena-mcp[mcp]"

# Full agent runtime (Pydantic AI + epistemic-graph engine)
uv pip install "jena-mcp[agent]"

# Everything (development)
uv pip install "jena-mcp[all]"      # or: python -m pip install "jena-mcp[all]"
```

### Container images (`:mcp` vs `:agent`)

One multi-stage `docker/Dockerfile` builds two right-sized images, selected by `--target`:

| Image tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|
| `knucklessg1/jena-mcp:mcp` | `--target mcp` | `jena-mcp[mcp]` — **slim**, no engine/`pydantic-ai`/`dspy`/`llama-index`/`tree-sitter` | `jena-mcp` |
| `knucklessg1/jena-mcp:latest` | `--target agent` (default) | `jena-mcp[agent]` — **full** agent runtime + epistemic-graph engine | `jena-agent` |

```bash
docker build --target mcp   -t knucklessg1/jena-mcp:mcp    docker/   # slim MCP server
docker build --target agent -t knucklessg1/jena-mcp:latest docker/   # full agent
```

`docker/mcp.compose.yml` runs the slim `:mcp` server; `docker/compose.yml` runs the
agent (`:latest`) with a co-located `:mcp` sidecar.

### Knowledge-graph database (`epistemic-graph`)

The **full agent** (`[agent]` / `:latest`) embeds the **epistemic-graph** engine (pulled in
transitively via `agent-utilities[agent]`). For production — or to share one knowledge graph
across multiple agents — run **epistemic-graph as its own database container** and point the
agent at it instead of embedding it. Deployment recipes (single-node + Raft HA), connection
config, and the full database architecture (with diagrams) are documented in the
[epistemic-graph deployment guide](https://knuckles-team.github.io/epistemic-graph/deployment/).
The slim `[mcp]` server does **not** require the database.

## Usage
Run the MCP server directly:
```bash
python -m jena_mcp
```

### MCP Configuration Examples

<!-- MCP-CONFIG-EXAMPLES:START -->

> **Install the slim `[mcp]` extra.** All examples install `jena-mcp[mcp]` — the
> MCP-server extra that pulls only the FastMCP / FastAPI tooling (`agent-utilities[mcp]`).
> It deliberately **excludes** the heavy agent runtime (`pydantic-ai`, the epistemic-graph
> engine, `dspy`, `llama-index`), so `uvx` / container installs are far smaller. Use the
> full `[agent]` extra only when you need the integrated Pydantic AI agent.

#### stdio Transport (local IDEs — Cursor, Claude Desktop, VS Code)

```json
{
  "mcpServers": {
    "jena-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "jena-mcp[mcp]",
        "jena-mcp"
      ],
      "env": {
        "MCP_TOOL_MODE": "condensed",
        "APACHE_JENA_TOKEN": "",
        "APACHE_JENA_URL": "http://localhost:3030",
        "JENATOOL": "True",
        "JENA_FUSEKI_URL": "http://localhost:3030/ds",
        "JENA_PASSWORD": "admin",
        "JENA_TOKEN": "",
        "JENA_URL": "http://localhost:3030",
        "JENA_USERNAME": "admin"
      }
    }
  }
}
```

#### Streamable-HTTP Transport (networked / production)

```json
{
  "mcpServers": {
    "jena-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "jena-mcp[mcp]",
        "jena-mcp",
        "--transport",
        "streamable-http",
        "--port",
        "8000"
      ],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "0.0.0.0",
        "PORT": "8000",
        "MCP_TOOL_MODE": "condensed",
        "APACHE_JENA_TOKEN": "",
        "APACHE_JENA_URL": "http://localhost:3030",
        "JENATOOL": "True",
        "JENA_FUSEKI_URL": "http://localhost:3030/ds",
        "JENA_PASSWORD": "admin",
        "JENA_TOKEN": "",
        "JENA_URL": "http://localhost:3030",
        "JENA_USERNAME": "admin"
      }
    }
  }
}
```

Alternatively, connect to a pre-deployed Streamable-HTTP instance by `url`:

```json
{
  "mcpServers": {
    "jena-mcp": {
      "url": "http://localhost:8000/jena-mcp/mcp"
    }
  }
}
```

Deploying the Streamable-HTTP server via Docker:

```bash
docker run -d \
  --name jena-mcp-mcp \
  -p 8000:8000 \
  -e TRANSPORT=streamable-http \
  -e HOST=0.0.0.0 \
  -e PORT=8000 \
  -e MCP_TOOL_MODE=condensed \
  -e APACHE_JENA_TOKEN="" \
  -e APACHE_JENA_URL=http://localhost:3030 \
  -e JENATOOL=True \
  -e JENA_FUSEKI_URL=http://localhost:3030/ds \
  -e JENA_PASSWORD=admin \
  -e JENA_TOKEN="" \
  -e JENA_URL=http://localhost:3030 \
  -e JENA_USERNAME=admin \
  knucklessg1/jena-mcp:mcp
```

_Auto-generated from the code-read env surface (`MCP_TOOL_MODE` + package vars) — do not edit._
<!-- MCP-CONFIG-EXAMPLES:END -->

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`jena-mcp` can also run as a **local container** (Docker / Podman / `uv`) or be
consumed from a **remote deployment**. The
[Deployment guide](https://knuckles-team.github.io/jena-mcp/deployment/) has full, copy-paste
`mcp_config.json` for all four transports — **stdio**, **streamable-http**,
**local container / uv**, and **remote URL**:

- **Local container / uv** — launch the server from `mcp_config.json` via `uvx`,
  `docker run`, or `podman run`, or point at a local streamable-http container by `url`.
- **Remote URL** — connect to a server deployed behind Caddy at
  `http://jena-mcp.arpa/mcp` using the `"url"` key.
<!-- END GENERATED: additional-deployment-options -->

## Environment Variables

<!-- ENV-VARS-TABLE:START -->

#### Package environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `APACHE_JENA_URL` | `http://localhost:3030` | deployed convention; takes precedence |
| `JENA_FUSEKI_URL` | `http://localhost:3030/ds` |  |
| `JENA_URL` | `http://localhost:3030` | fallback alias for the base URL |
| `APACHE_JENA_TOKEN` | — | deployed convention; takes precedence |
| `JENA_TOKEN` | — | fallback alias for the bearer token |
| `JENA_USERNAME` | `admin` |  |
| `JENA_PASSWORD` | `admin` |  |
| `JENA_SSL_VERIFY` | `True` |  |
| `JENATOOL` | `True` |  |

#### Inherited agent-utilities variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `TRANSPORT` | `stdio` | MCP transport: `stdio` | `streamable-http` | `sse` |
| `HOST` | `0.0.0.0` | Bind host (HTTP transports) |
| `PORT` | `8000` | Bind port (HTTP transports) |
| `MCP_TOOL_MODE` | `condensed` | Tool surface: `condensed` | `verbose` | `both` |
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `EUNOMIA_TYPE` | `none` | Authorization mode: `none` | `embedded` | `remote` |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` | Embedded Eunomia policy file |
| `EUNOMIA_REMOTE_URL` | — | Remote Eunomia authorization server URL |
| `ENABLE_OTEL` | `False` | Enable OpenTelemetry export |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OTLP collector endpoint |
| `MCP_CLIENT_AUTH` | — | Outbound MCP auth (`oidc-client-credentials` for fleet calls) |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET` | — | OIDC client secret (service-account auth) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | `openai` | LLM provider for the agent |
| `MODEL_ID` | `gpt-4o` | Model id for the agent |
| `ENABLE_WEB_UI` | `True` | Serve the AG-UI web interface |

_9 package + 22 inherited variable(s). Auto-generated from `.env.example` + the shared agent-utilities set — do not edit._
<!-- ENV-VARS-TABLE:END -->


Every variable the server reads, grouped by purpose.

### Connection & Credentials (Jena / Fuseki)
| Variable | Description | Default |
|----------|-------------|---------|
| `JENA_FUSEKI_URL` | Fuseki server base URL (aliases: `APACHE_JENA_URL`, `JENA_URL`) | `http://localhost:3030/ds` |
| `JENA_USERNAME` | Basic-auth user id | — |
| `JENA_PASSWORD` | Basic-auth password | — |
| `JENA_TOKEN` | Bearer token, used in place of basic auth (alias: `APACHE_JENA_TOKEN`) | — |
| `JENA_SSL_VERIFY` | Verify TLS (set `False` for self-signed homelab) | `True` |

### MCP server / transport
| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSPORT` | `stdio`, `streamable-http`, or `sse` | `stdio` |
| `HOST` | Bind host (HTTP transports) | `0.0.0.0` |
| `PORT` | Bind port (HTTP transports) | `8000` |
| `MCP_TOOL_MODE` | Tool surface: `condensed`, `verbose`, or `both` | `condensed` |

### Telemetry & governance
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_OTEL` | Enable OpenTelemetry export | `True` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | — |
| `EUNOMIA_TYPE` | Authorization mode: `none`, `embedded`, `remote` | `none` |
| `EUNOMIA_POLICY_FILE` | Embedded policy file | `mcp_policies.json` |
| `EUNOMIA_REMOTE_URL` | Remote Eunomia server URL | — |

### Tool toggles
| Variable | Description | Default |
|----------|-------------|---------|
| `JENATOOL` | Register the Jena tool set (set `false` to disable) | `True` |

## MCP Tools
Auto-generated — do not edit between the markers below.
<!-- MCP-TOOLS-TABLE:START -->

#### Condensed action-routed tools (default — `MCP_TOOL_MODE=condensed`)

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `jena_admin` | `JENATOOL` | Administer the Fuseki server: datasets, stats, tasks, backup, compact. |
| `jena_graph` | `JENATOOL` | Read or modify RDF graphs via the Graph Store Protocol. |
| `jena_sparql` | `JENATOOL` | Execute a SPARQL query or update against a Fuseki dataset. |

#### Verbose 1:1 API-mapped tools (`MCP_TOOL_MODE=verbose` or `both`)

<details>
<summary>19 per-operation tools — one per public API method (click to expand)</summary>

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `jena_backup` | `JENA_APITOOL` | Trigger an async backup of a dataset; returns a task handle. |
| `jena_compact` | `JENA_APITOOL` | Trigger an async TDB2 compaction; returns a task handle. |
| `jena_create_dataset` | `JENA_APITOOL` | Create a dataset. ``db_type`` is one of ``tdb2``, ``tdb``, ``mem``. |
| `jena_dataset_info` | `JENA_APITOOL` | Detail for a single dataset. |
| `jena_delete_dataset` | `JENA_APITOOL` | Remove a dataset (and its configuration). |
| `jena_delete_graph` | `JENA_APITOOL` | Drop a graph (named or default). |
| `jena_get_graph` | `JENA_APITOOL` | Fetch an RDF graph (named or default) as text. |
| `jena_list_datasets` | `JENA_APITOOL` | List datasets and their state. |
| `jena_list_tasks` | `JENA_APITOOL` | List async admin tasks (backup/compact). |
| `jena_metrics` | `JENA_APITOOL` | Prometheus metrics exposition. |
| `jena_ping` | `JENA_APITOOL` | Server liveness check. |
| `jena_post_graph` | `JENA_APITOOL` | Merge the supplied RDF into a graph. |
| `jena_put_graph` | `JENA_APITOOL` | Replace a graph with the supplied RDF. |
| `jena_query` | `JENA_APITOOL` | Run a SPARQL read query (SELECT/ASK/CONSTRUCT/DESCRIBE). |
| `jena_server_info` | `JENA_APITOOL` | Server build info and the list of mounted datasets/services. |
| `jena_set_dataset_state` | `JENA_APITOOL` | Set a dataset ``active`` (online) or ``offline``. |
| `jena_stats` | `JENA_APITOOL` | Server-wide or per-dataset request statistics. |
| `jena_task_info` | `JENA_APITOOL` | Detail for a single async task. |
| `jena_update` | `JENA_APITOOL` | Run a SPARQL update (INSERT/DELETE/LOAD/CLEAR). |

</details>

_3 action-routed tool(s) (default) · 19 verbose 1:1 tool(s). Each is enabled unless its `<DOMAIN>TOOL` toggle is set false; `MCP_TOOL_MODE` selects the surface (`condensed` default · `verbose` 1:1 · `both`). Auto-generated — do not edit._
<!-- MCP-TOOLS-TABLE:END -->

## Documentation

The complete documentation is published as the
[official documentation site](https://knuckles-team.github.io/jena-mcp/) and is the
recommended reference for installation, deployment, and day-to-day operation.

| Page | Contents |
|---|---|
| [Installation](https://knuckles-team.github.io/jena-mcp/installation/) | pip, source, extras, prebuilt Docker image |
| [Deployment](https://knuckles-team.github.io/jena-mcp/deployment/) | run the MCP and agent servers, Compose, Caddy + Technitium, env config |
| [Usage](https://knuckles-team.github.io/jena-mcp/usage/) | the MCP tools, the `JenaApi` client, the CLI |
| [Backing Platform](https://knuckles-team.github.io/jena-mcp/platform/) | deploy Apache Jena Fuseki with Docker |
| [Overview](https://knuckles-team.github.io/jena-mcp/overview/) | tool surface, endpoints, components |
| [Architecture](https://knuckles-team.github.io/jena-mcp/architecture/) | layered client, MCP surface, agent server |
| [Concepts](https://knuckles-team.github.io/jena-mcp/concepts/) | concept registry (`CONCEPT:JENA-*`) |

`AGENTS.md` is the canonical contributor/agent guidance.


<!-- BEGIN agent-os-genesis-deploy (generated; do not edit between markers) -->

## Deploy with `agent-os-genesis`

This package can be provisioned for you — skill-guided — by the **`agent-os-genesis`**
universal skill (its *single-package deploy mode*): it picks your install method, seeds
secrets to OpenBao/Vault (or `.env`), trusts your enterprise CA, registers the MCP
server, and verifies it — the same machinery that stands up the whole Agent OS, narrowed
to just this package. Ask your agent to **"deploy `jena-mcp` with agent-os-genesis"**.

| Install mode | Command |
|------|---------|
| Bare-metal, prod (PyPI) | `uvx jena-mcp` · or `uv tool install jena-mcp` |
| Bare-metal, dev (editable) | `uv pip install -e ".[all]"` · or `pip install -e ".[all]"` |
| Container, prod | deploy `knucklessg1/jena-mcp:latest` via docker-compose / swarm / podman / podman-compose / kubernetes |
| Container, dev (editable) | deploy `docker/compose.dev.yml` (source-mounted at `/src`; edits live on restart) |

Secrets are read-existing + seeded via `vault_sync` — you are only prompted for what's missing.

<!-- END agent-os-genesis-deploy -->
