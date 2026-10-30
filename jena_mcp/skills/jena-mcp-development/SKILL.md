---
name: jena-mcp-development
skill_type: skill
description: >-
  Develop and maintain the jena-mcp connector, including its Fuseki client,
  governed MCP tools, source declarations, packaged content, and release gates.
  Use when changing connector behavior, skills, prompts, ontology, or delivery
  configuration.
license: MIT
tags: [jena, fuseki, mcp, connector, development, delivery]
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---

# Jena MCP Development

Use this skill with the repository `AGENTS.md`, the owning `specs/` files, and
the focused tests. Keep the connector's one-door boundaries intact: the MCP
server exposes governed operations, while the API client owns HTTP details and
the source declarations describe ingestion metadata.

## Route and inspect before editing

1. Find the owning requirement under `specs/` before changing behavior. Record
   the requirement ID in the commit trailer.
2. Inspect the relevant source seam before editing:
   `jena_mcp/api/api_client_jena.py` owns Fuseki requests,
   `jena_mcp/mcp/mcp_jena.py` owns the typed `jena_sparql`, `jena_graph`,
   `jena_admin`, and `jena_source_records` tools, and
   `jena_mcp/connector_sources.py` owns source metadata.
3. Reuse the existing skills and workflow catalog for provider-specific
   procedures. Keep Graph Store, SPARQL, and server administration concerns in
   their respective skills instead of duplicating recipes here.
4. Preserve authentication and TLS policy in `jena_mcp/auth.py`; use
   `APACHE_JENA_URL` and `APACHE_JENA_TOKEN` first, with `JENA_TLS_PROFILE` for
   the named TLS policy. Never add credentials, raw endpoints, or bypassed TLS
   examples to a skill or test.

## Rapid delivery: the 5-minute contract

Deliver one small, reviewable slice tied to the owning spec row.

1. Read the owning spec, this skill, `AGENTS.md`, and the focused tests before
   editing. Confirm whether the change belongs to the connector, SDK, or
   pipelines repository before touching a file.
2. Make the smallest source or packaged-content change. Generated
   `specs/*/status.json` files are produced by the pipelines hook; never hand
   edit them. Keep package data under `jena_mcp/skills/`, `prompts/`, or
   `ontology/` so the existing setuptools declaration includes it.
3. Add or update a focused, network-free test that proves the changed contract
   and uses the real package paths. Do not turn a documentation check into a
   live Fuseki request.
4. Run the focused test and the repository's normal pre-commit checks. Inspect
   the complete diff and confirm that no root scratch files, credentials, or
   generated artifacts were added.
5. Commit with `Spec: PIPE-CONNSPEC-R130.4` when this skill contract is the
   owning delivery row, followed by the required `Co-Authored-By:` trailer.

## Setup and gates

Use the project extras for local checks:

```bash
uv sync --extra test
uv run pytest tests/test_jena_development_skill.py
pre-commit run --all-files
```

Keep test fixtures deterministic and offline. The normal package-data entry in
`pyproject.toml` must continue to include `skills/**`; do not add a second
installer or copy skill content into Python strings. If dependencies change,
use the repository's version and lockfile workflow from `AGENTS.md`.

## Delivery discipline

Work in a private real Git worktree based on the exact current `origin/main`.
Inspect `git status --short`, the staged allowlist, and the full diff before
committing. A skill-only change does not claim a released wheel, hosted Pages
publication, or runtime Fuseki evidence; those require their own release and
publication receipts.
