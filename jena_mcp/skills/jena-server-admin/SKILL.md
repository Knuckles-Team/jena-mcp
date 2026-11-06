---
name: jena-server-admin
skill_type: skill
description: >-
  Administer an Apache Jena Fuseki server via the jena-mcp MCP server's admin
  tools (jena_list_datasets, jena_create_dataset, ...) — dataset lifecycle (create/list/info/delete/set-state),
  server info, request stats, Prometheus metrics, async tasks, and TDB2 backup /
  compaction. Use when the agent must provision or take a dataset offline, check
  server health/stats, or run and track a backup or compaction. Do NOT use to run
  SPARQL (use jena-sparql-operations) or to read/write graph RDF (use
  jena-graph-store).
license: MIT
tags: [jena, fuseki, admin, tdb2, backup, mcp]
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---
# Jena Server Admin

Operational control of an Apache Jena **Fuseki** server via its admin API
(`/$/…`), exposed as one typed tool per operation. Covers dataset provisioning,
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

## Tools
One typed tool per Fuseki admin operation.

| Tool | Arguments |
|------|-----------|
| `jena_ping`, `jena_server_info`, `jena_metrics`, `jena_list_datasets`, `jena_list_tasks` | none |
| `jena_stats` | `dataset` (optional; omit for server-wide) |
| `jena_dataset_info` | `name` |
| `jena_create_dataset` | `name`, `db_type` (`tdb2` default, `tdb`, `mem`) |
| `jena_delete_dataset` | `name`, `confirm` |
| `jena_set_dataset_state` | `name`, `state` (`active` / `offline`) |
| `jena_task_info` | `task_id` |
| `jena_backup` | `dataset` |
| `jena_compact` | `dataset`, `delete_old` (bool, default false) |

## Recipes
Create a durable TDB2 dataset: `jena_create_dataset` with `name="ds"`, `db_type="tdb2"`.

Take a dataset offline before maintenance: `jena_set_dataset_state` with `name="ds"`, `state="offline"`.

Per-dataset request stats: `jena_stats` with `dataset="ds"`.

Trigger a backup, then poll the returned task: `jena_backup` with `dataset="ds"`, then `jena_task_info` with `task_id="1"`.

Compact TDB2 and reclaim old files: `jena_compact` with `dataset="ds"`, `delete_old=true`.

## Gotchas
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
