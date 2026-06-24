# 109 - PlantUML EBNF diagram from syntactic section

**Type:** feat
**Date:** 2026-06-24

## Description

PlantUML supports an `@startebnf` / `@endebnf` diagram type that renders grammar rules visually. It would be useful to generate one of these from the syntactic section of a spec file, giving users a readable picture of their grammar alongside the existing class diagram.

## Notes

- The input is the syntactic section of the spec (grammar rules), not the model JSON (AST classes), so this differs architecturally from the existing class diagram pipeline.
- Could be a new format plugin (`--format=plantuml-ebnf`) within the existing `plcc-diagram` dispatch, or a separate top-level command (e.g., `plcc-ebnf-diagram`). The right choice depends on whether the emit/build/run pipeline fits.
- PlantUML's EBNF syntax: each rule becomes a named definition with its alternatives, sequences, terminals, and non-terminals expressed in PlantUML EBNF notation.
- The existing `plcc-spec` output (spec JSON) already contains the parsed syntactic rules, so no new parsing work is needed — only a new emitter.
