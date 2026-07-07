# Design: Rename Diagram Commands to `plcc-diagram-*` Namespace (Issue 113)

**Date:** 2026-06-25
**Issue:** [113 - Rename diagram commands to consistent `plcc-diagram-*` namespace](../issues/done/113-rename-diagram-commands.md)

## Summary

Rename all diagram commands to a unified `plcc-diagram-*` namespace and restructure the Python modules to match. `plcc-diagram` evolves from a single class-diagram orchestrator into a type-discoverer that runs all installed diagram types. This is a pre-1.0 breaking change that must land before issue #109 (EBNF diagram).

Delivered in two phases: infrastructure first (additive, nothing breaks), then the rename + module restructure (breaking).

---

## Command Architecture

### User-facing commands

| Old | New | Role |
|-----|-----|------|
| `plcc-diagram` | `plcc-diagram` | **Repurposed**: type-discoverer; scans PATH for `plcc-diagram-{type}` commands and runs each |
| `plcc-diagram` | `plcc-diagram-class` | Class diagram orchestrator (what `plcc-diagram` does today) |

### Emit plugins (type + format specific)

| Old | New |
|-----|-----|
| `plcc-plantuml-diagram-emit` | `plcc-diagram-class-plantuml-emit` |
| `plcc-mermaid-diagram-emit` | `plcc-diagram-class-mermaid-emit` |

### Build/run plugins (format specific, shared across diagram types)

| Old | New |
|-----|-----|
| `plcc-plantuml-diagram-build` | `plcc-diagram-plantuml-build` |
| `plcc-plantuml-diagram-run` | `plcc-diagram-plantuml-run` |
| `plcc-mermaid-diagram-build` | `plcc-diagram-mermaid-build` |
| `plcc-mermaid-diagram-run` | `plcc-diagram-mermaid-run` |

### Dispatchers (names unchanged, dispatch patterns updated)

| Command | Old dispatch target | New dispatch target |
|---------|---------------------|---------------------|
| `plcc-diagram-emit` | `plcc-{fmt}-diagram-emit` | `plcc-diagram-{type}-{fmt}-emit` |
| `plcc-diagram-build` | `plcc-{fmt}-diagram-build` | `plcc-diagram-{fmt}-build` |
| `plcc-diagram-run` | `plcc-{fmt}-diagram-run` | `plcc-diagram-{fmt}-run` |
| `plcc-diagram-list` | scans `plcc-(.+)-diagram-emit` | scans `plcc-diagram-(.+)-(.+)-emit`, prints one `type/format` pair per line (e.g., `class/plantuml`) |

`plcc-diagram-emit` gains a `--type` flag (no default; required; the class orchestrator passes `--type=class`).

---

## Type Discovery (`plcc-diagram`)

`plcc-diagram` scans PATH for executables matching `plcc-diagram-{type}` and runs each in sequence. It passes `--spec` and `--banner` through to each type orchestrator; each type manages its own `--format` default.

**Reserved words** excluded from type discovery: `emit`, `build`, `run`, `list`.

```python
RESERVED = {'emit', 'build', 'run', 'list'}

def find_types():
    # scan PATH for plcc-diagram-{name} where name not in RESERVED
```

This is the same PATH-scanning approach used by `plcc-diagram-list` for format discovery.

---

## Python Module Structure

`class` is a Python keyword so the class-diagram subdirectory is named `class_diagram`.

```
src/plcc/
  cmd/
    diagram.py                   # repurposed: plcc-diagram type-discoverer
    diagram_test.py
  diagram/
    build.py                     # plcc-diagram-build dispatcher (pattern updated)
    build_test.py
    emit.py                      # plcc-diagram-emit dispatcher (gains --type flag)
    emit_test.py
    run.py                       # plcc-diagram-run dispatcher (pattern updated)
    run_test.py
    list.py                      # plcc-diagram-list (scan pattern updated)
    list_test.py
    class_diagram/               # NEW: class diagram type
      diagram.py                 # plcc-diagram-class orchestrator (moved from cmd/diagram.py)
      diagram_test.py
      plantuml/
        emit.py                  # plcc-diagram-class-plantuml-emit (moved from diagram/plantuml/emit.py)
        emit_test.py
      mermaid/
        emit.py                  # plcc-diagram-class-mermaid-emit (moved from diagram/mermaid/emit.py)
        emit_test.py
    plantuml/
      build.py                   # plcc-diagram-plantuml-build (emit.py removed)
      build_test.py
      run.py                     # plcc-diagram-plantuml-run
      run_test.py
    mermaid/
      build.py                   # plcc-diagram-mermaid-build (emit.py removed)
      build_test.py
      run.py                     # plcc-diagram-mermaid-run
      run_test.py
```

Moved files will need their relative imports updated to account for changed directory depth.

---

## `pyproject.toml` Entry Points

```toml
plcc-diagram                  = "plcc.cmd.diagram:main"                       # repurposed
plcc-diagram-class            = "plcc.diagram.class_diagram.diagram:main"     # new
plcc-diagram-class-plantuml-emit = "plcc.diagram.class_diagram.plantuml.emit:main"
plcc-diagram-class-mermaid-emit  = "plcc.diagram.class_diagram.mermaid.emit:main"
plcc-diagram-plantuml-build   = "plcc.diagram.plantuml.build:main"
plcc-diagram-plantuml-run     = "plcc.diagram.plantuml.run:main"
plcc-diagram-mermaid-build    = "plcc.diagram.mermaid.build:main"
plcc-diagram-mermaid-run      = "plcc.diagram.mermaid.run:main"
# dispatchers (module paths unchanged):
plcc-diagram-emit             = "plcc.diagram.emit:main"
plcc-diagram-build            = "plcc.diagram.build:main"
plcc-diagram-run              = "plcc.diagram.run:main"
plcc-diagram-list             = "plcc.diagram.list:main"
```

Old entries (`plcc-plantuml-diagram-emit`, etc.) are removed.

---

## Affected Files Beyond Python Source

**Bats tests** — rename files and update command references inside:

| Old | New |
|-----|-----|
| `tests/bats/commands/plcc-diagram.bats` | split: `plcc-diagram.bats` (type-discoverer) + `plcc-diagram-class.bats` |
| `tests/bats/commands/plcc-plantuml-diagram-emit.bats` | `plcc-diagram-class-plantuml-emit.bats` |
| `tests/bats/commands/plcc-plantuml-diagram-build.bats` | `plcc-diagram-plantuml-build.bats` |
| `tests/bats/commands/plcc-plantuml-diagram-run.bats` | `plcc-diagram-plantuml-run.bats` |

**Docs** — rename pages and update all command name references:

| Old | New |
|-----|-----|
| `docs/cli/commands/plcc-diagram.md` | split: `plcc-diagram.md` + `plcc-diagram-class.md` |
| `docs/cli/commands/plcc-plantuml-diagram-emit.md` | `plcc-diagram-class-plantuml-emit.md` |
| `docs/cli/commands/plcc-plantuml-diagram-build.md` | `plcc-diagram-plantuml-build.md` |
| `docs/cli/commands/plcc-plantuml-diagram-run.md` | `plcc-diagram-plantuml-run.md` |
| `docs/cli/commands/plcc-mermaid-diagram-emit.md` | `plcc-diagram-class-mermaid-emit.md` |
| `docs/cli/commands/plcc-mermaid-diagram-build.md` | `plcc-diagram-mermaid-build.md` |
| `docs/cli/commands/plcc-mermaid-diagram-run.md` | `plcc-diagram-mermaid-run.md` |

Guide pages (`diagram-extensions.md`, `under-the-hood.md`, `author-commands.md`) need all command name references updated.

---

## Phasing

### Phase 1 — New `plcc-diagram` type-discoverer (additive, nothing breaks)

Implement the new `plcc-diagram` in `src/plcc/cmd/diagram.py`. In Phase 1 it will discover no types (since `plcc-diagram-class` does not exist yet) and exit cleanly. Tests cover the scanning and reserved-word filtering logic. No existing commands are touched.

### Phase 2 — Rename + Restructure (breaking)

All remaining changes land together so the dispatch patterns, plugin names, and module paths are always consistent:

- Add `--type` flag to `plcc-diagram-emit`; update its dispatch pattern to `plcc-diagram-{type}-{fmt}-emit`
- Update dispatch patterns in `plcc-diagram-build` and `plcc-diagram-run`
- Update scan pattern in `plcc-diagram-list`
- Rename all `pyproject.toml` entry points
- Move Python files into `class_diagram/` layout; update imports
- Update all docstrings and string literals referencing old command names
- Rename and update bats test files
- Rename and update doc pages
