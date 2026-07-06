# 151 - migrate-superpowers-docs-to-dev-docs

**Type:** docs
**Date:** 2026-07-06

## Description

`docs/superpowers/specs/` (50 files) and `docs/superpowers/plans/` (51
files) hold the same kind of per-issue brainstorming design docs and
implementation plans that `dev-docs/specs/` and `dev-docs/plans/` already
hold — two parallel locations for the same artifact type, populated by
different sessions guessing at the convention. `docs/superpowers/` should
not exist going forward; everything belongs under `dev-docs/`.

Migrate the contents of `docs/superpowers/specs/` into `dev-docs/specs/`
and `docs/superpowers/plans/` into `dev-docs/plans/` (via `git mv`, so
history is preserved), fixing each moved file's internal relative links
(issue references, cross-references to other specs/plans) for its new
depth, then remove the now-empty `docs/superpowers/` directory.

## Notes

- Discovered while writing issue 150's design doc: it was first written
  to `docs/superpowers/specs/` by copy-pattern-matching an existing file
  there, then corrected back to `dev-docs/specs/` once this duplication
  was noticed.
- Check whether anything (mkdocs nav, a skill, tooling) references
  `docs/superpowers/` by path before deleting it, so nothing 404s.
