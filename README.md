# jena-mcp

A Model Context Protocol (MCP) server for Jena integration.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [MCP Tools](#mcp-tools)

## Overview
jena-mcp exposes a standardized interface to interact with Jena using the Model Context Protocol.

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

## Environment Variables
| Variable | Description |
|----------|-------------|
| `JENA_FUSEKI_URL` | Fuseki server URL |
| `JENA_USER` | Admin user |
| `JENA_PASSWORD` | Admin password |

## MCP Tools
| Tool | Description |
|------|-------------|
| `get_jena_info` | Retrieve basic information from Jena |
| `query_jena` | Run a query against the Jena instance |
