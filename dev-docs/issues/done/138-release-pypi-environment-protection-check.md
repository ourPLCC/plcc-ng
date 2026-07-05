# 138 - Confirm the `pypi` GitHub Environment has an approval gate

**Type:** chore
**Date:** 2026-07-03

## Description

`.github/workflows/release.yml`'s `publish` job runs under `environment: pypi`. GitHub Environments can require reviewer approval before a job runs, but whether that protection rule is actually configured for `pypi` can't be confirmed by reading the repo — it's a repository setting, not something in version control.

Today, once conventional commits land on `main`, the entire pipeline (tag, changelog, GitHub release, PyPI publish) runs with no other human checkpoint before the package reaches real PyPI, unless the `pypi` environment has required reviewers configured.

## Decision

Verified 2026-07-05 via the GitHub environments API (the repo is
public, so the configuration is anonymously readable):

- The `pypi` environment has **no required reviewers** and no wait
  timer — its only protection rule is a deployment branch policy.
- That branch policy already restricts the environment to the `main`
  branch and `v*.*.*` tags, so the issue-134 follow-up below is in
  place: a dispatch from any other branch can never reach the publish
  job.

**Decision: keep the pipeline ungated and document the absence of an
approval gate as intentional.** The automation is the point of the
release design: TestPyPI publish + smoke test run before the real PyPI
upload, and the branch policy pins the publish job to `main`. The
configuration and rationale are now recorded in the release SOP
(`dev-docs/release-sop.md`, "The `pypi` environment").

## Notes

- Found while writing the release SOP (issue 130).
- Action: check GitHub repo Settings → Environments → `pypi` for required reviewers / protection rules. If none exist, decide whether to add one (trades release speed for a manual gate) or document that the lack of a gate is intentional.
- This is a verification/decision task, not necessarily a code change.
- Follow-up from issue 134: the same Settings → Environments → `pypi` page
  also supports deployment branch policies. Restricting the `pypi`
  environment to `main` would enforce the release SOP's "dispatch from
  `main` only" guidance in settings rather than prose — a dispatch from any
  other branch (which runs that branch's copy of release.yml) could then
  never reach the publish job. Worth configuring while checking the
  approval gate.
