# 159 - Migration guide buries breaking behavior changes

**Type:** docs
**Date:** 2026-07-22

## Description

`docs/migration.md` mentions two breaking behavior changes, but both are
easy to miss because they're buried in a comparison table rather than
called out prominently:

1. `plcc-parse` no longer has a `-t` flag and no longer prints `OK`. It
   always prints the full parse tree now. Instructors coming from old PLCC
   expect `-t` and `OK` from muscle memory.
2. `plcc-scan` output format changed from `TOKEN_NAME(lexeme)` to
   `source:line:col TOKEN_NAME 'lexeme'`. The guide's table shows the new
   format but doesn't flag it as a breaking change that will invalidate any
   existing documentation, tests, or course materials showing the old format.

Both of these were hit while migrating the CCSCNE-2026 workshop materials
to plcc-ng (surfaced via the plcc-ng-demo project's dev-docs/issues/001).

## Notes

Add a prominent "Breaking behavior changes" callout section to
`docs/migration.md` that covers both of these explicitly, rather than
relying solely on the "Replace commands" table.
