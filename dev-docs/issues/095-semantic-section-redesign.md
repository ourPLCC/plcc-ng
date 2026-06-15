# 095 - Redesign the semantic section format

**Type:** feat
**Date:** 2026-06-15

## Description

The semantic section of a spec file needs a coherent redesign. Four earlier
issues (087, 090, 091, 092) approached this piecemeal and in some cases
contradicted each other. This issue supersedes all four and describes the
final agreed design.

## Desired Behavior

### Divider

The divider between sections is a bare `%` on a line by itself — nothing else
on the line.

```text
token NUM '\d+'
skip  SPACE '\s+'

%

<Program> **= <Expr:e>

%

Python

Program
%%%
def _run(self):
    print(self.e._v)
%%%
```

### Language declaration

The **first non-blank, non-comment line** of the semantics section is the
language name. It must appear on a line by itself.

- The name is **case-sensitive** and must match the canonical casing registered
  by the language extension (e.g. `Python`, `Java`).
- The name identifies which extension commands process the section:
  `plcc-<lang>-emit`, `plcc-<lang>-build`, etc.
- A non-canonical casing (e.g. `python`, `JAVA`) is a syntax error.

### No tool naming

The old `% toolname Language` divider syntax and the concept of named "tools"
within a spec file are removed entirely. A spec file may contain only one
semantics section. The `--tool` flag on `plcc-rep` (and any other command
that accepted it) is removed.

## Replaces

- [[087-divider-language-first]] — divider syntax change (superseded: language
  goes in body, not on divider)
- [[090-separator-language-case-sensitive]] — case sensitivity (absorbed here)
- [[091-single-semantic-section]] — single section + remove `--tool` (absorbed)
- [[092-language-as-first-line-of-semantics]] — language in body (the adopted
  design; superseded by this consolidated issue)

## Notes

- This is a breaking change for any spec file using the old `% Language` or
  `% toolname Language` divider syntax.
- The `%` divider becomes uniform across all three section boundaries.
- See also [[089-grammar-to-spec-rename]] for the broader rename of "grammar
  file" to "spec file," which lands alongside this work.
- See [[094-docs-status-after-initial-branch]] for doc pages that will need
  updating once this lands (`language-guide/semantic.md`,
  `cli/orchestrators.md`, `language-guide/examples.md`).
