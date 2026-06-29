# Drop Mermaid Diagram Support — Design

**Issue:** #124
**Date:** 2026-06-29

## Goal

Remove the Mermaid diagram extension from plcc-ng entirely. The extension is broken (`plcc-diagram-mermaid-build` calls kroki.io, which is unreliable; `plcc-diagram-mermaid-run` has no working renderer), and the redesign proposed in #111 was abandoned. PlantUML covers all current diagram needs. If a future diagram type requires Mermaid, it can be re-added then.

## What Gets Removed

### Source packages (delete entirely)

- `src/plcc/diagram/mermaid/` — `build.py`, `run.py`, their unit tests
- `src/plcc/diagram/class_diagram/mermaid/` — `emit.py`, its unit test

### Bats tests (delete entirely)

- `tests/bats/commands/plcc-diagram-class-mermaid-emit.bats`
- `tests/bats/commands/plcc-diagram-mermaid-build.bats`
- `tests/bats/commands/plcc-diagram-mermaid-run.bats`

### Docs (delete entirely)

- `docs/cli/commands/plcc-diagram-class-mermaid-emit.md`

## What Gets Edited

### `pyproject.toml`

Remove three entry points:

```
plcc-diagram-class-mermaid-emit
plcc-diagram-mermaid-build
plcc-diagram-mermaid-run
```

### `mkdocs.yml`

Remove three stale nav entries (old names from before #113 rename, already pointing to non-existent paths):

```yaml
- plcc-mermaid-diagram-build: cli/commands/plcc-mermaid-diagram-build.md
- plcc-mermaid-diagram-emit: cli/commands/plcc-mermaid-diagram-emit.md
- plcc-mermaid-diagram-run: cli/commands/plcc-mermaid-diagram-run.md
```

### Source files with Mermaid references

- `src/plcc/diagram/class_diagram/diagram.py` — remove `'mermaid': 'mmd'` from `_SOURCE_EXT`
- `src/plcc/diagram/syntax_diagram/diagram.py` — remove dead `'mermaid': 'mmd'` from `_SOURCE_EXT` (no corresponding emitter was ever registered)
- `src/plcc/diagram/build_test.py` — remove the Mermaid format test case
- `src/plcc/diagram/run_test.py` — remove the Mermaid format test case
- `src/plcc/diagram/list_test.py` — remove `class/mermaid` from expected outputs; remove `extract_type_format` test for `plcc-diagram-class-mermaid-emit`

### Bats tests with Mermaid references

- `tests/bats/commands/plcc-diagram-list.bats` — remove the `class/mermaid` assertion

### Docs with Mermaid mentions

Scrub all references to Mermaid from:

- `docs/cli/guide/diagram-extensions.md`
- `docs/cli/guide/under-the-hood.md`
- `docs/cli/guide/author-commands.md`
- `docs/cli/commands/plcc-diagram-class.md`
- `docs/cli/commands/plcc-diagram-emit.md`
- `docs/cli/commands/plcc-diagram-list.md`

## No Devcontainer or CI Changes

The Mermaid build command used Python stdlib (`urllib`) to call kroki.io — no Node.js, npm, or external CLI tool was installed. Nothing to remove from the devcontainer or workflows.

## CHANGELOG

Note as a breaking change: `--format=mermaid` is no longer accepted; `plcc-diagram-class-mermaid-emit`, `plcc-diagram-mermaid-build`, and `plcc-diagram-mermaid-run` are removed.

## Out of Scope

- `docs/superpowers/specs/2026-06-24-111-mermaid-build-kroki-design.md` and `docs/superpowers/plans/2026-06-24-111-mermaid-build-kroki.md` — these are historical development docs; leave them in place.
