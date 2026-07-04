---
name: jena-server-admin
description: >-
  Administer an Apache Jena Fuseki server via the jena-mcp MCP server's admin
  tool (jena_admin) — dataset lifecycle (create/list/info/delete/set-state),
  server info, request stats, Prometheus metrics, async tasks, and TDB2 backup /
  compaction. Use when the agent must provision or take a dataset offline, check
  server health/stats, or run and track a backup or compaction. Do NOT use to run
  SPARQL (use jena-sparql-operations) or to read/write graph RDF (use
  jena-graph-store).
license: MIT
tags: [jena, fuseki, admin, tdb2, backup, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# Jena Server Admin

Operational control of an Apache Jena **Fuseki** server via its admin API
(`/$/…`), exposed by the single `jena_admin` tool. Covers dataset provisioning,
health/stats, and the two long-running maintenance tasks (backup, TDB2
compaction).

## When to use
- Provision a dataset (`create_dataset`) or remove one (`delete_dataset`).
- List datasets / inspect one (`list_datasets`, `dataset_info`).
- Take a dataset online/offline (`set_dataset_state`).
- Health-check and observe the server (`ping`, `server_info`, `stats`, `metrics`).
- Kick off and track maintenance (`backup`, `compact`, `list_tasks`, `task_info`).

## When NOT to use
- Querying or mutating triples → `jena-sparql-operations`.
- Reading/replacing/merging/dropping graph RDF documents → `jena-graph-store`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`jena-mcp`** MCP server. Admin
endpoints may require credentials even when the data endpoints are open.

| Variable | Required | Notes |
|----------|----------|-------|
| `APACHE_JENA_URL` | ✅ | Fuseki base URL (aliases `JENA_FUSEKI_URL`, `JENA_URL`) |
| `APACHE_JENA_TOKEN` | optional | Bearer token (alias `JENA_TOKEN`) |
| `JENA_USERNAME` / `JENA_PASSWORD` | optional | Basic auth (often required for `/$/`) |
| `JENA_SSL_VERIFY` | optional | TLS verification toggle |

## Tools & actions
The `jena_admin` tool takes an `action` plus `params_json` (a **JSON string**).

| Action | `params_json` keys |
|--------|--------------------|
| `ping` / `server_info` / `metrics` / `list_datasets` / `list_tasks` | — |
| `stats` | `dataset` (optional; omit for server-wide) |
| `dataset_info` | `name` |
| `create_dataset` | `name`, `db_type` (`tdb2` default, `tdb`, `mem`) |
| `delete_dataset` | `name` |
| `set_dataset_state` | `name`, `state` (`active` / `offline`) |
| `task_info` | `task_id` |
| `backup` | `dataset` |
| `compact` | `dataset`, `delete_old` (bool, default false) |

## Recipes (`params_json`)
Create a durable TDB2 dataset:
```json
{"name": "ds", "db_type": "tdb2"}
```
Take a dataset offline before maintenance:
```json
{"name": "ds", "state": "offline"}
```
Per-dataset request stats:
```json
{"dataset": "ds"}
```
Trigger a backup, then poll the returned task:
```json
{"dataset": "ds"}
```
```json
{"task_id": "1"}
```
Compact TDB2 and reclaim old files:
```json
{"dataset": "ds", "delete_old": true}
```

## Gotchas
- `params_json` is a **string** of JSON, not an object — serialize it.
- `backup` and `compact` are **asynchronous**: they return a task handle; poll
  `task_info`/`list_tasks` for `finished` before assuming completion.
- `compact` applies to **tdb2** datasets only; `mem` datasets are non-durable and
  lost on restart, and `tdb` (v1) cannot be compacted this way.
- `delete_dataset` removes the dataset *and its configuration* — irreversible;
  take a `backup` first.
- `set_dataset_state=offline` stops the dataset serving queries; remember to set
  it back to `active`.
- `stats` with no `dataset` is server-wide; pass `dataset` for one mount.

## Related
- `jena-sparql-operations` — SPARQL query/update on a live dataset.
- `jena-graph-store` — whole-graph RDF read/replace/merge/drop.
