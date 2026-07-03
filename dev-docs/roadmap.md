# Roadmap

8 open issues as of 2026-07-03.

## Open Issues

### Docs

- **[#130](issues/130-release-sop.md) — Write the release SOP**
  `dev-docs/release-sop.md` is empty; needed before v1.0.

### Fixes

- **[#135](issues/135-release-pypi-publish-skip-existing.md) — Real PyPI publish step lacks skip-existing, unlike TestPyPI**
  The "Publish to PyPI" step has no `skip-existing: true`, so a rerun against an already-published version fails hard instead of skipping.

- **[#140](issues/140-release-smoke-test-testpypi-propagation.md) — Smoke test races TestPyPI index propagation**
  The post-upload `pip install` from TestPyPI can run before the index has propagated, intermittently failing the `publish` job even though the upload succeeded.

### Features

- **[#134](issues/134-release-pypi-publish-failure-recovery.md) — No recovery path when PyPI publish fails after tagging**
  Once semantic-release tags a version, a subsequent publish failure can't be retried — reruns find no new releasable commits and skip the publish job.

- **[#112](issues/112-first-major-release.md) — Prepare for first major release (v1.0.0)**
  Define v1.0 criteria and coordinate the remaining pre-1.0 work (docs 130, release-pipeline gaps 134-138 and 140).

### Refactors

- **[#136](issues/136-release-changelog-vcs-release-divergence.md) — GitHub Release notes and CHANGELOG.md generated from different sources**
  `vcs_release: false` means release notes come from `gh release create --generate-notes` (PR-based) while `CHANGELOG.md` comes from semantic-release (commit-based) — the two can diverge.

### Tests

- **[#137](issues/137-release-smoke-test-emitter-coverage.md) — Release smoke test only exercises one trivial fixture, no emitters**
  The post-publish smoke test never invokes any of the four emitters, so a broken published package for Java/Haskell/JS wouldn't be caught.

### Chores

- **[#138](issues/138-release-pypi-environment-protection-check.md) — Confirm the `pypi` GitHub Environment has an approval gate**
  Whether the `pypi` environment requires reviewer approval before publish can't be confirmed from the repo; needs a settings check.
