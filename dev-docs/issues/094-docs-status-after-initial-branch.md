# 094 - Docs status after initial documentation branch

**Type:** chore
**Date:** 2026-06-15

## Description

Status of each docs page after the `docs/initial-documentation` branch merged.
Use this to track what still needs attention.

## Pages in good shape

- **`index.md`** — Clean, complete homepage.
- **`getting-started.md`** — Solid end-to-end tutorial. Fixed: "plcc.plcc" → "spec.plcc".
- **`language-guide/index.md`** — Good overview with PlantUML pipeline diagram. Fixed: "secction" typo.
- **`language-guide/lexical.md`** — Complete and accurate. Fixed: "ID matches" → "IF matches" in example.
- **`language-guide/syntactic.md`** — Solid. Fixed: "Slautation" → "Salutation" in PlantUML diagram.
- **`language-guide/semantic.md`** — Covers the material. Will need updating once issues
  [[091-single-semantic-section]] and [[092-language-as-first-line-of-semantics]] land
  (section header format changes), but accurate for current behavior.
- **`cli/index.md`** — Good overview. Fixed: removed unresolved TODO about grammar memory.
- **`cli/primitives.md`** — Good. One remaining TODO: how to obtain LL1_JSON for `plcc-trees`.

## Pages needing follow-up

- **`cli/orchestrators.md`** — One remaining TODO about how to suppress interactive mode.
  Will also need updating once issues [[084-no-banner-default]], [[089-grammar-to-spec-rename]],
  [[091-single-semantic-section]], and [[093-incremental-parsing-repl]] land
  (`--tool` flag removed, `-g` → `-s`, interactive mode behavior changes).

- **`language-guide/examples.md`** — Uses old syntax throughout (`% subtract Python`,
  `-g subtract.plcc`, `--tool=subtract`, `grammar.plcc`). Several TODOs on unverified
  output formats. Needs a full pass once the spec rename and semantic section issues land.

## Placeholder pages (content not yet written)

- **`instructor-guide/index.md`**
- **`instructor-guide/evaluating.md`**
- **`instructor-guide/adopting.md`**
