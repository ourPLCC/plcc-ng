# 141 - whats-new-user-release-notes

**Type:** feat
**Date:** 2026-07-04

## Description

Add a user-facing "What's New" page: hand-curated (AI-drafted,
human-reviewed) release notes that tell users what changed, why it
matters to them, and where to learn more — distinct from the
developer-facing CHANGELOG.md and GitHub Releases.

Agreed design (Part 2 of
[the issue-136 design spec](../../specs/2026-07-04-136-release-notes-unification-design.md)):

- `docs/whats-new.md`, in the mkdocs nav near the top. Newest entry
  first. Each entry: date, version range covered, prose sections, links
  into the user docs. An HTML comment marker
  (`<!-- last-covered: vX.Y.Z -->`) records where the next drafting
  session picks up.
- Cadence: milestone-driven with a quarterly floor — a new entry when a
  roadmap phase or significant batch of work completes, or when three
  months elapse, whichever comes first.
- Process: AI drafts from CHANGELOG.md (since the marker), design specs,
  and closed issues in that range; a human reviews and edits before
  merge. Review is the quality gate.
- First entry: timed with the approach to v1.0 — a highlights tour of
  PLCC-ng, especially relative to PLCC, linking to `docs/migration.md`
  rather than duplicating it.
- Once the page exists, the changelog page (`docs/changelog.md`) leaves
  the user docs site and nav (`mkdocs.yml`); the developer-facing
  changelog is published on the dev-docs site (`mkdocs-dev.yml`)
  instead.

## Notes

- Split out of issue 136 during brainstorming (2026-07-04): the
  per-release narrative unification landed there; this issue owns the
  user-facing narrative.
- Towncrier (per-PR news fragments) was considered and rejected for
  now — wrong cost/benefit at release-per-merge cadence; revisit if the
  milestone cadence proves too coarse.
