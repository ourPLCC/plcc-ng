# 138 - Confirm the `pypi` GitHub Environment has an approval gate

**Type:** chore
**Date:** 2026-07-03

## Description

`.github/workflows/release.yml`'s `publish` job runs under `environment: pypi`. GitHub Environments can require reviewer approval before a job runs, but whether that protection rule is actually configured for `pypi` can't be confirmed by reading the repo — it's a repository setting, not something in version control.

Today, once conventional commits land on `main`, the entire pipeline (tag, changelog, GitHub release, PyPI publish) runs with no other human checkpoint before the package reaches real PyPI, unless the `pypi` environment has required reviewers configured.

## Notes

- Found while writing the release SOP (issue 130).
- Action: check GitHub repo Settings → Environments → `pypi` for required reviewers / protection rules. If none exist, decide whether to add one (trades release speed for a manual gate) or document that the lack of a gate is intentional.
- This is a verification/decision task, not necessarily a code change.
