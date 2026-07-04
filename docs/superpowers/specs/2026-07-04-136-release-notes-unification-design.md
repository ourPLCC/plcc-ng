# Release notes unification (issue 136) — design

**Date:** 2026-07-04
**Issue:** [136 - GitHub Release notes and CHANGELOG.md are generated from different sources](../../../dev-docs/issues/136-release-changelog-vcs-release-divergence.md)

## Problem

Each release currently produces two independently-generated narratives:

- `CHANGELOG.md`, written by python-semantic-release from conventional-commit
  messages (`vcs_release: false` in `pyproject.toml`).
- The GitHub Release body, written by `gh release create --generate-notes` in
  the `create-release` job of `.github/workflows/release.yml`, which builds
  notes from merged PR titles.

These diverge in grouping, granularity, and content. Separately, neither
narrative is written *for users*: both are developer-grade change lists.

## Decisions

Explored during brainstorming (2026-07-04):

1. **Conventional commits remain the source of per-release narratives.**
   PR descriptions and merge commits were rejected as a source. The
   towncrier/news-fragment model (user-authored fragments per PR) was
   considered and rejected for now: it requires rewiring the
   semantic-release job and adds a per-PR authoring habit, for little
   aggregation benefit at this repo's release-per-merge cadence.
2. **`vcs_release: true` was rejected.** It would create the GitHub Release
   in the semantic-release job, before PyPI publish — breaking the
   issue-134 recovery design (release created only after publish succeeds,
   and only if missing), and the republish path skips semantic-release
   entirely so it could never create a missing release.
3. **User-facing release notes become a separate, milestone-cadence
   document** ("What's New"), split out as its own issue. Per-release
   artifacts (CHANGELOG.md, GitHub Releases) are developer-facing.

## Part 1: GitHub Release notes come from CHANGELOG.md (this branch)

### Change

The `create-release` job stops using `--generate-notes`. Instead:

1. A new script `bin/release/extract-changelog.bash <version>` prints the
   CHANGELOG.md section for the given version (the block below its
   second-level `##` heading up to, but excluding, the next second-level
   heading or end of file) to stdout. The version heading line itself is
   excluded — the GitHub Release title already names the tag — and
   leading/trailing blank lines are trimmed. The version argument is given without the leading `v` (e.g.
   `0.65.0`); the script prepends `v` to match headings of the form
   `## v{version} (date)`. If no matching heading exists, the script
   prints a diagnostic to stderr and exits non-zero.
2. The `create-release` job writes that output to a file and runs
   `gh release create` with `--notes-file` (and `--title` as today)
   instead of `--generate-notes`.

### Why this works in both workflow modes

python-semantic-release tags the release commit — the commit that contains
the CHANGELOG.md update. Any checkout at a tag (normal release or the
`workflow_dispatch` republish path) therefore contains that version's
section. Notes come from the repository at the tag, not from
semantic-release's in-run state, so the issue-134 recovery properties are
preserved: the GitHub Release is still created only after PyPI publish
succeeds, only if missing, and republish can recreate it.

### Error handling

If extraction fails (missing or malformed heading), the `create-release`
job fails loudly. No fallback to `--generate-notes`: a silent fallback
would quietly reintroduce the divergence this change removes. Recovery is
the existing republish path after fixing the cause.

### Testing

- Bats command tests for `bin/release/extract-changelog.bash` in
  `tests/bats/commands/`: extracts a middle section, the newest section,
  the oldest section; fails non-zero on an unknown version; output excludes
  neighboring sections' content.
- Safe end-to-end check after merge, per the release SOP: dispatch the
  release workflow with the latest already-published tag and confirm the
  run no-ops green. Extraction runs only when a release is actually
  created (inside the release-missing branch) — tags predating the script
  cannot run it, and republishing them must stay green. The first real
  release after merge verifies the wiring: its GitHub Release body must
  match its CHANGELOG.md section.

### Documentation

`dev-docs/release-sop.md` notes that GitHub Release notes are the
version's CHANGELOG.md section, and that a failed extraction fails the
`create-release` job (recover via republish).

### Out of scope

Existing GitHub Releases are not rewritten; the change applies from the
next release forward.

## Part 2: "What's New" user-facing release notes (new issue, not this branch)

Recorded here as the agreed direction; detailed design happens under its
own issue.

- A hand-curated document, `docs/whats-new.md`, in the mkdocs nav near the
  top. Newest entry first. Each entry: date, version range covered, prose
  on what changed and why it matters to users, links into the user docs.
  An HTML comment marker (`<!-- last-covered: vX.Y.Z -->`) records where
  the next drafting session picks up.
- **Cadence:** milestone-driven with a quarterly floor — a new entry when a
  roadmap phase or significant batch of work completes, or when three
  months elapse, whichever comes first.
- **Process:** AI drafts from CHANGELOG.md (since the marker), design
  specs, and closed issues in that range, linking into user docs; a human
  reviews and edits before merge. Review is the quality gate: user-facing
  claims must be verified.
- **First entry:** timed with the approach to 1.0 — a highlights tour of
  PLCC-ng, especially relative to PLCC, linking to `docs/migration.md`
  rather than duplicating it.
- **CHANGELOG.md moves to the dev-docs site.** Once the What's New page
  exists, the changelog page (`docs/changelog.md`, which includes
  `CHANGELOG.md`) leaves the user docs site and nav (`mkdocs.yml`); the
  developer-facing changelog is published on the dev-docs site
  (`mkdocs-dev.yml`) instead.

This branch's only Part 2 work: create the issue via
`bin/issues/new.bash` with a roadmap entry, capturing the above.

## Implementation shape (Part 1)

1. `bin/release/extract-changelog.bash` + bats command tests (TDD).
2. `release.yml` `create-release` job: extraction step + `--notes-file`.
3. `release-sop.md` update.
4. New issue for Part 2 (What's New doc) + roadmap entry.
5. Close issue 136 via `bin/issues/close.bash` as the final commit.
