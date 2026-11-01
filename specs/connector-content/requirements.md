# CONN-JENA-MCP-CONNECTOR-CONTENT — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-JENA-MCP-CONNECTOR-CONTENT-R001` | **Default content.** `pyproject.toml` declares `jena-mcp` as the single `scion_sdk.connector` entry point. The server lists the packaged `skill://` and `ontology://` resources and the packaged prompts with no `content=` argument. Proving test: `tests/test_default_content_surfaces.py`. Caller chain: console_script jena-mcp (scion_sdk.cli:serve L18) -> installed_connectors -> jena_mcp/__init__.py::connector -> scion_sdk._connector_serve.build_server (L39), which serves the packaged skills, ontology (jena_mcp/ontology/jena.ttl) and prompts. Shape: no code change; Connector(api, get_client, tools, instructions) takes no content argument and the SDK builds defaults with ConnectorContent.for_package; the test uses build_server('jena_mcp', command_args=['--transport','stdio','--auth-type','none']) with a FastMCP Client. | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. Planned test: `tests/test_default_content_surfaces.py::test_default_content_surfaces`. |
