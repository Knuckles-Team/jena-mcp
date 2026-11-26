---
name: jena-mcp-operations
skill_type: skill
description: >-
  Operate jena-mcp through its governed MCP and Arbora capabilities, including jena graph store, jena server admin, jena sparql operations. Use when a request requires this provider's read, change, automation, ingestion, troubleshooting, or evidence workflows.
---

# Jena Mcp Operations

Use the provider's governed MCP tools through Arbora delegation.

## Workflow

1. Establish the verified GraphSession and tenant before discovery or retrieval.
2. Discover the current condensed tool surface; never assume a stale tool name or schema.
3. Prefer read-only inspection first. For changes, present impact and use the provider's
   dry-run or preview mode when available.
4. Execute mutations as fenced WorkItems so retries remain idempotent and auditable.
5. Ingest source data only through the signed connector preset and ChangeEnvelope path.
6. Verify the durable result and its trace/evidence before reporting completion.

## Steps

1. Probe the surface with `jena_ping`. Verify it responds instead of returning a connection or authentication error.
2. Inspect first with `jena_list_datasets` and `jena_query` (dataset, sparql) using a `LIMIT`. Verify the target dataset exists and holds the expected data.
3. For a change, present the impact and pick the tool: `jena_update` (dataset, sparql), `jena_put_graph`, or `jena_create_dataset` (name, db_type). Verify the requester approved the exact dataset and graph.
4. Execute the single approved call, for example `jena_update` (dataset, sparql). Verify the response returns without error.
5. Re-read with `jena_query` or `jena_get_graph` (dataset, graph, accept). Verify the stored result matches the request and report it.

## Failure recovery

| Failure | Cause | Recovery |
|---------|-------|----------|
| Connection or authentication error | `APACHE_JENA_URL` unset, or credentials missing or wrong | Check `APACHE_JENA_URL` and `APACHE_JENA_TOKEN` or `JENA_USERNAME` and `JENA_PASSWORD`, and report which is unset |
| Destructive tool refused | `confirm` was not passed to `jena_delete_graph` or `jena_delete_dataset` | Show the target to the requester and pass `confirm=true` only after explicit approval |
| Query returns nothing | Wrong `dataset` name or graph IRI | Run `jena_list_datasets` and resend with the exact name |

## Safety contract

- Never persist credentials, endpoints, raw personal identifiers, hostnames, or local paths.
- Resolve TLS trust and verification from environment/configuration; never hardcode bypasses.
- Treat unknown ACL, tenant, schema, or tool-contract state as a hard failure.
- Require explicit approval for destructive, externally visible, or irreversible actions.
- Keep runtime traces policy-scoped and privacy-sanitized.

## Specialized workflows

Read [the workflow catalog](references/catalog.md) only when the request needs a
provider-specific procedure, parameter map, script, or reference asset.
