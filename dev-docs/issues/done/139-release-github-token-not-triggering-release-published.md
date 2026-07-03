# 139 - GITHUB_TOKEN-created GitHub Releases may never trigger docs.yml's release:published listener

**Type:** fix
**Date:** 2026-07-03

## Description

`.github/workflows/release.yml`'s `create-release` job runs `gh release
create` authenticated with `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}`. GitHub
Actions documents that events created by the automatic `GITHUB_TOKEN`
(other than `workflow_dispatch`/`repository_dispatch`) do not start new
workflow runs, to prevent recursive triggering. If that applies to
`release: published` the way it does to `push`/`pull_request`, then
`docs.yml`'s "Deploy versioned docs (on release)" job — which triggers on
`release: published` — may never fire on the automated release path,
regardless of timing/ordering.

This would make the fix in issue 133 (gating the GitHub Release on
`publish` job success) necessary but not sufficient: the release event
would be correctly delayed, but still never reach `docs.yml`.

## Steps to Reproduce

1. Check `origin/gh-pages`'s `versions.json` — as of 2026-07-03 it
   contains only a single `dev` entry, despite 60+ tagged releases
   (`v0.6.0` through `v0.64.0` in `git tag`). No versioned docs entry or
   `latest` alias has ever appeared, which is consistent with
   `docs.yml`'s release-triggered job never having run.
2. Confirm directly (not yet done) by checking the Actions run history
   for `docs.yml` and filtering for runs with `event: release` — if none
   exist across all past releases, that confirms the token issue rather
   than some other cause.

## Notes

- Found while implementing issue 133's fix; a whole-branch code review
  surfaced the `GITHUB_TOKEN` recursion-prevention behavior as a likely
  explanation for the empty `versions.json`.
- The `GITHUB_TOKEN` used in the `create-release` job step is unchanged
  from before issue 133's fix (only the job it lives in moved) — this is
  a pre-existing condition, not a regression.
- Possible fix: authenticate the `gh release create` step with the
  existing GitHub App token (`steps.app-token.outputs.token`, already
  minted in the `semantic-release` job via
  `actions/create-github-app-token@v1`) instead of `GITHUB_TOKEN`, since
  events created by a GitHub App installation token do trigger downstream
  workflows.
- Related to issue 133 (docs deploy ordering) — same code path, adjacent
  bug.
