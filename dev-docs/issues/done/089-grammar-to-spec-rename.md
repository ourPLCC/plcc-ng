# 089 - Rename "grammar file" to "specification file" throughout

**Type:** feat
**Date:** 2026-06-12

## Description

A `.plcc` file contains more than a grammar — it includes lexical rules,
syntactic rules, and semantic code. Calling it a "grammar file" undersells
it and is technically inaccurate. It should be called a "specification file"
(or just "spec file") because it fully specifies a language.

## Desired Changes

This is a broad rename touching multiple layers. Measure impact before
committing to a single approach; consider breaking into phases prioritizing
user-facing changes first.

### User-facing (highest priority)

- **Default file name:** `grammar.plcc` → `spec.plcc`
- **CLI flags:** `--grammar`/`-g` → `--spec`/`-s` on all commands
  (`plcc-make`, `plcc-scan`, `plcc-parse`, `plcc-rep`, and any others)
- **Error messages:** any message referencing "grammar file" or "grammar"
  in the context of the file name should say "spec file" or "spec"
- **Documentation:** all references to "grammar file", "grammar.plcc",
  and `--grammar`/`-g` in the docs

### Internal (lower priority)

- **Identifiers:** variable names, function names, class attributes that
  use `grammar` to refer to the spec file (e.g., `grammar_path`,
  `grammar_file`)
- **Comments:** inline comments referencing "grammar file"

## Notes

Measure the full scope before starting:

- Count occurrences of `grammar` in user-visible strings (error messages,
  help text, CLI flag names, docs)
- Count occurrences in internal identifiers and comments

Breaking this into sub-issues is recommended:
1. CLI flags and default file name
2. Error messages and help text
3. Documentation
4. Internal identifiers and comments

Each sub-issue can ship independently, prioritizing user-facing impact.
