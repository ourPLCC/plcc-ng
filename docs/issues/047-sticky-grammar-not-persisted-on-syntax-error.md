# 047 - Sticky grammar not persisted when grammar has a syntax error

**Type:** fix
**Date:** 2026-05-29

## Description

When a grammar file has a syntax error, the build fails before `build/.grammar` is
written, so the sticky grammar feature does not take effect. A subsequent invocation
without `--grammar-file` falls back to the default `grammar.plcc` instead of retrying
the grammar the user was working on.

## Steps to Reproduce

```bash
plcc-parse --grammar-file=A.plcc   # A.plcc has a syntax error; user sees error and fixes A.plcc
plcc-parse                          # user expects a retry of A.plcc; instead tries grammar.plcc
```

## Notes

`build/.grammar` is written after a successful build. A syntax error aborts the build
early, leaving `build/` empty (or stale), so there is no record of which grammar was
last requested.

Possible fix: write `build/.grammar` as soon as the grammar file is resolved and
validated to exist — before the build stages run — so the intent is recorded even
when the build fails. The wipe-on-change logic (issue 046) would still apply: if
`--grammar-file` names a different grammar than what is stored, wipe `build/` first,
then record the new grammar path, then attempt the build.
