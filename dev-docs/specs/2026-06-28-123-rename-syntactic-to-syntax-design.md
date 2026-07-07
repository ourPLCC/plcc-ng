# Design: Rename syntactic → syntax in plcc-diagram-* (Issue #123)

**Date:** 2026-06-28
**Type:** refactor
**Issue:** [123](../issues/done/123-rename-syntactic-to-syntax-in-plcc-diagram.md)

## Summary

Replace every occurrence of "syntactic" in the `plcc-diagram-*` surface with "syntax". This is a clean-break rename with no backward-compatibility aliases. The issue explicitly acknowledges this as a breaking change.

## Scope

### Command names (`pyproject.toml` entry points)

| Old | New |
|-----|-----|
| `plcc-diagram-syntactic` | `plcc-diagram-syntax` |
| `plcc-diagram-syntactic-plantuml-emit` | `plcc-diagram-syntax-plantuml-emit` |

### Internal dispatch (`src/plcc/diagram/syntax_diagram/diagram.py`)

The `--type=syntactic` argument passed to `plcc-diagram-emit` becomes `--type=syntax`. This controls which emit plugin is resolved (e.g. `plcc-diagram-syntax-plantuml-emit`).

### Output filenames (generated at runtime)

| Old | New |
|-----|-----|
| `build/diagram/syntactic.puml` | `build/diagram/syntax.puml` |
| `build/diagram/syntactic.png` | `build/diagram/syntax.png` |

### Python module directory

`src/plcc/diagram/syntactic_diagram/` → `src/plcc/diagram/syntax_diagram/`

All internal imports that reference `syntactic_diagram` are updated to `syntax_diagram`.

### Tests

| Old | New |
|-----|-----|
| `tests/bats/commands/plcc-diagram-syntactic.bats` | `tests/bats/commands/plcc-diagram-syntax.bats` |
| `tests/bats/commands/plcc-diagram-syntactic-plantuml-emit.bats` | `tests/bats/commands/plcc-diagram-syntax-plantuml-emit.bats` |
| `tests/bats/commands/plcc-diagram-list.bats` | update `syntactic/plantuml` → `syntax/plantuml` |
| `bin/test/packaging.bash` | update command names + list assertion |

Docstrings and inline string literals in `diagram.py`, `diagram_test.py`, and `plantuml/emit.py` are updated throughout.

## Out of scope

- `plcc-validate-syntactic` — not a `plcc-diagram-*` command; a separate concern.
- `src/plcc/spec/syntax/` — "syntactic" appears only in internal Python identifiers related to spec parsing (a different concept, not user-facing command names or filenames).
- Any `dev-docs/` or `docs/` prose that mentions "syntactic" as a concept (not a command name).

## Approach

Single clean-break commit. No aliases. No phased rollout.
