# 157 - docs-only-changes-never-reach-current-version-docs

**Type:** chore
**Date:** 2026-07-07

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

Our published docs are versioned with `mike` (see
[.github/workflows/docs.yml](../../.github/workflows/docs.yml)):

- Every push to `main` redeploys the `dev` alias.
- Only a GitHub `release` event redeploys a version alias (e.g. `1.0`)
  and moves `latest`.

Since `docs`-only commits never bump the version (by design — see the
classification note in [issues/TEMPLATE.md](../TEMPLATE.md)), a
docs-only PR merged to `main` updates `dev` but never touches `1.0` or
`latest`. That was fine as an assumption when docs shipped in lockstep
with the release that introduced them, but in practice docs regularly
lag behind — we fix or clarify documentation for features that already
shipped, in PRs with no code change. Right now those fixes are
invisible to anyone pinned to `1.0`/`latest` until we happen to cut a
new release for an unrelated reason.

Discovered while discussing issue #147 (heading capitalization): the
fix merged to `main` and appeared on the `dev` docs preview, but users
on the `1.0` docs won't see it until the next release.

## Notes

Proposed direction: add a workflow step, triggered on push to `main`
with a `docs/` path filter, that looks up whatever version `mike list`
currently reports as newest (not `dev`) and re-runs `mike deploy
<that-version>` — no `--update-aliases`, so it doesn't create a new
version or move `latest`, just refreshes that version's already-live
content.

Open question worth resolving before implementing: should this
sync unconditionally on every docs-only merge, or only for changes
judged worth backporting (e.g. broken instructions, wrong commands)
versus purely cosmetic changes (e.g. heading capitalization) that
don't need to disturb an already-published snapshot? Auto-syncing
everything is simplest but means a version's docs silently drift from
"what shipped with that release" toward "whatever main says now," even
for non-functional edits.
