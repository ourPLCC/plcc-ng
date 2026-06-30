# Design: Rename `build/` output directory to `plcc-ng/` (issue 125)

**Date:** 2026-06-29
**Type:** refactor / breaking change

## Problem

plcc-ng writes generated output into a directory named `build/`. This name collides with the output directories of many common build tools (Maven, Gradle, CMake, npm, etc.). When plcc-ng is used alongside any of those tools in the same project, ownership of the directory is ambiguous and collision risk is real. Renaming to `plcc-ng/` makes the directory unambiguously ours.

## Decision

**Clean cut.** No migration path, no deprecation period. The project has not yet cut a first major release, so backward compatibility is not required. The rename is noted as a breaking change in CHANGELOG.

## Approach

Introduce a single constant `OUTPUT_DIR = 'plcc-ng'` in `src/plcc/build/__init__.py`. Every site that currently hardcodes `'build'` as the output directory imports and uses this constant. No other structural changes.

The `plcc.build` module functions (`read_spec`, `write_spec`, `read_sentinel`, etc.) already take `build_dir` as an explicit parameter. Their signatures do not change.

## Constant

```python
# src/plcc/build/__init__.py
OUTPUT_DIR = 'plcc-ng'
```

This is the single source of truth. All other changes are mechanical consequences of importing this constant.

## Source changes (~4 files)

| File | What changes |
| --- | --- |
| `src/plcc/cmd/make.py:60` | `Path('build')` → `Path(OUTPUT_DIR)` |
| `src/plcc/cmd/rep.py` | Four `'build'` directory references → `OUTPUT_DIR` |
| `src/plcc/diagram/class_diagram/diagram.py` | Three `'build'` directory references → `OUTPUT_DIR` |
| `src/plcc/diagram/syntax_diagram/diagram.py` | Two `'build'` directory references → `OUTPUT_DIR` |

**Not changed:** `src/plcc/cmd/diagram.py:28` — `_RESERVED = frozenset({'emit', 'build', 'run', 'list'})`. The `'build'` here is a reserved subcommand verb, not an output directory name.

## Test changes (~14 files)

**Pytest tests (~11 files):** Replace `tmp_path / "build"` with `tmp_path / "plcc-ng"`. These tests pass paths explicitly, so no logic changes — only the string. Files:

- `src/plcc/cmd/make_test.py`, `parse_test.py`, `rep_test.py`, `scan_test.py`
- `src/plcc/diagram/class_diagram/diagram_test.py`, `syntax_diagram/diagram_test.py`

**Bats tests (~3 files):** Replace every `build/` shell path with `plcc-ng/`. No logic changes.

- `tests/bats/commands/plcc-make.bats` (~30 occurrences)
- `tests/bats/e2e/happy-path.bats` (2 occurrences)
- `tests/bats/e2e/plcc-rep.bats` (~14 occurrences)

## Docs changes (~10 files)

**Update:** User-facing docs that show shell examples with `build/` paths:

- `docs/migration.md` (3 occurrences)
- `docs/cli/commands/plcc-ll1.md`, `plcc-trees.md`, `plcc-model.md`, `plcc-tokens.md`, `plcc-parser-table.md`

**Leave untouched:** `docs/superpowers/plans/` — frozen historical records, not live documentation.

## CHANGELOG

Add a breaking change entry in the next release section:

> **Breaking:** The output directory has been renamed from `build/` to `plcc-ng/`. Update any `.gitignore` entries, scripts, or tooling that reference the old path.

## What is explicitly out of scope

- No auto-migration of existing `build/` directories on first run.
- No support for both `build/` and `plcc-ng/` simultaneously.
- No changes to `pyproject.toml`, entry points, or packaging layout.
- No changes to the `plcc.build` module function signatures.
