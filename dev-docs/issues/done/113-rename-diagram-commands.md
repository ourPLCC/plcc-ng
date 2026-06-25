# 113 - Rename diagram commands to consistent `plcc-diagram-*` namespace

**Type:** refactor
**Date:** 2026-06-24

## Description

The current diagram command names use an inconsistent `plcc-{format}-diagram-{action}` pattern (e.g., `plcc-plantuml-diagram-emit`, `plcc-diagram` for the class diagram orchestrator). With the addition of issue #109 (`plcc-diagram-ebnf`), we need a consistent naming scheme before the first release.

Rename all diagram commands to a unified `plcc-diagram-*` namespace following this structure:
- `diagram → type → format → action` for emit (type+format specific)
- `diagram → format → action` for build/run (format specific, shared across types)

## Renames

**User-facing orchestrators:**
- `plcc-diagram` → `plcc-diagram-class`

**Emit plugins (type + format specific):**
- `plcc-plantuml-diagram-emit` → `plcc-diagram-class-plantuml-emit`
- `plcc-mermaid-diagram-emit` → `plcc-diagram-class-mermaid-emit`

**Build/run plugins (format specific, shared across diagram types):**
- `plcc-plantuml-diagram-build` → `plcc-diagram-plantuml-build`
- `plcc-plantuml-diagram-run` → `plcc-diagram-plantuml-run`
- `plcc-mermaid-diagram-build` → `plcc-diagram-mermaid-build`
- `plcc-mermaid-diagram-run` → `plcc-diagram-mermaid-run`

**Dispatchers (internal, purpose unchanged):**
- `plcc-diagram-emit` — stays, but dispatches to `plcc-diagram-{type}-{fmt}-emit`
- `plcc-diagram-build` — stays, but dispatches to `plcc-diagram-{fmt}-build`
- `plcc-diagram-run` — stays, but dispatches to `plcc-diagram-{fmt}-run`
- `plcc-diagram-list` — stays, scans for `plcc-diagram-*-emit` commands

## Notes

- This is a breaking change to all entry points, module paths, bats tests, and docs — but acceptable pre-1.0.
- Must be completed before the first release.
- Issue #109 (`plcc-diagram-ebnf`) should be built on top of this rename, not before it.
