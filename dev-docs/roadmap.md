# Roadmap

9 open issues as of 2026-07-03.

## Open Issues

### Docs

- **[#130](issues/130-release-sop.md) — Write the release SOP**
  `dev-docs/release-sop.md` is empty; needed before v1.0.

### Fixes

- **[#133](issues/133-release-docs-deploy-decoupled-from-pypi-publish.md) — Docs deploy is not gated on PyPI publish success**
  `docs.yml` deploys versioned docs on `release: published`, which fires before the `publish` job finishes — a version can show as `latest` in the docs before, or even if, it reaches PyPI.

- **[#135](issues/135-release-pypi-publish-skip-existing.md) — Real PyPI publish step lacks skip-existing, unlike TestPyPI**
  The "Publish to PyPI" step has no `skip-existing: true`, so a rerun against an already-published version fails hard instead of skipping.

### Features

- **[#131](issues/131-haskell-language-error-not-accessible-from-user-code.md) — Make `LanguageError` accessible from Haskell user code**
  `LanguageError` is defined in generated `Main.hs` but unreachable from user semantics modules; needs a dedicated runtime module.

- **[#134](issues/134-release-pypi-publish-failure-recovery.md) — No recovery path when PyPI publish fails after tagging**
  Once semantic-release tags a version, a subsequent publish failure can't be retried — reruns find no new releasable commits and skip the publish job.

- **[#112](issues/112-first-major-release.md) — Prepare for first major release (v1.0.0)**
  Define v1.0 criteria and coordinate the remaining pre-1.0 work (docs 128, 130, feature 131, release-pipeline gaps 133-138).

### Refactors

- **[#136](issues/136-release-changelog-vcs-release-divergence.md) — GitHub Release notes and CHANGELOG.md generated from different sources**
  `vcs_release: false` means release notes come from `gh release create --generate-notes` (PR-based) while `CHANGELOG.md` comes from semantic-release (commit-based) — the two can diverge.

### Tests

- **[#137](issues/137-release-smoke-test-emitter-coverage.md) — Release smoke test only exercises one trivial fixture, no emitters**
  The post-publish smoke test never invokes any of the four emitters, so a broken published package for Java/Haskell/JS wouldn't be caught.

### Chores

- **[#138](issues/138-release-pypi-environment-protection-check.md) — Confirm the `pypi` GitHub Environment has an approval gate**
  Whether the `pypi` environment requires reviewer approval before publish can't be confirmed from the repo; needs a settings check.
