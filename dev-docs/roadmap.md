# Roadmap

## Path to v1.0

Recommended order. Fix release-pipeline reliability first, then settle design
decisions, then broaden verification, then document the result and ship.
Completed items are checked off (and stay listed) so this section tracks
progress toward the milestone; the section retires when v1.0 ships.

1. [x] [#140](issues/done/140-release-smoke-test-testpypi-propagation.md) — the propagation race is actively breaking releases; retry/poll before installing.
2. [ ] [#135](issues/135-release-pypi-publish-skip-existing.md) — one-line `skip-existing` fix; prerequisite for any rerun/retry story (could ride with #140).
3. [ ] [#134](issues/134-release-pypi-publish-failure-recovery.md) — recovery path for tagged-but-not-published; builds on #135, may reduce to documenting "Re-run failed jobs" plus a republish dispatch input.
4. [ ] [#136](issues/136-release-changelog-vcs-release-divergence.md) — decide `vcs_release` vs. PR-based notes; the answer changes what the SOP documents.
5. [ ] [#138](issues/138-release-pypi-environment-protection-check.md) — settings check + decision; an SOP input, doable any time.
6. [ ] [#137](issues/137-release-smoke-test-emitter-coverage.md) — extend the smoke test to all four emitters; defines post-release verification for the SOP.
7. [ ] [#130](issues/130-release-sop.md) — write the SOP once the pipeline is stable; exercise it on a pre-1.0 release.
8. [ ] [#112](issues/112-first-major-release.md) — agree on v1.0 criteria and cut the release.

## Open Issues

### Docs

- **[#130](issues/130-release-sop.md) — Write the release SOP**
  `dev-docs/release-sop.md` is empty; needed before v1.0.

### Fixes

- **[#135](issues/135-release-pypi-publish-skip-existing.md) — Real PyPI publish step lacks skip-existing, unlike TestPyPI**
  The "Publish to PyPI" step has no `skip-existing: true`, so a rerun against an already-published version fails hard instead of skipping.

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
