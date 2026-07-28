# 175 - Build sentinel ignores the installed PLCC-ng version

**Type:** fix
**Date:** 2026-07-28

## Description

The build sentinel (`src/plcc/build/staleness.py`, `write_sentinel`/
`is_current`) records only the SHA-256 hash of `spec.json` and the set
of completed stages — never the installed PLCC-ng package version. So
upgrading the PLCC-ng package does not, by itself, invalidate a cached
`plcc-ng/` build directory: with an unchanged spec, `is_current`
reports the build as current and `plcc-make` reuses the old generated
artifacts (parse tables, emitted code) even though the installed
package version has changed the code that produces them.

Issue #174's fix is the concrete instance: a user who already hit the
repetition-rule bug has a successfully-built `plcc-ng/` directory (the
build succeeded; only parsing failed). After upgrading to the fixed
version, `plcc-make` sees an unchanged spec hash, reports the build is
current, and reuses the old `ll1.json` — so the fix silently never
reaches them unless they manually delete the build directory. The
v2.0.1 `docs/whats-new.md` entry currently works around this with a
"delete your build directory" instruction, but that's a documentation
band-aid, not a fix.

## Steps to Reproduce

1. Build a spec with a version of PLCC-ng affected by a generation bug
   (e.g. pre-#174), producing a `plcc-ng/` build directory.
2. Upgrade PLCC-ng to a version with the bug fixed, without touching
   the spec file.
3. Run `plcc-make` (or any command that shells out to it, e.g.
   `plcc-parse`) again.
4. Observe the build is reported current and reuses the stale
   generated artifacts, even though the fix is installed.

## Notes

Suggested direction: include the installed package version (e.g.
`plcc.version`) in the sentinel alongside the spec hash and completed
stages, so a version change forces a rebuild the same way a spec
change does.
