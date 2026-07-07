# Design: PlantUML EBNF Diagram from Syntactic Section (Issue #109)

**Date:** 2026-06-25
**Status:** Approved

## Overview

Add `plcc-diagram-syntactic`, a command that generates a PlantUML EBNF diagram from the syntactic (grammar) section of a PLCC spec file. This gives users a visual picture of their grammar rules alongside the existing class diagram.

This issue also updates `plcc-diagram-class` to write its build artifacts to `build/diagram/class.*` for consistency with the new naming convention.

## Architecture

Two new modules under `src/plcc/diagram/`, mirroring the existing `class_diagram/` structure:

```text
src/plcc/diagram/
  syntactic_diagram/
    __init__.py
    diagram.py          ← plcc-diagram-syntactic orchestrator
    plantuml/
      __init__.py
      emit.py           ← plcc-diagram-syntactic-plantuml-emit
      emit_test.py
```

Two new entry points in `pyproject.toml`:

```toml
plcc-diagram-syntactic                = "plcc.diagram.syntactic_diagram.diagram:main"
plcc-diagram-syntactic-plantuml-emit  = "plcc.diagram.syntactic_diagram.plantuml.emit:main"
```

Existing infrastructure reused unchanged:

- `plcc-diagram-emit` dispatcher (routes `--type=syntactic --format=plantuml` → `plcc-diagram-syntactic-plantuml-emit`)
- `plcc-diagram-plantuml-build` (renders `.puml` → `.png` via plantuml.com)
- `plcc-diagram-plantuml-run` (opens `.png`)
- `plcc-diagram-list` (auto-discovers new emitter via `plcc-diagram-{type}-{fmt}-emit` pattern)

## Data Flow

```text
plcc-diagram-syntactic [--spec=FILE] [--format=plantuml]
  → plcc-spec <specfile>                             (stdout: spec JSON; validates spec)
  → plcc-diagram-emit --type=syntactic --format=FMT  (stdin: spec JSON; stdout: .puml source)
      → plcc-diagram-syntactic-plantuml-emit
  → plcc-diagram-build --format=FMT --input=build/diagram/syntactic.puml --output=build/diagram/syntactic.png
  → plcc-diagram-run --format=FMT --input=build/diagram/syntactic.png
```

Key difference from `plcc-diagram-class`: runs `plcc-spec` (fast, no model building) instead of `plcc-make --through=model`. The spec does not need to be LL(1)-valid to generate a syntactic diagram.

## Build Artifact Naming

All diagram artifacts live flat in `build/diagram/`, named by type:

| Command | Source file | Image file |
| --- | --- | --- |
| `plcc-diagram-class` | `build/diagram/class.puml` | `build/diagram/class.png` |
| `plcc-diagram-syntactic` | `build/diagram/syntactic.puml` | `build/diagram/syntactic.png` |

This also updates `plcc-diagram-class` from its current `build/diagram/diagram.{ext}` paths to `build/diagram/class.{ext}`.

## EBNF Translation

The emitter (`plcc-diagram-syntactic-plantuml-emit`) reads spec JSON from stdin, extracts `syntax.rules`, groups rules by LHS name, and emits a `@startebnf ... @endebnf` block.

**Rule grouping:** Multiple PLCC rules with the same LHS (alternatives via `altName`) are collapsed into one EBNF definition with `|`-separated alternatives.

**Mappings:**

| PLCC rule | PlantUML EBNF |
| --- | --- |
| `Lhs := A B C` | `Lhs ::= A B C ;` |
| Two rules: `Lhs := A` and `Lhs:Alt := B C` | `Lhs ::= A \| B C ;` |
| `Lhs **= Elem` (zero-or-more, no sep) | `Lhs ::= { Elem } ;` |
| `Lhs **= Elem SEP` (zero-or-more, with sep) | `Lhs ::= { Elem 'SEP' } ;` |
| `Lhs += Elem` (one-or-more, no sep) | `Lhs ::= Elem { Elem } ;` |
| `Lhs += Elem SEP` (one-or-more, with sep) | `Lhs ::= Elem { 'SEP' Elem } ;` |
| Terminal symbol (ALL_CAPS) | rendered quoted: `'PLUS'` |
| Non-terminal symbol (PascalCase) | rendered unquoted: `Expr` |

## Testing

- **Unit tests** in `emit_test.py`: cover each rule type (standard, multi-alternative, repeating zero-or-more/one-or-more, with and without separator). Tests use spec JSON as input and assert the emitted `.puml` string.
- **Bats command test** for `plcc-diagram-syntactic`: runs against a fixture spec, verifies `build/diagram/syntactic.puml` is produced with expected content. Build/run steps skipped in CI (consistent with existing class diagram bats tests).
- **Update `plcc-diagram-class` bats tests** to expect `build/diagram/class.puml` / `build/diagram/class.png` instead of `build/diagram/diagram.puml` / `build/diagram/diagram.png`.

## Out of Scope

- `plcc-diagram-lexical` (lexical section EBNF diagram) — tracked in issue #114.
- Mermaid format for syntactic diagrams — no `@startebnf` equivalent in Mermaid; deferred.
- LL(1) validation is not required to generate the diagram.
