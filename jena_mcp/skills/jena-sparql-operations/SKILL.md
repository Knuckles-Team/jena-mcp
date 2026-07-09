---
name: jena-sparql-operations
skill_type: skill
description: >-
  Run SPARQL against an Apache Jena Fuseki dataset via the jena-mcp MCP server —
  read queries (SELECT/ASK/CONSTRUCT/DESCRIBE) and updates (INSERT/DELETE/LOAD/
  CLEAR) with the domain-typed jena_sparql tool. Use when the agent must query
  triples, count/aggregate over a graph, or mutate data with a SPARQL update
  against a named Fuseki dataset. Do NOT use to read/replace whole graphs as RDF
  documents (use jena-graph-store) or to create datasets / run backups / read
  stats (use jena-server-admin).
license: MIT
tags: [jena, fuseki, sparql, rdf, triplestore, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# Jena SPARQL Operations

Domain-typed SPARQL access to an Apache Jena **Fuseki** dataset. The single
`jena_sparql` tool routes to the dataset's `/sparql` (read) and `/update`
(write) endpoints. Prefer it over raw HTTP — it carries the correct content
types and Accept negotiation.

## When to use
- Read triples with a SELECT / ASK / CONSTRUCT / DESCRIBE query.
- Aggregate or count over a graph (COUNT, GROUP BY).
- Mutate data with a SPARQL UPDATE (INSERT DATA, DELETE/INSERT WHERE, LOAD, CLEAR).

## When NOT to use
- Reading or replacing an entire named graph as an RDF document (bulk export /
  import) → `jena-graph-store` (Graph Store Protocol is faster and streamable).
- Creating / deleting datasets, reading stats/metrics, backup, or compaction →
  `jena-server-admin`.
- SPARQL against a non-Jena store → that store's own skill.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`jena-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `APACHE_JENA_URL` | ✅ | Fuseki base URL (aliases `JENA_FUSEKI_URL`, `JENA_URL`); defaults to `http://localhost:3030` |
| `APACHE_JENA_TOKEN` | optional | Bearer token (alias `JENA_TOKEN`) |
| `JENA_USERNAME` / `JENA_PASSWORD` | optional | Basic auth |
| `JENA_SSL_VERIFY` | optional | TLS verification toggle |

## Tools & actions
| Tool | Actions | Key params |
|------|---------|-----------|
| `jena_sparql` | `query`, `update` | `dataset`, `sparql`, `accept` (query only) |

- `dataset` — the Fuseki mount name (e.g. `ds`), not a full URL.
- `sparql` — the query/update string.
- `accept` — result media type for `query` (default
  `application/sparql-results+json`; use `text/turtle` for CONSTRUCT/DESCRIBE).

## Recipes
Count triples in the default graph:
```
action=query dataset=ds
sparql="SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }"
```
List 10 subjects of a type:
```
action=query dataset=ds
sparql="PREFIX : <http://knuckles.team/kg#> SELECT ?s WHERE { ?s a :JenaDataset } LIMIT 10"
```
CONSTRUCT a subgraph as Turtle:
```
action=query dataset=ds accept=text/turtle
sparql="CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o } LIMIT 100"
```
Insert triples:
```
action=update dataset=ds
sparql="PREFIX : <http://knuckles.team/kg#> INSERT DATA { :ds1 a :JenaDataset ; :datasetName \"ds\" }"
```
Delete-insert (rename in place):
```
action=update dataset=ds
sparql="DELETE { ?s :datasetState \"offline\" } INSERT { ?s :datasetState \"active\" } WHERE { ?s :datasetState \"offline\" }"
```

## Gotchas
- Pick the right `action`: reads go through `query`, all mutations through
  `update`. A SELECT sent to `update` (or vice versa) is rejected by Fuseki.
- `dataset` is the mount name only — the tool appends `/sparql` or `/update`.
- For CONSTRUCT/DESCRIBE set `accept=text/turtle` (or another RDF type); the
  default JSON results type only applies to SELECT/ASK.
- `LOAD <url>` fetches server-side — the URL must be reachable from the Fuseki
  host, not the agent.
- Always bound exploratory SELECTs with `LIMIT`; unbounded scans over TDB2 are
  slow on large datasets.

## Related
- `jena-graph-store` — whole-graph RDF read/replace/merge/drop (GSP).
- `jena-server-admin` — dataset lifecycle, stats, tasks, backup, compaction.
