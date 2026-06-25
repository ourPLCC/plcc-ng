# 114 - PlantUML EBNF diagram from lexical section

**Type:** feat
**Date:** 2026-06-25

## Description

Add `plcc-diagram-lexical`, a command that generates a PlantUML EBNF-style diagram from the lexical section of a PLCC spec file. This is the lexical counterpart to issue #109 (`plcc-diagram-syntactic`).

## Notes

- Input is the lexical section of the spec (token and skip rules), available from `plcc-spec` JSON output — no new parsing needed.
- Entry points follow the naming scheme established in issue #113:
  - `plcc-diagram-lexical` (orchestrator)
  - `plcc-diagram-lexical-plantuml-emit` (emitter)
- Reuses `plcc-diagram-plantuml-build` and `plcc-diagram-plantuml-run` unchanged.
- PlantUML EBNF (`@startebnf`) can represent lexical rules as named token definitions; skip rules may be included or omitted (TBD).
- Should be built after issue #109 (`plcc-diagram-syntactic`) since they share the same orchestrator pattern.
