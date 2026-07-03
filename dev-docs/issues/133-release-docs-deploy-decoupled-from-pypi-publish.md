# 133 - Docs deploy is not gated on PyPI publish success

**Type:** fix
**Date:** 2026-07-03

## Description

In `.github/workflows/release.yml`, the `semantic-release` job creates the GitHub Release (`gh release create`) before the `publish` job (build wheel, publish TestPyPI, smoke test, publish real PyPI) has run or succeeded. `docs.yml` deploys versioned docs on the `release: published` event, which fires as soon as the release is created — independent of whether `publish` later succeeds.

This means the docs site can show a version as `latest` (via `mike set-default --push latest`) before, or even if, that version never actually reaches PyPI. A user following the docs could try to install a version that isn't installable yet, or ever, if publish fails.

## Notes

- Found while writing the release SOP (issue 130) and reviewing `release.yml` / `docs.yml`.
- Possible fix: make docs deploy depend on `publish` succeeding, e.g. have the docs workflow triggered from (or gated on) the `publish` job's outcome rather than purely on `release: published`.
- Related to issue 134 (no recovery path if publish fails) — the two probably want the same design pass.
