# Jena Graph Store

Read, replace, merge, or drop whole RDF graphs in an Apache Jena Fuseki dataset via the jena-mcp MCP server's Graph Store Protocol tool (jena_graph). Use when the agent must export a named/default graph as RDF, bulk-load an RDF document, merge triples into a graph, or delete a graph outright. Do NOT use for fine-grained SELECT/UPDATE by pattern (use jena-sparql-operations) or for server/dataset administration (use jena-server-admin).

# Jena Graph Store (GSP)

Whole-graph RDF I/O against an Apache Jena **Fuseki** dataset via the SPARQL
1.1 **Graph Store Protocol** (`/data`). The `jena_graph` tool addresses a named
graph URI or the default graph and moves the RDF as a serialized document.

## When to use
- Export a named or default graph as an RDF document (Turtle, N-Triples, JSON-LD…).
- Replace a graph wholesale with a supplied RDF payload (`put`).
- Merge additional triples into a graph without clearing it (`post`).
- Drop a graph entirely (`delete`).

## When NOT to use
- Querying/mutating by triple pattern, aggregates, or CONSTRUCT →
  `jena-sparql-operations`.
- Creating/deleting the *dataset* itself, stats, backup, compaction →
  `jena-server-admin`.
- Loading RDF the Fuseki host can fetch by URL — a SPARQL `LOAD <url>` update via
  `jena-sparql-operations` avoids shipping the payload through the agent.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`jena-mcp`** MCP server. Same
env as the other jena skills:

| Variable | Required | Notes |
|----------|----------|-------|
| `APACHE_JENA_URL` | ✅ | Fuseki base URL (aliases `JENA_FUSEKI_URL`, `JENA_URL`) |
| `APACHE_JENA_TOKEN` | optional | Bearer token (alias `JENA_TOKEN`) |
| `JENA_USERNAME` / `JENA_PASSWORD` | optional | Basic auth |
| `JENA_TLS_PROFILE` | optional | Named outbound TLS policy from AgentConfig |

## Tools & actions
| Tool | Actions | Key params |
|------|---------|-----------|
| `jena_graph` | `get`, `put`, `post`, `delete` | `dataset`, `graph`, `rdf_data`, `content_type`, `accept` |

- `dataset` — the Fuseki mount name (e.g. `ds`).
- `graph` — a named graph URI, or `default` (the literal) / `""` for the default graph.
- `rdf_data` — the serialized RDF payload (for `put`/`post`).
- `content_type` — serialization of `rdf_data` (default `text/turtle`).
- `accept` — desired serialization of the returned graph (for `get`, default `text/turtle`).

## Recipes
Export the default graph as Turtle:
```
action=get dataset=ds graph=default accept=text/turtle
```
Export a named graph as N-Triples:
```
action=get dataset=ds graph=[configured-endpoint] accept=application/n-triples
```
Replace a named graph with new Turtle (destructive):
```
action=put dataset=ds graph=[configured-endpoint] content_type=text/turtle
rdf_data="@prefix : <[configured-endpoint]> . :s :p :o ."
```
Merge triples into the default graph (additive):
```
action=post dataset=ds graph=default content_type=text/turtle
rdf_data="@prefix : <[configured-endpoint]> . :s2 :p :o2 ."
```
Drop a named graph:
```
action=delete dataset=ds graph=[configured-endpoint]
```

## Gotchas
- `put` **replaces** the entire graph — any triples not in `rdf_data` are lost.
  Use `post` to add without clearing.
- `graph=default` (or empty) targets the unnamed default graph; any other value
  is treated as a named-graph IRI.
- `content_type` must match the actual serialization of `rdf_data`, and `accept`
  drives the returned serialization on `get` — a mismatch yields a parse error or
  an unexpected format.
- GSP moves the whole graph in one request. For very large graphs prefer a
  server-side SPARQL `LOAD` (via `jena-sparql-operations`) over posting a huge
  payload through the agent.
- `delete` on a missing graph is a no-op/404 depending on Fuseki config — check
  the result rather than assuming success.

## Related
- `jena-sparql-operations` — pattern-level query/update and server-side `LOAD`.
- `jena-server-admin` — dataset lifecycle, backup, compaction, stats.
