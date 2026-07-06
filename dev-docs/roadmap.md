# Roadmap

## Path to v1.0

Recommended order. Fix release-pipeline reliability first, then settle design
decisions, then broaden verification, then document the result and ship.
Completed items are checked off (and stay listed) so this section tracks
progress toward the milestone; the section retires when v1.0 ships.

1. [x] [#140](issues/done/140-release-smoke-test-testpypi-propagation.md) — the propagation race is actively breaking releases; retry/poll before installing.
2. [x] [#135](issues/done/135-release-pypi-publish-skip-existing.md) — one-line `skip-existing` fix; prerequisite for any rerun/retry story (could ride with #140).
3. [x] [#134](issues/done/134-release-pypi-publish-failure-recovery.md) — recovery path for tagged-but-not-published; builds on #135, may reduce to documenting "Re-run failed jobs" plus a republish dispatch input.
4. [x] [#136](issues/done/136-release-changelog-vcs-release-divergence.md) — resolved: GitHub Release notes now come from the tag's CHANGELOG.md section (`--notes-file`); `vcs_release` stays false; SOP updated.
5. [x] [#138](issues/done/138-release-pypi-environment-protection-check.md) — settings check + decision; an SOP input, doable any time.
6. [x] [#137](issues/done/137-release-smoke-test-emitter-coverage.md) — extend the smoke test to all four emitters; defines post-release verification for the SOP.
7. [x] [#130](issues/done/130-release-sop.md) — write the SOP once the pipeline is stable; exercise it on a pre-1.0 release.
8. [ ] [#112](issues/112-first-major-release.md) — agree on v1.0 criteria and cut the release.

## Open Issues

### Fixes

- **[#142](issues/142-verify-pypi-simple-index-race.md) — verify.bash PyPI check races the simple index**
  Check 1 polls the JSON API, but pip installs from the simple index, which
  lags it; the check passes while the install step fails.

### Features

- **[#112](issues/112-first-major-release.md) — Prepare for first major release (v1.0.0)**
  Define v1.0 criteria and coordinate the remaining pre-1.0 work (docs 130, release-pipeline gaps 134-138 and 140).
- **[#141](issues/141-whats-new-user-release-notes.md) — Add a user-facing "What's New" page**
  Milestone-cadence, AI-drafted/human-reviewed release notes in the user
  docs; moves the changelog page to the dev-docs site. First entry
  targets v1.0. Design in the issue-136 spec (Part 2).
