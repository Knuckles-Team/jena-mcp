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

> **Install the slim `[mcp]` extra.** The examples below install `jena-mcp[mcp]` —
> the MCP-server extra that pulls only the FastMCP / FastAPI tooling
> (`agent-utilities[mcp]`). It deliberately **excludes** the heavy agent runtime
> (the epistemic-graph engine, `pydantic-ai`, `dspy`, `llama-index`, `tree-sitter`),
> so `uvx`/container installs are dramatically smaller and faster. Use the full
> `[agent]` extra only when you need the integrated A2A agent (see [Installation](#installation)).

#### stdio Transport (local IDEs — Cursor, Claude Desktop)

```json
{
  "mcpServers": {
    "jena-mcp": {
      "command": "uvx",
      "args": ["--from", "jena-mcp[mcp]", "jena-mcp"],
      "env": {
        "JENA_FUSEKI_URL": "http://localhost:3030/ds",
        "JENA_USERNAME": "admin",
        "JENA_PASSWORD": "your_password"
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
      "args": ["--from", "jena-mcp[mcp]", "jena-mcp", "--transport", "streamable-http", "--port", "8000"],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "0.0.0.0",
        "PORT": "8000",
        "JENA_FUSEKI_URL": "http://localhost:3030/ds",
        "JENA_USERNAME": "admin",
        "JENA_PASSWORD": "your_password"
      }
    }
  }
}
```

## Architecture
See `/docs` for architectural diagrams and further documentation.

## Deployment
### Bare-metal
```bash
python -m jena_mcp.agent_server
```

### Docker
```bash
docker compose -f docker/compose.yml up -d       # full agent (:latest) + :mcp sidecar
docker compose -f docker/mcp.compose.yml up -d   # slim MCP server only (:mcp)
```

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

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `jena_admin` | `JENATOOL` | Administer the Fuseki server: datasets, stats, tasks, backup, compact. |
| `jena_graph` | `JENATOOL` | Read or modify RDF graphs via the Graph Store Protocol. |
| `jena_sparql` | `JENATOOL` | Execute a SPARQL query or update against a Fuseki dataset. |

_3 action-routed tools (default `MCP_TOOL_MODE=condensed`). Each is enabled unless its toggle is set false; set `MCP_TOOL_MODE=verbose` (or `both`) for the 1:1 per-operation surface. Auto-generated — do not edit._
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
