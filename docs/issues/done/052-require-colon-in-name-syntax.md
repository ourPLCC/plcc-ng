# 052 - Require colon in <...>:name syntax; reject <...>name

**Type:** refactor
**Date:** 2026-05-29

## Description

Names attached to non-terminals on the LHS and RHS of production rules should only
be accepted in the `<...>:name` form (colon between `>` and the name). The
no-colon form `<...>name` is currently accepted on the RHS and should be rejected.

## Notes

The LHS already requires the colon. The RHS is the only place where the colon is
optional. The relevant code is in
`src/plcc/spec/syntax/parse_syntactic_spec.py`:

- **Line 88:** RHS symbol regex `r"<(?P<name>\S*)>(?P<altName>\S+)?"` captures
  anything after `>` as `altName` regardless of whether a colon is present.
- **Line 97:** `altName.strip(":")` silently discards the colon if present, making
  both forms equivalent.

Fix: update the RHS regex to require a leading colon before the alt name, and remove
the `strip(":")` call. Grammars using the no-colon form should get a clear syntax
error.

Update the test in `src/plcc/spec/syntax/parse_syntactic_spec_test.py` — the
no-colon test case (around line 304, `<word>hello`) should become an error case.
