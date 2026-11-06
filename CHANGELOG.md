# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.8] - 2026-11-06

### Changed
- Removed the action-routed `jena_sparql`, `jena_graph` and `jena_admin` tools; every Fuseki operation is its own typed tool (`jena_query`, `jena_update`, `jena_*_graph`, the admin tools).
- Declared tool-use contracts, links, data locations and business roles; replaced the single prompt with an operator prompt and three business-role prompts; raised `scion-sdk` to `>=0.9.0`.

## [2.4.7] - 2026-10-30

### Changed
- Require `scion-sdk>=0.6.4,<0.7.0`; `uv.lock` relocked.

## [2.4.5] - 2026-10-27

### Added
- Add the packaged development skill and make the canonical Pages publisher exclusive.

## [2.4.4] - 2026-10-24

### Changed
- Central connector migration: requires `agent-connector-sdk>=0.5.4`; server bootstrap, version, containers, ontology artifacts, security scaffold and pre-commit config are provided centrally.

## [Unreleased]

## [0.1.0] - 2026-06-01
### Added
- Initial project structure and standardization
- Standardized README, AGENTS, and `.env.example`
- Copied testing and script boilerplate from gitlab-api
