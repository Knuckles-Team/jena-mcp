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
| `jena-mcp[mcp]` | Connector-focused MCP server (`agent-utilities[mcp]` — FastMCP/FastAPI + `epistemic-graph[full]`) | You only run the **MCP server** (smallest install / image) |
| `jena-mcp[agent]` | Agent runtime (`agent-utilities[agent-runtime,logfire]` — model orchestration + `epistemic-graph[full]`) | You run the **integrated A2A agent** |
| `jena-mcp[all]` | Everything (`mcp` + `agent` + `logfire`) | Development / both surfaces |

```bash
# Connector-focused MCP server (includes the shared graph engine)
uv pip install "jena-mcp[mcp]"

# Agent runtime (adds model orchestration to the shared graph engine)
uv pip install "jena-mcp[agent]"

# Everything (development)
uv pip install "jena-mcp[all]"      # or: python -m pip install "jena-mcp[all]"
```

### Container images (`:mcp` vs `:agent`)

One multi-stage `docker/Dockerfile` builds two right-sized images, selected by `--target`:

| Image tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|
| `example/jena-mcp:mcp` | `--target mcp` | `jena-mcp[mcp]` — **connector-focused**, includes `epistemic-graph[full]`; no model-orchestration stack | `jena-mcp` |
| `example/jena-mcp@sha256:<digest>` | `--target agent` (default) | `jena-mcp[agent]` — **agent runtime**, model orchestration + `epistemic-graph[full]` | `jena-agent` |

```bash
docker build --target mcp   -t example/jena-mcp:mcp    docker/   # connector-focused MCP server
docker build --target agent -t example/jena-mcp:agent-local docker/   # agent runtime
```

`docker/mcp.compose.yml` runs the connector-focused `:mcp` server; `docker/compose.yml` runs the
agent (`immutable agent digest`) with a co-located `:mcp` sidecar.

### Knowledge-graph database (`epistemic-graph`)

Both `[mcp]` and `[agent]` carry the **epistemic-graph** engine through the required
Agent Utilities core dependency (`epistemic-graph[full]`). The `[mcp]` extra keeps
the server connector-focused; `[agent]` additionally enables model orchestration. Local
deployments can use the bundled engine. For production or shared state, run
**epistemic-graph as a dedicated database service** and configure the runtime to use it.
Deployment recipes (single-node + Raft HA), connection configuration, and architecture
diagrams are documented in the
[epistemic-graph deployment guide](https://knuckles-team.github.io/epistemic-graph/deployment/).

## Usage
Run the MCP server directly:
```bash
python -m jena_mcp
```

### MCP Configuration Examples

<!-- MCP-CONFIG-EXAMPLES:START -->

> **Install the connector-focused `[mcp]` extra.** Examples use `jena-mcp[mcp]` to add
> FastMCP / FastAPI through `agent-utilities[mcp]`; the required Agent Utilities core
> still carries `epistemic-graph[full]`. The `[agent-runtime]` extra additionally
> enables model orchestration.

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
        "MCP_TOOL_MODE": "intent",
        "APACHE_JENA_URL": "http://localhost:3030",
        "JENATOOL": "True",
        "JENA_FUSEKI_URL": "http://localhost:3030/ds",
        "JENA_PASSWORD": "admin",
        "JENA_URL": "http://localhost:3030",
        "JENA_USERNAME": "admin"
      }
    }
  }
}
```

Runtime references require an alias-aware launcher such as GraphOS. Other
launchers must omit those entries and inject the resolved values through their
own runtime secret boundary.

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
        "HOST": "127.0.0.1",
        "PORT": "8000",
        "MCP_TOOL_MODE": "intent",
        "APACHE_JENA_URL": "http://localhost:3030",
        "JENATOOL": "True",
        "JENA_FUSEKI_URL": "http://localhost:3030/ds",
        "JENA_PASSWORD": "admin",
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

Run a reviewed container image as a least-privilege stdio child (no
listener or published port):

```bash
docker run -i --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  -e TRANSPORT=stdio \
  -e MCP_TOOL_MODE=intent \
  -e APACHE_JENA_URL=http://localhost:3030 \
  -e JENATOOL=True \
  -e JENA_FUSEKI_URL=http://localhost:3030/ds \
  -e JENA_PASSWORD=admin \
  -e JENA_URL=http://localhost:3030 \
  -e JENA_USERNAME=admin \
  registry.example.invalid/jena-mcp@sha256:<digest> jena-mcp
```

For containerized network HTTP, supply an authenticated TLS ingress (or
direct server TLS), exact `MCP_ALLOWED_HOSTS`, and an exact trusted-proxy
CIDR policy through the operator-owned deployment profile. The generator
does not emit an unauthenticated non-loopback listener.

_Auto-generated from the code-read env surface (`MCP_TOOL_MODE` + package vars) — do not edit._
<!-- MCP-CONFIG-EXAMPLES:END -->

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`jena-mcp` can run as a local stdio process or container, or behind a remote
network boundary. The
[Deployment guide](https://knuckles-team.github.io/jena-mcp/deployment/) carries
the detailed transport contract.

- **Local container** — launch a reviewed immutable image as a least-privilege
  stdio child with no listener or published port.
- **Remote URL** — connect through an operator-supplied authenticated HTTPS
  ingress. Keep its URL, outbound identity references, trust profile, and exact
  `MCP_ALLOWED_HOSTS` in `AgentConfig`.
<!-- END GENERATED: additional-deployment-options -->

## Environment Variables

<!-- ENV-VARS-TABLE:START -->

#### Package environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `APACHE_JENA_URL` | `http://localhost:3030` | deployed convention; takes precedence |
| `JENA_FUSEKI_URL` | `http://localhost:3030/ds` |  |
| `JENA_URL` | `http://localhost:3030` | fallback alias for the base URL |
| `APACHE_JENA_TOKEN` | secret-injected | deployed convention; takes precedence |
| `JENA_TOKEN` | secret-injected | fallback alias for the bearer token |
| `JENA_USERNAME` | `admin` |  |
| `JENA_PASSWORD` | secret-injected |  |
| `JENA_TLS_PROFILE` | — |  |
| `JENA_TLS_PROFILE_REF` | — |  |
| `JENATOOL` | `True` |  |

#### Inherited agent-utilities variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `TRANSPORT` | `stdio` | MCP transport: `stdio` \| `streamable-http` \| `sse` |
| `HOST` | `127.0.0.1` | Loopback bind host (set an authenticated ingress explicitly) |
| `PORT` | `8000` | Bind port (HTTP transports) |
| `MCP_TOOL_MODE` | `intent` | Tool surface: `intent` \| `condensed` \| `verbose` \| `both` |
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `EUNOMIA_TYPE` | `none` | Authorization mode: `none` \| `embedded` \| `remote` |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` | Embedded Eunomia policy file |
| `EUNOMIA_REMOTE_URL` | — | Remote Eunomia authorization server URL |
| `ENABLE_OTEL` | `False` | Enable OpenTelemetry export |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OTLP collector endpoint |
| `MCP_CLIENT_AUTH` | — | Outbound MCP child auth: `oidc-client-credentials` \| `basic` \| `none` |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET_REF` | `secret://identity/oidc-client-secret` | Runtime secret reference for the OIDC service account |
| `MCP_BASIC_AUTH_USERNAME` | — | HTTP Basic username (`MCP_CLIENT_AUTH=basic`) |
| `MCP_BASIC_AUTH_PASSWORD_REF` | `secret://identity/mcp-basic-password` | Runtime secret reference for HTTP Basic auth (`MCP_CLIENT_AUTH=basic`) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | `openai` | LLM provider for the agent |
| `MODEL_ID` | `gpt-4o` | Model id for the agent |
| `ENABLE_WEB_UI` | `True` | Serve the AG-UI web interface |

_10 package + 24 inherited variable(s). Auto-generated from `.env.example` + the shared agent-utilities set — do not edit._
<!-- ENV-VARS-TABLE:END -->


Every variable the server reads, grouped by purpose.

### Connection & Credentials (Jena / Fuseki)
| Variable | Description | Default |
|----------|-------------|---------|
| `JENA_FUSEKI_URL` | Fuseki server base URL (aliases: `APACHE_JENA_URL`, `JENA_URL`) | `http://localhost:3030/ds` |
| `JENA_USERNAME` | Basic-auth user id | — |
| `JENA_PASSWORD` | Basic-auth password | — |
| `JENA_TOKEN` | Bearer token, used in place of basic auth (alias: `APACHE_JENA_TOKEN`) | — |
| `JENA_TLS_PROFILE` | Named outbound TLS policy from AgentConfig | `system` |

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


<!-- BEGIN agent-utilities-deployment (generated; do not edit between markers) -->

## Deploy with `agent-utilities-deployment`

Provision this package with the consolidated **`agent-utilities-deployment`**
workflow. It selects an installed-package, editable-source, or immutable-container
path; records only runtime secret and TLS-profile references in `AgentConfig`; and
runs doctor, registration, policy, observability, and rollback gates. Ask your agent
to **"deploy `jena-mcp` with agent-utilities-deployment"**.

| Install mode | Command |
|------|---------|
| Installed package | `uv tool install "jena-mcp[mcp]"`, then run `jena-mcp` |
| Editable source | `uv pip install -e ".[agent]"`, then run `jena-mcp` |
| Immutable container | deploy `registry.example.invalid/jena-mcp@sha256:<digest>` through the operator-selected orchestrator |

The repository embeds no deployment profile, credential value, certificate path, or
environment-specific endpoint. Supply those at runtime through `AgentConfig` and the
configured secret provider.

<!-- END agent-utilities-deployment -->

<!-- GOVERNED-CAPABILITY:START -->
## Governed capability contract

This package ships a compact canonical skill surface with specialist procedures
kept as referenced workflows. The current MCP tools, skill metadata,
`connector_manifest.yml`, ontology, mappings, shapes, fixtures, migrations,
tool-schema fingerprints, and certification metadata form one versioned
capability contract. Validate them together; do not rely on stale tool names or
historical per-task skill wrappers.

Runtime endpoints, credentials, certificate trust, tenant identity, retention,
and observability policy are deployment inputs and are never packaged values.
See [Configuration, trust, and privacy](docs/configuration.md) before enabling a
network transport, connector ingestion, GraphOS delegation, or trace export.
<!-- GOVERNED-CAPABILITY:END -->
