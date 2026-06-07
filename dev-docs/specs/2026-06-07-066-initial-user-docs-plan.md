# Initial User Documentation — Approach and Mapping

**Date:** 2026-06-07
**Related spec:** [065 — Documentation Design](2026-06-07-065-documentation-design.md)

## Overview

The original PLCC project has a well-structured README that covers installation,
a working example, a commands reference, and full coverage of the three grammar
sections (lexical, syntactic, semantic). plcc-ng shares the same grammar language
and pipeline concepts but differs in installation, CLI command names, and implementation
language (Python instead of Java).

The approach is to batch-draft all plcc-ng user doc pages by mapping content from the
original PLCC README into the appropriate stub pages, then review flagged divergences
with the project maintainer before finalizing.

## Content Mapping

| PLCC README section | plcc-ng doc page |
|---|---|
| Installation (Codespace/Docker/Native) | `docs/getting-started.md` — replaced with `pip install plcc-ng` + prerequisites |
| Usage quickstart | `docs/getting-started.md` — updated for plcc-ng's CLI |
| Working Example | `docs/language-guide/examples.md` |
| Commands Reference | `docs/cli/primitives.md`, `docs/cli/orchestrators.md`, `docs/cli/index.md` |
| Grammar Files Structure (3-section intro) | `docs/language-guide/index.md` |
| Lexical Specification | `docs/language-guide/tokens.md` |
| Syntactic Specification | `docs/language-guide/grammar.md` |
| Semantic Specification + Hooks | `docs/language-guide/code-generation.md` |
| JSON AST | `docs/language-guide/code-generation.md` (appended; flagged if not yet in plcc-ng) |
| Home page navigation | `docs/index.md` |

## What Is Preserved

- Grammar syntax: `token`, `skip`, BNF rules, the `**=` repetition rule
- Scan and parse algorithm descriptions
- BNF naming conventions (non-terminals, terminals, distinguishing names)
- The working example (subtraction language) as the basis for `examples.md`
- Semantic specification structure and code injection pattern
- All hooks: `:top`, `:import`, `:class`, `:init` (these belong to the spec language,
  not to any specific target language)

## What Is Dropped

- Java-specific installation (SDKMAN, `javac`, `java -version`)
- PLCC's Docker/Codespace setup (plcc-ng installs via pip)
- PLCC's monolithic `plccmk`/`scan`/`parse`/`rep` command reference
  (replaced by plcc-ng's Level 0 primitives and Level 2 orchestrators)

## Flagging Convention

Anywhere the original content may not accurately reflect plcc-ng's current state —
different command names, unconfirmed feature parity, known divergences — the draft
marks the spot with an HTML comment:

```
<!-- TODO: verify this reflects plcc-ng (original PLCC used X, plcc-ng may differ) -->
```

These comments are invisible on the rendered site. Running `grep -r 'TODO:' docs/`
produces the review checklist.

## Areas Flagged for Review

These are known divergences that need maintainer judgment before the draft is final:

- **CLI command names** — PLCC uses `scan`, `parse`, `rep`; plcc-ng uses primitives
  (`plcc-tokens`, `plcc-trees`, etc.) and orchestrators (`plcc-scan`, `plcc-parse`,
  `plcc-rep`). The exact flags and contracts need verification against the installed
  commands.
- **Semantic specification / code injection** — PLCC injects Java. plcc-ng supports
  multiple target languages. How the code injection blocks work in plcc-ng (syntax,
  target language selection, entry point) needs verification.
- **JSON AST** — PLCC's `--json_ast` flag may or may not be present in plcc-ng.
- **Repetition rule (`**=`)** — Likely present but needs verification.
- **`$run()` entry point** — PLCC's start symbol overrides `$run()`. Verify plcc-ng
  uses the same convention.

## Draft Order

Pages are drafted in this order to build context incrementally:

1. `docs/language-guide/index.md` — establishes the three-section structure
2. `docs/language-guide/tokens.md` — lexical spec
3. `docs/language-guide/grammar.md` — syntactic spec
4. `docs/language-guide/code-generation.md` — semantic spec + hooks
5. `docs/language-guide/examples.md` — working example tying it all together
6. `docs/getting-started.md` — install + quickstart (references the example)
7. `docs/cli/index.md` — CLI overview
8. `docs/cli/primitives.md` — Level 0 commands
9. `docs/cli/orchestrators.md` — Level 2 commands
10. `docs/index.md` — home page with audience navigation paths
