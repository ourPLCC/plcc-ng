# Design: v1.0 Readiness Criteria (issue #112)

## Purpose

Issue #112 asks what "done enough for v1.0" means for plcc-ng and to
work toward it. Every prerequisite issue on the roadmap (#130,
#134–#138, #140) is already done, making #112 the last open item.
This design defines the v1.0 criteria, records the audit of the repo
against them, and produces a durable artifact so the decision doesn't
need to be re-litigated.

The actual release cutover (forcing a `v1.0.0` tag past
`major_on_zero`, running the release SOP, updating
`docs/whats-new.md`'s placeholder date) is out of scope for this
design and remains open work under issue #112.

## Criteria

Adopted verbatim from the candidates listed in
`dev-docs/issues/112-first-major-release.md`:

1. No known correctness bugs in the core pipeline (scan → parse → emit)
2. Stable CLI surface (command names, flags, output formats) we are
   willing to maintain
3. Stable spec syntax — no planned breaking changes to the `.plcc`
   file format
4. End-user documentation covers the full workflow (install,
   quickstart, language guide, CLI reference)
5. Release SOP (`dev-docs/release-sop.md`) is complete and tested
6. CI is green and the test suite covers the happy path end-to-end
   for at least Python and Java
7. All four emitters (Python, Java, Haskell, JavaScript) are v1
   supported — no experimental tier

## Audit findings

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | No known correctness bugs | Met | No open bug-type issues (only #112 is open). Last four `fix:` commits are release-tooling, not pipeline correctness. |
| 2 | Stable CLI surface | Met (declared) | Project owner declares `plcc-scan`, `plcc-parse`, `plcc-rep`, `plcc-diagram` stable: command names, flags, and output formats are committed to; changes require a major version bump. |
| 3 | Stable spec syntax | Met (declared) | Project owner declares the plcc-ng specification language's syntax and semantics stable: no planned breaking changes to the `.plcc` file format. |
| 4 | End-user docs | Met | `docs/installation.md`, `docs/quick-start.md`, `docs/language-guide/`, `docs/cli/`, `docs/migration.md` all present and cover the full workflow. |
| 5 | Release SOP | Met | `dev-docs/release-sop.md` written (200 lines); roadmap shows issue #130 ("write the SOP... exercise it on a pre-1.0 release") done. |
| 6 | CI green + Python/Java e2e | Met | Recent CI runs on `main` green (Docs, Release workflows completed/success). `tests/bats/e2e/happy-path.bats` covers Python; `tests/bats/e2e/languages-java.bats` covers Java. |
| 7 | Four emitters stable, no experimental tier | Met (declared) | Project owner declares the Python, Java, JavaScript, and Haskell language extensions stable. Each has a doc page under `docs/language-guide/languages/`; the only "experimental" hit in `docs/` is in an unrelated internal design-spec doc, not user-facing docs. |

All seven criteria are met as of this writing.

## Deliverable

A new document, `dev-docs/v1.0-criteria.md`, recording:

- The seven criteria (adopted from issue #112)
- Their status and evidence, per the audit table above
- The three stability declarations, attributed and dated
- A "Remaining before v1.0.0 ships" section listing the release
  cutover work that stays open under issue #112:
  - Flip `major_on_zero` in `pyproject.toml` (or otherwise force a
    `1.0.0` tag)
  - Cut the release per `dev-docs/release-sop.md`
  - Update `docs/whats-new.md`'s `2026-07-XX` placeholder to the
    actual release date
  - Run `bin/release/verify.bash` against the new tag

## Relationship to issue #112

This document does not close issue #112. It records that the
"agree on v1.0 criteria" half of #112 is done; the "cut the release"
half remains open, tracked by the same issue's existing notes.
`dev-docs/issues/112-first-major-release.md` gets a short pointer
added to its Notes section referencing the new criteria doc, so
future readers don't have to re-derive that the criteria question is
settled.

## Out of scope

- Forcing `major_on_zero` / the mechanics of the v1.0.0 tag itself
- Running the release
- Updating `docs/whats-new.md`'s placeholder date
- Any further emitter or CLI feature work — this design only records
  the stability decision already made
