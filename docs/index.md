# jena-mcp

Apache Jena (Fuseki) **API + MCP Server + A2A Agent** for the agent-utilities
ecosystem — SPARQL query/update, the Graph Store Protocol, and Fuseki server
administration exposed as typed, deterministic tools.

!!! info "Official documentation"
    This site is the canonical reference for `jena-mcp`, maintained alongside every
    release.

[![PyPI](https://img.shields.io/pypi/v/jena-mcp)](https://pypi.org/project/jena-mcp/)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
[![License](https://img.shields.io/pypi/l/jena-mcp)](https://github.com/Knuckles-Team/jena-mcp/blob/main/LICENSE)
[![GitHub](https://img.shields.io/badge/source-GitHub-181717?logo=github)](https://github.com/Knuckles-Team/jena-mcp)

## Overview

`jena-mcp` wraps an Apache Jena **Fuseki** server's REST surface — the SPARQL
Protocol, the Graph Store Protocol (GSP), and the Fuseki administration API — with
typed MCP tools and an optional Pydantic-AI agent server. It provides:

- **`JenaApi`** — a tolerant `requests`-based REST facade over a Fuseki endpoint,
  organized by protocol (SPARQL, Graph Store, administration); every call degrades
  to a clear error rather than failing silently.
- **Three action-dispatch MCP tools** — `jena_sparql`, `jena_graph`, and
  `jena_admin` — covering reads, writes, and server administration.
- **An A2A agent server** (`jena-agent`) that runs graph-orchestrated workflows over
  the same tool surface.

The server **remains inactive when credentials are absent**, so it is safe to
register before a Fuseki endpoint is reachable.

## Explore the documentation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Installation](installation.md)** — pip, source, extras, and the prebuilt Docker image.
- :material-server-network: **[Deployment](deployment.md)** — run the MCP and agent servers, Docker Compose, Caddy + Technitium.
- :material-console: **[Usage](usage.md)** — the MCP tools, the `JenaApi` client, and the CLI.
- :material-database-cog: **[Backing Platform](platform.md)** — deploy Apache Jena Fuseki with Docker.
- :material-sitemap: **[Architecture](architecture.md)** — layered client, MCP surface, agent server.
- :material-tag-multiple: **[Concepts](concepts.md)** — the `CONCEPT:JENA-*` registry.

</div>

## Quick start

```bash
pip install "jena-mcp[mcp]"
jena-mcp                          # stdio MCP server (default transport)
```

Connect it to a Fuseki server:

```bash
export JENA_FUSEKI_URL=http://your-fuseki:3030
export JENA_USERNAME=admin
export JENA_PASSWORD=admin
jena-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

See **[Installation](installation.md)** and **[Deployment](deployment.md)** for the
full matrix (PyPI extras, Docker image, all transports, reverse proxy, DNS, and the
agent server).
