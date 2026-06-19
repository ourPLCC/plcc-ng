# Roadmap

14 open issues as of 2026-06-19. Grouped by theme; within a theme the order reflects dependencies.

## Phase 1 — Docs: structural decisions (resolve first)

These issues ask a question or make an architectural call that blocks or shapes downstream work.

| # | Issue | Why it blocks |
|---|---|---|
| [100](issues/100-docs-cli-command-classification.md) | Reconsider CLI command classification | Determines how all CLI reference pages are organized; supersedes 083 |
| [076](issues/076-docs-home-install-redundancy.md) | Home page install redundancy | Determines whether a standalone Install page exists or install lives only in the quickstart |
| [077](issues/077-docs-licensing.md) | Should the docs include a licensing page? | Policy decision that 078 depends on |
| [079](issues/079-docs-diagrams.md) | Diagrams: Mermaid vs PlantUML | Tooling choice needed before any diagram content is added (080 also depends on framework) |

## Phase 2 — Docs: quick wins (independent, any order)

Each of these can be done without waiting on Phase 1 decisions.

| # | Issue | Notes |
|---|---|---|
| [099](issues/099-docs-link-to-source.md) | Add link to source repo | Likely a one-line config change in the doc framework |
| [073](issues/073-docs-java-jdk-prerequisite.md) | Java JDK as optional prerequisite | Add to the prerequisites section |
| [078](issues/078-docs-content-license.md) | Content license | Finalize once 077 is resolved; add notice + LICENSE coverage |
| [071](issues/071-docs-upgrade-guide.md) | Upgrade guide | New page near the install docs |
| [072](issues/072-docs-pin-version.md) | Version-pinning instructions | Pair with 071 — same page or adjacent |

## Phase 3 — Docs: quickstart and examples (sequential)

074 must land before the broader audit in 081.

| # | Issue | Notes |
|---|---|---|
| [074](issues/074-docs-simplify-quickstart.md) | Simplify quickstart and fix sample output | Remove `plcc-make` step; re-run for real output |
| [081](issues/081-docs-remove-plcc-make-from-examples.md) | Remove `plcc-make` from all other examples | Audit the rest of the docs after quickstart is fixed |

## Phase 4 — Docs: CLI reference (depends on Phase 1)

| # | Issue | Notes |
|---|---|---|
| [083](issues/083-fix-plcc-diagram-misclassified.md) | Reclassify `plcc-diagram` as Level 2 | May be absorbed into 100 depending on how classification is resolved |

## Phase 5 — Docs: site features (depends on framework/tooling decisions)

| # | Issue | Notes |
|---|---|---|
| [080](issues/080-docs-tabbed-code-blocks.md) | Tabbed code blocks for language variants | Implementation depends on the doc framework in use |

## Phase 6 — Feature: new language emitter

| # | Issue | Notes |
|---|---|---|
| [066](issues/066-extend-to-another-language.md) | Extend to one more language | Large, independent of all docs work; candidates: C#, TypeScript, Go, Kotlin |
