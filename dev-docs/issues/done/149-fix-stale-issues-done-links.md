# 149 - Fix stale issues/NNN links that should point to issues/done/

**Type:** docs
**Date:** 2026-07-06

## Description

~23 links in `dev-docs/specs/*.md` and `dev-docs/v1.0-criteria.md`
point at `issues/NNN-*.md` for issues that have since closed and moved
to `issues/done/NNN-*.md`. They 404 when clicked on GitHub — this is
independent of the mkdocs build (#148); it's broken regardless of
whether these files are ever rendered by mkdocs.

Also two related depth bugs turned up in the same investigation:
`dev-docs/issues/done/018-ctrl-d-exit-missing-newline.md` and
`dev-docs/issues/done/025-interactive-first-line-attempt-before-continuation.md`
link to a sibling closed issue via `done/NNN-*.md`, even though both
files already live inside `issues/done/` themselves (the correct link
is the bare sibling filename). And
`dev-docs/issues/done/146-cut-v1.0.0-release.md` links to
`../v1.0-criteria.md`, one `../` short now that the file is one
directory level deeper than when it was written.

The full file-by-file list of affected links (16 spec files, plus
`v1.0-criteria.md`, plus the 3 depth-bug files) is captured in
`docs/superpowers/specs/2026-07-06-145-mkdocs-strict-warnings-cleanup-design.md`,
under "Bucket B" — that content is unaffected by the #148
decommission decision and still accurate.

## Notes

- Filed while resolving #145 (mkdocs `--strict` warnings cleanup).
- See also #150: hardens `bin/issues/close.bash` so this bug class
  doesn't recur on future issue closes.
