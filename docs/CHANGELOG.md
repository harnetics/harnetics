# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-20

### Added

- **Document Library**: Upload and browse Markdown/YAML documents with automatic section parsing and ICD parameter extraction; upload button wired to `POST /api/documents/upload`
- **Document Graph**: Directed graph of document relationships (traces_to, references, derived_from, constrained_by, supersedes, impacts) stored in SQLite
- **Draft Generation**: LLM-powered alignment draft generation with citation backfill from graph store, conflict detection, and evaluator quality gates
- **Impact Analysis**: BFS-based downstream change impact analysis with dual mode (AI vector search + heuristic), batch LLM judgement, and per-request caching
- **Evaluator Bus**: Pluggable quality gate framework with EA (citation integrity), EB (ICD consistency), and ED (AI quality) evaluator families
- **React SPA Frontend**: 9-page React 18 + TypeScript 5.7 application with shadcn/ui amethyst-haze theme, including Dashboard, Documents, Draft Workbench, Impact Analysis, and Graph Visualization
- **Settings UI**: Runtime LLM and embedding configuration (API key, model name, base URL) editable from the web settings page and persisted to `.env` via `write_dotenv_values()`
- **OpenAI-Compatible LLM Client**: Vendor-neutral LLM routing via OpenAI SDK with explicit Ollama fallback and status diagnostics
- **Embedding Search**: Section-level semantic search via ChromaDB with sentence-transformers and OpenAI-compatible embedding support
- **CLI**: `harnetics init`, `harnetics ingest`, `harnetics serve` commands via typer
- **Docker Support**: Multi-stage Dockerfile (Node 22 frontend builder + Python 3.12 runtime); `docker-compose.yml` for cloud/API-key deployments; `docker-compose-local.yml` for fully local Ollama GPU deployments; frontend `dist` bundled into runtime image so `docker compose up` serves the complete SPA + API
- **Fixture Corpus**: 10+ aerospace sample documents (requirements, ICD, design, test plans, quality, templates) for development and demo

### Changed

- Dockerfile dependency installation switched from pip to **uv** (local `.docker/uv` binary, no network fetch at build time)
- `docker-compose.yml` and `docker-compose-local.yml` split into separate files for cloud vs. local-model deployments
- README rewritten with Docker as the primary quickstart path; added Qwen 3.5 model compatibility table with 4-bit VRAM requirements

### Architecture

- Single workflow loop: Ingest → Parse & Graph Index → LLM Draft Generation → Evaluator Quality Gates → Impact Analysis → API/Web UI
- Backend: Python 3.12+ / FastAPI / SQLite (graph store) / ChromaDB (vector embeddings)
- Frontend: React 18 / TypeScript 5.7 / Vite 6 / Tailwind CSS v4 / shadcn/ui
- Local-first design: all data stays on the user's machine; `.env` is the single source of truth for runtime configuration

[0.1.0]: https://github.com/harnetics/harnetics/releases/tag/v0.1.0
