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
```bash
pip install -e .
```

## Usage
Run the MCP server directly:
```bash
python -m jena_mcp
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
docker compose -f docker/agent.compose.yml up -d
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
| Variable | Description |
|----------|-------------|
| `JENA_FUSEKI_URL` | Fuseki server base URL (alias: `JENA_URL`) |
| `JENA_USERNAME` | Basic-auth user id |
| `JENA_PASSWORD` | Basic-auth password |
| `JENA_TOKEN` | Bearer token (used in place of basic auth) |
| `JENA_SSL_VERIFY` | Verify TLS (set `False` for self-signed homelab) |
| `JENATOOL` | Register the Jena tool set |

## MCP Tools
| Tool | Description |
|------|-------------|
| `jena_sparql` | Run a SPARQL query or update against a Fuseki dataset |
| `jena_graph` | Read or modify RDF graphs via the Graph Store Protocol |
| `jena_admin` | Administer the Fuseki server: datasets, stats, tasks, backup, compact |

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
