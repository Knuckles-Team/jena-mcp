# Installation

`jena-mcp` is a standard Python package and a prebuilt container image. Pick the
path that matches how you want to run it.

## Requirements

- **Python 3.11 – 3.14**.
- A reachable **Apache Jena Fuseki** server — see [Backing Platform](platform.md)
  to deploy one locally.

## From PyPI (recommended)

```bash
pip install jena-mcp
```

### Optional extras

The base install is intentionally minimal. Install the extra for what you need:

| Extra | Install | Pulls in |
|---|---|---|
| `mcp` | `pip install "jena-mcp[mcp]"` | FastMCP MCP-server runtime (`agent-utilities[mcp]`) |
| `agent` | `pip install "jena-mcp[agent]"` | Pydantic-AI agent server + Logfire tracing |
| `all` | `pip install "jena-mcp[all]"` | The MCP server, the agent server, and tracing |
| `test` | `pip install "jena-mcp[test]"` | `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-xdist` |

```bash
# Typical: run both the MCP server and the A2A agent server
pip install "jena-mcp[all]"
```

## From source

```bash
git clone https://github.com/Knuckles-Team/jena-mcp.git
cd jena-mcp
pip install -e ".[all]"          # editable install with every extra
```

With [`uv`](https://docs.astral.sh/uv/):

```bash
uv pip install -e ".[all]"
uv run jena-mcp
```

## Prebuilt Docker image

A multi-stage runtime image is published on every release (installs `jena-mcp[all]`,
entrypoint `jena-mcp`):

```bash
docker pull example/jena-mcp@sha256:<digest>

docker run --rm -i \
  -e JENA_FUSEKI_URL=http://your-fuseki:3030 \
  -e JENA_USERNAME=admin \
  -e JENA_PASSWORD=admin \
  example/jena-mcp@sha256:<digest>          # stdio transport (default)
```

For an HTTP server with a published port, see [Deployment](deployment.md).

## Verify the install

```bash
jena-mcp --help
python -c "import jena_mcp; print(jena_mcp.__version__)"
```

## Next steps

- **[Deployment](deployment.md)** — run it as a long-lived MCP server (and agent server) behind Caddy + DNS.
- **[Usage](usage.md)** — call the tools, the `JenaApi` client, and the CLI.
- **[Configuration](deployment.md#configuration-environment)** — every environment variable.
