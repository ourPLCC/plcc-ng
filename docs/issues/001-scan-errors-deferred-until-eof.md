# 001 - Scan errors deferred until EOF instead of reported inline

**Type:** fix
**Date:** 2026-05-07

## Description

`plcc-scan` collects lexing errors and prints them only after all input has been
processed (i.e., at EOF). In batch mode this is noticeable but not unreasonable.
But in interactive mode it is misleading:

- The user sees no indication that a token failed to match until they type `^D`.
- If they kill the process with `^C`, they never see the errors at all.
- The output interleaving is wrong: errors should appear at the position in the
  token stream where they occur, not at the end.

## Steps to Reproduce

1. Define a grammar with a single rule: `A 'a'`
2. Run `plcc-scan` (or the equivalent pipeline entry point) interactively.
3. Type `a@a` and press Enter.
4. Observe: output shows `token token` with no error on that line.
5. Type `^D` (EOF).
6. Observe: errors appear now, after the session has ended.
7. Repeat steps 2–4, then type `^C` instead of `^D`.
8. Observe: no errors are ever shown.

Expected: the error for `@` should appear in the output stream at the point it
was encountered, i.e., between the two `token` lines (or inline on the same
line, depending on the output format).

## Notes

The fix should flush/emit each error immediately when the unmatched input is
detected, rather than accumulating errors and printing them at shutdown.
Consider whether the error output should go to stderr (so it doesn't corrupt
the token stream consumed by downstream stages) or be embedded in the token
stream as a distinguished error token — whichever is consistent with how
downstream stages (parser, etc.) handle scan errors.
