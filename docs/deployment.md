# Deployment

This page covers running `jena-mcp` as a long-lived server: the transports, a Docker
Compose stack, putting it behind a Caddy reverse proxy, and giving it a DNS name with
Technitium. To provision the **Apache Jena Fuseki** server it connects to, see
[Backing Platform](platform.md).

> `jena-mcp` ships **both** an MCP server (console script `jena-mcp`) and an A2A
> agent server (console script `jena-agent`). The MCP server is the typed,
> deterministic tool surface a policy router / agent calls; the agent server runs
> graph-orchestrated workflows over that same surface. The agent server is
> documented in [Agent server](#agent-server) below.

## Run the MCP server

The transport is selected with `--transport` (or the `TRANSPORT` env var):

=== "stdio (default)"

    ```bash
    jena-mcp
    ```
    For IDE / desktop MCP clients that launch the server as a subprocess.

=== "streamable-http"

    ```bash
    jena-mcp --transport streamable-http --host 0.0.0.0 --port 8000
    ```
    A network server with a `/health` endpoint and `/mcp` route.

=== "sse"

    ```bash
    jena-mcp --transport sse --host 0.0.0.0 --port 8000
    ```

Health check (HTTP transports):

```bash
curl -s http://localhost:8000/health        # {"status":"OK"}
```

## Configuration (environment) {#configuration-environment}

`jena-mcp` is configured entirely from the environment. The **required** set:

| Var | Default | Meaning |
|---|---|---|
| `JENA_FUSEKI_URL` | `http://localhost:3030` | Fuseki server base URL (alias: `JENA_URL`) |
| `JENA_USERNAME` | _(unset)_ | Basic-auth user id |
| `JENA_PASSWORD` | _(unset)_ | Basic-auth password |
| `JENA_TOKEN` | _(unset)_ | Bearer token (used in place of basic auth) |
| `JENA_SSL_VERIFY` | `True` | Verify TLS (set `False` for self-signed homelab) |
| `JENATOOL` | `True` | Register the Jena tool set |

Plus `HOST` / `PORT` / `TRANSPORT` for HTTP transports. A starting template is
provided in
[`.env.example`](https://github.com/Knuckles-Team/jena-mcp/blob/main/.env.example) —
copy it to `.env` and fill in your connection settings.

## Docker Compose

The repo ships
[`docker/mcp.compose.yml`](https://github.com/Knuckles-Team/jena-mcp/blob/main/docker/mcp.compose.yml).
The following stack reads a sibling `.env` and publishes the HTTP server on `:8000`:

```yaml
services:
  jena-mcp:
    image: knucklessg1/jena-mcp:latest
    container_name: jena-mcp
    hostname: jena-mcp
    restart: always
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - PORT=8000
      - TRANSPORT=streamable-http
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
cp .env.example .env          # then edit JENA_* values
docker compose -f docker/mcp.compose.yml up -d
docker compose -f docker/mcp.compose.yml logs -f
```

## Behind a Caddy reverse proxy

Expose the HTTP server on a hostname with automatic TLS. Add to your `Caddyfile`:

```caddy
# Internal (self-signed) — homelab .arpa zone
jena-mcp.arpa {
    tls internal
    reverse_proxy jena-mcp:8000
}
```

```caddy
# Public — automatic Let's Encrypt
jena-mcp.example.com {
    reverse_proxy jena-mcp:8000
}
```

Reload Caddy:

```bash
docker compose -f services/caddy/compose.yml exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## DNS with Technitium

Point the hostname at the host running Caddy. Via the Technitium API:

```bash
curl -s "http://technitium.arpa:5380/api/zones/records/add" \
  --data-urlencode "token=$TECHNITIUM_DNS_TOKEN" \
  --data-urlencode "domain=jena-mcp.arpa" \
  --data-urlencode "zone=arpa" \
  --data-urlencode "type=A" \
  --data-urlencode "ipAddress=10.0.0.10" \
  --data-urlencode "ttl=3600"
```

…or add an **A record** `jena-mcp.arpa → <caddy-host-ip>` in the Technitium web
console (`http://technitium.arpa:5380`). The ecosystem
[`technitium-dns-mcp`](https://knuckles-team.github.io/technitium-dns-mcp/) automates
this as a tool.

## Register with an MCP client

Add to your client's `mcp_config.json`:

```json
{
  "mcpServers": {
    "jena-mcp": {
      "command": "uv",
      "args": ["run", "jena-mcp"],
      "env": {
        "JENA_FUSEKI_URL": "http://your-fuseki:3030",
        "JENA_USERNAME": "admin",
        "JENA_PASSWORD": "admin",
        "JENA_SSL_VERIFY": "False",
        "JENATOOL": "True"
      }
    }
  }
}
```

For a remote HTTP server, point the client at `http://jena-mcp.arpa/mcp` instead.

## Agent server

`jena-mcp` also ships a Pydantic-AI **A2A agent server** (console script
`jena-agent`) that runs graph-orchestrated workflows over the MCP tool surface. The
agent connects to a running MCP server via `--mcp-url` (or a bundled
`mcp_config.json`) and exposes its own HTTP endpoint.

```bash
# Point the agent at a running MCP server and serve it on :8001
jena-agent --mcp-url http://jena-mcp:8000/mcp --host 0.0.0.0 --port 8001
```

The repo ships
[`docker/agent.compose.yml`](https://github.com/Knuckles-Team/jena-mcp/blob/main/docker/agent.compose.yml)
to run the agent alongside the MCP server:

```yaml
services:
  jena-agent:
    image: knucklessg1/jena-mcp:latest
    container_name: jena-agent
    hostname: jena-agent
    restart: always
    command: ["jena-agent", "--host", "0.0.0.0", "--port", "8001"]
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
      - MCP_URL=http://jena-mcp:8000/mcp
    ports:
      - "8001:8001"
    depends_on:
      - jena-mcp
```

```bash
docker compose -f docker/agent.compose.yml up -d
```

The agent's capabilities are declared in
[`a2a.json`](https://github.com/Knuckles-Team/jena-mcp/blob/main/a2a.json).
