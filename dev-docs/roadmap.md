# Roadmap

8 open issues as of 2026-06-20. Grouped by theme; within a theme the order reflects dependencies.

## Phase 1 — Docs: CLI reference (implement the #100 decision)

The classification and doc structure were decided in #100. This phase implements that decision.

| # | Issue | Notes |
| --- | --- | --- |
| [100](issues/100-docs-cli-command-classification.md) | Implement CLI command classification | Restructure `docs/cli/` into per-group pages with an overview |

## Phase 2 — Docs: quick wins (independent, any order)

| # | Issue | Notes |
| --- | --- | --- |
| [081](issues/081-docs-remove-plcc-make-from-examples.md) | Remove `plcc-make` from examples | `examples.md` still tells users to run it directly |
| [101](issues/101-docs-acknowledgments-page.md) | Acknowledgments page | Credit contributors, institutions, and key dependencies |
| [071](issues/071-docs-upgrade-guide.md) | Upgrade guide | New page near the install docs |
| [072](issues/072-docs-pin-version.md) | Version-pinning instructions | Pair with 071 — same page or adjacent |
| [102](issues/102-docs-migration-from-plcc.md) | Migration guide from PLCC to PLCC-ng | Pair with 071/072 — all belong in the same "getting/staying on PLCC-ng" cluster |

## Phase 3 — Docs: site features

Framework and tooling decisions are resolved (MkDocs Material + PlantUML via Kroki).

| # | Issue | Notes |
| --- | --- | --- |
| [080](issues/080-docs-tabbed-code-blocks.md) | Tabbed code blocks for language variants | MkDocs Material content tabs; enable `content.tabs` feature |

## Phase 4 — Feature: new language emitter

| # | Issue | Notes |
| --- | --- | --- |
| [066](issues/066-extend-to-another-language.md) | Extend to one more language | Large, independent of all docs work; candidates: C#, TypeScript, Go, Kotlin |
