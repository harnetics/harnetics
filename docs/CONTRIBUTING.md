# Contributing to Harnetics

Thank you for your interest in contributing to Harnetics! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Reporting Bugs](#reporting-bugs)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/harnetics.git
   cd harnetics
   ```
3. **Add upstream** remote:
   ```bash
   git remote add upstream https://github.com/harnetics/harnetics.git
   ```

## Development Setup

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | ≥ 3.12 | Backend runtime |
| uv | latest | Python package manager |
| Node.js | ≥ 20 | Frontend build |
| npm | latest | Frontend package manager |

### Backend

```bash
uv sync --dev
```

### Frontend

```bash
cd frontend
npm install
cd ..
```

### Running the App

```bash
# Start backend (serves both API and SPA)
uv run uvicorn harnetics:create_app --factory --reload --port 8000

# Start frontend dev server (separate terminal, for hot reload)
cd frontend && npm run dev
```

### Running Tests

```bash
# Backend tests
uv run pytest -q

# Frontend build check
cd frontend && npm run build
```

### Backend-Only vs Frontend-Only Development

- **Backend only**: Skip `npm install`. The API works standalone at `http://localhost:8000/api/`.
- **Frontend only**: Run `npm run dev` in `frontend/`. The Vite dev server proxies API calls to the backend — make sure the backend is running on port 8000.

## Making Changes

### Branch Naming

Create a feature branch from `main`:

```bash
git checkout main
git pull upstream main
git checkout -b <type>/<short-description>
```

Branch types:
- `feat/` — New feature or enhancement
- `fix/` — Bug fix
- `docs/` — Documentation only
- `refactor/` — Code refactoring (no behavior change)
- `test/` — Adding or updating tests
- `ci/` — CI/CD changes

Examples: `feat/yaml-icd-parser`, `fix/impact-analysis-cache`, `docs/api-reference`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

<optional body>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `chore`

Examples:
```
feat(engine): add batch LLM judgement for impact analysis
fix(graph): prevent duplicate edges on re-import
docs(readme): add architecture diagram
```

## Pull Request Process

1. **Update your branch** with the latest `main`:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
2. **Ensure all tests pass**:
   ```bash
   uv run pytest -q
   cd frontend && npm run build
   ```
3. **Create the PR** against `main` branch
4. **Fill out the PR template** — describe what, why, and how to test
5. **Wait for CI** — all checks must pass before review
6. **Address review feedback** — push additional commits, then squash on merge

### What Makes a Good PR

- **Small and focused** — one logical change per PR
- **Tests included** — if you change behavior, add/update tests
- **Documentation updated** — if you add features, update relevant docs
- **AGENTS.md synced** — if you add/remove/move files, update the nearest AGENTS.md

## Coding Standards

### Python (Backend)

- **Style**: Follow existing code conventions; no excessive abstraction
- **Functions**: Keep under 20 lines; extract only when genuinely reused
- **Files**: Keep under 800 lines
- **Directories**: Max 8 files per directory level
- **Comments**: Chinese + ASCII block style (matches existing codebase)
- **Types**: Use Python type hints for function signatures
- **Tests**: pytest; place tests in `tests/` mirroring `src/` structure

### TypeScript (Frontend)

- **Components**: shadcn/ui + Tailwind CSS v4 (design system first)
- **Style**: No custom CSS — everything through Tailwind utilities
- **State**: React hooks; no global state library unless justified
- **Types**: Strict TypeScript; no `any` escape hatches

### Documentation Protocol (GEB)

This project follows a fractal documentation protocol:
- **L1** (`/AGENTS.md`): Project-level directory map
- **L2** (`/{module}/AGENTS.md`): Module member list and interfaces
- **L3** (file headers): `[INPUT]/[OUTPUT]/[POS]/[PROTOCOL]` contracts

When you add, remove, or move files, update the relevant AGENTS.md files. See [AGENTS.md](../AGENTS.md) for details.

## Reporting Bugs

Use the [Bug Report](https://github.com/harnetics/harnetics/issues/new?template=bug_report.yml) issue template. Include:

- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version, Node version)
- Relevant logs or screenshots

## Questions?

Open a [Discussion](https://github.com/harnetics/harnetics/discussions) or reach out via Issues.

---

Thank you for helping make aerospace document alignment better! 🚀
