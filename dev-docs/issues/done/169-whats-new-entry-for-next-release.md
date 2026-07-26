# 169 - Add whats-new.md entry for the next release before merging this branch

**Type:** docs
**Date:** 2026-07-24

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

`docs/whats-new.md` has a `<!-- last-covered: v1.0.0 -->` marker and a
single dated entry for the v1.0.0 release. This branch
(`worktree-run-contract-impl`) has accumulated a full release's worth of
user-facing changes since then — several of them `fix!`/`BREAKING CHANGE`
commits (issues #162/#165's `_run()` return-a-string contract; #164's
alt-name case fix; likely #168's bare-name field derivation fix once
implemented) — with no corresponding `whats-new.md` entry.

Add a new dated section to `docs/whats-new.md` covering everything merged
on this branch since v1.0.0, and move the `last-covered` marker forward,
before this branch is merged to `main`.

## Steps to Reproduce

(Not applicable — this is a docs gap, not a bug.)

## Notes

Do this once for the whole branch, not per-issue — it belongs in the
branch's final docs pass, after all the branch's other issues
(#162, #164, #165, #168, ...) are closed, so the entry can summarize the
complete, accurate set of changes rather than being written piecemeal and
going stale.

Survey with `git log --oneline main..HEAD` (or equivalent once other
issues on the branch are closed) to enumerate what actually shipped.
Follow the existing v1.0.0 entry's structure/tone in `whats-new.md`.
