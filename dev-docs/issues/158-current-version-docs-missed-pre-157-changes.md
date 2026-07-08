# 158 - current-version-docs-missed-pre-157-changes

**Type:** chore
**Date:** 2026-07-08

<!--
Classify by user-facing impact, not by whether something was "broken".
`fix` and `feat` bump the release version (see [tool.semantic_release]
in pyproject.toml); reserve them for changes to the shipped package
(src/). A bug in a test, script, or CI workflow (bin/, tests/,
.github/) is still a bug, but it's not user-facing — classify it
`test` or `chore` instead so it doesn't spin the version. `docs` is for
documentation content, and never bumps the version either way.
-->

## Description

Issue [#157](done/157-docs-only-changes-never-reach-current-version-docs.md)
made docs-only pushes to `main` sync forward into the current live
version (`1.0`/`latest`) from here on, but it doesn't backfill anything
— it only reruns `mike deploy <current>` on pushes that happen *after*
the workflow change landed (merged in commit `42f2070b`, 2026-07-08
00:41:54 UTC).

`v1.0.0` was tagged 2026-07-06 16:31:07 UTC. Between the tag and the
157 fix landing, at least one docs-only change merged to `main` and
was never synced to the `1.0`/`latest` live docs — it only ever
reached the `dev` preview:

- `de4b31fc` "docs(headings): standardize section headings to sentence
  case" (2026-07-07 22:36:50 UTC) — touches 45 files under `docs/`.

Confirmed directly on `gh-pages`: `1.0/acknowledgments/index.html`
still reads "Institutions &amp; Funding" / "Open-Source Dependencies"
(title case), while `dev/acknowledgments/index.html` already has the
fixed "Institutions &amp; funding" / "Open-source dependencies"
(sentence case).

## Notes

- One-time backfill: run `mike deploy 1.0` (or whatever `mike list
  latest -j` currently reports) from a checkout of `main` to push the
  already-merged docs content into the live version, same as the
  automated step 157 added now does per-push.
- Worth double-checking for other docs-only commits in the same
  `v1.0.0..42f2070b` window beyond `de4b31fc` before running the
  backfill, in case more than one change needs syncing:
  `git log --oneline v1.0.0..42f2070b -- docs/`.
- Not a recurring problem — 157 closes the gap for everything after
  `42f2070b`. This is purely about the changes stranded in the gap
  before that fix existed.
