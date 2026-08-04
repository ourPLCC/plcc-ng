# 184 - Follow-ups left open by the docs example tier

**Type:** test
**Date:** 2026-08-04

## Description

Six observations from the reviews of #181/#182/#183 that were judged
non-blocking and deliberately not fixed on that branch. None weakens detection;
they are diagnostics and test hygiene. Recorded here so they survive — they were
previously only in a scratch ledger.

Two review findings that *did* weaken something were fixed on that branch rather
than deferred here:

- `docs-tests.yml`'s `paths:` filter omitted `mkdocs-strict.yml` and
  `bin/docs/build.bash`, so the strict gate could not be triggered by changes to
  its own inputs.
- `UNCOVERED` was a page-level allowlist that skipped every fence on a listed
  page, so a new runnable specification added to an already-exempt page landed
  unguarded — and `CONTRIBUTING.md` claimed otherwise. Raised by a Copilot review
  of the PR. The allowlist now records a fence count per page, so an exemption
  covers only the fences that existed when it was written.

### 1. The strict gate re-enumerates the plugin list

`mkdocs-strict.yml` uses `INHERIT: mkdocs.yml` but restates `plugins` to drop
`kroki`, and `INHERIT` replaces lists rather than merging them. So a plugin added
to `mkdocs.yml` never reaches the strict gate, and the gate builds a different
site than the deploy does. Nothing detects the divergence.

Options: a pointer comment in `mkdocs.yml:27` naming the sibling file, or a test
asserting `strict.plugins == mkdocs.plugins - {kroki}`. The second is better and
is roughly the same shape as the `UNCOVERED` guard already in
`tests/docs/example_block_test.py`.

### 2. Whitespace-only drift produces a visually identical diff

`tests/docs/example_block_test.py`'s failure output uses
`difflib.unified_diff`, which emits no `\ No newline at end of file` marker and
does not escape trailing spaces. Drift consisting only of a trailing space, or of
a fixture losing its final newline, renders as two apparently identical lines.
The test still fails correctly — only the diagnostic is weak. `repr`-ing the
differing lines, or noting "difference is whitespace-only" when
`documented.split() == tested.split()`, would close it.

### 3. Two extractor error branches are untested

`extract_tabbed_block`'s "is not followed by a fenced block" (both raise sites)
and "has an under-indented line" have no test. Deleting either guard would not
fail the suite. Impact is bounded: both only upgrade a would-be mismatch into a
clearer message, so their loss degrades diagnostics rather than detection.

### 4. The tab-selection test asserts only one direction

`test_extract_selects_the_named_tab` extracts the *last* tab from a two-tab
input; it never asserts that extracting the earlier tab stops before the adjacent
one. An over-running extractor would still be caught today (for the last tab it
runs off the end and raises), so this is a missing direct pin rather than an
uncovered failure mode. One extra assertion closes it.

### 5. Focused runs of the docs test emit coverage noise

`bin/test/units.bash tests/docs/example_block_test.py` prints `CoverageWarning`
plus `WARNING: Failed to generate report: No data to report.` — it is the repo's
first test file that imports no `plcc` code, and `pdm test` adds `--cov=plcc`.
The full-tier run is clean, and `bin/test/docs.bash` avoids it by calling
`pdm run pytest` directly. Any fix touches coverage configuration, so it was left
alone.

### 6. `bin/test/docs.bash` fail-fast hides the second half

It runs under `set -euo pipefail`, so a pytest failure aborts before bats runs
and you cannot see both halves' results in one invocation. This matches
`functional.bash`, which chains all five tiers the same way and stops at the
first failure, so it was deferred rather than treated as a defect. If it is ever
changed, collect both exit codes and report at the end rather than dropping
`set -e`.

## Notes

Also noticed, unrelated to the tier itself: the plan
`dev-docs/plans/2026-08-03-181-182-doc-example-drift.md` lists
`bin/test/all.bash` in Task 5's Files block, contradicting its own File Structure
table, which correctly says `all.bash` inherits the tier through
`functional.bash` and is not touched. Historical document, cosmetic.

Context: `dev-docs/specs/2026-08-03-doc-example-drift-design.md`, and the closed
issues `dev-docs/issues/done/18{1,2,3}-*.md`.

The design's own stated limitation is worth keeping in view alongside these: the
tier executes examples, so it cannot check prose claims *about* behaviour. Two
false claims of that kind were found and fixed during the branch (one about
`--verbose-format=json` hiding stray output, one about an output-only comparison
passing for a broken example), and neither was caught by any test — both by
review.
