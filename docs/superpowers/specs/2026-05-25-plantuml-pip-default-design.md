---
title: PlantUML pip install as default diagram backend
date: 2026-05-25
---

## Problem

The current `plcc-mermaid-diagram-build` requires `npm install -g @mermaid-js/mermaid-cli`
(Node.js + npm). The previous Python `mmdc` library was dropped because PhantomJS is EOL.
PLCC's primary audience is students, who cannot be assumed to have Node.js, npm, or Java
pre-installed. Install friction must be minimized.

## Design

### Goal

`pip install plcc-ng[diagram]` gives users a working diagram experience out of the box.
No Node.js, no npm, no Java required.

### Approach

Use the `plantuml` PyPI package, which encodes `.puml` source and sends it to the
plantuml.com web API, returning a PNG. Zero external binaries. Requires internet access.

Local/offline rendering (local plantuml binary, Docker) is deferred to a future iteration.

### New files

**`src/plcc/diagram/plantuml/build.py`** — `plcc-plantuml-diagram-build`

Reads a `.puml` input file, sends it to `https://www.plantuml.com/plantuml/png/` via the
`plantuml` PyPI package, and writes the response as a `.png` output file.

If `plantuml` is not installed, exits with a clear error:
`plantuml not installed — run: pip install plcc-ng[diagram]`

**`src/plcc/diagram/plantuml/run.py`** — `plcc-plantuml-diagram-run`

Opens the PNG in the system viewer (`open` on macOS, `xdg-open` on Linux, `os.startfile`
on Windows). Identical in structure to `plcc-mermaid-diagram-run`. No extra dependencies.

### Default format change: `mermaid` → `plantuml`

Five locations hardcode `mermaid` as the default — all changed to `plantuml`:

| File | Change |
|------|--------|
| `src/plcc/diagram/emit.py` | docstring default |
| `src/plcc/diagram/build.py` | docstring default |
| `src/plcc/diagram/run.py` | docstring default |
| `src/plcc/cmd/diagram.py` | docstring default |
| `src/plcc/cmd/make.py` | docstring default + hardcoded fallback |

Corresponding tests updated: `emit_test.py`, `diagram_test.py`, `make_test.py`.

### `pyproject.toml` changes

New entry points:
```toml
plcc-plantuml-diagram-build = "plcc.diagram.plantuml.build:main"
plcc-plantuml-diagram-run   = "plcc.diagram.plantuml.run:main"
```

New optional dependency:
```toml
[project.optional-dependencies]
diagram = ["plantuml"]
```

Mermaid remains available as `--format=mermaid` for users who have `mmdc` on PATH.

## Testing

- Unit tests for `plcc-plantuml-diagram-build` (mock the `plantuml` package calls)
- Unit tests for `plcc-plantuml-diagram-run` (mock subprocess/os calls)
- Bats command tests for `plcc-plantuml-diagram-build` and `plcc-plantuml-diagram-run`
- Updated unit tests for default format change in emit, build, run, diagram, make
- No E2E test against plantuml.com (network dependency; not appropriate for CI)

## Future work

- Local plantuml binary support (detect Java + plantuml JAR, use if available)
- Docker-based rendering as an alternative for fully offline environments
- User-configurable default format (env var or config file)
