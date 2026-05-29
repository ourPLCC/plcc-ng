# 051 - Remove %%{ / %%} semantic block bracket syntax

**Type:** refactor
**Date:** 2026-05-29

## Description

The spec parser supports two ways to delimit semantic blocks: `%%%` (symmetric) and
`%%{` / `%%}` (asymmetric). Remove the `%%{` / `%%}` variant so there is only one
way.

## Notes

- The relevant patterns are `PPLC` and `PPRC` in
  `src/plcc/spec/rough/parse_blocks.py` (lines 13–14), along with the `brackets`
  dict and the fallback auto-close logic (line 53) that references `%%%`.
- Remove the `PPLC`/`PPRC` regexes, the `brackets` dispatch, and all code paths
  that handle the asymmetric form.
- Update tests in `src/plcc/spec/rough/parse_blocks_test.py` — the
  `%%{`/`%%}` test cases (lines ~53–95) should be removed or converted to
  error-case tests confirming the syntax is rejected.
- This is a breaking change if any grammars in the wild use `%%{` / `%%}`. A clear
  parse error with a helpful message ("use %%% instead of %%{ / %%}") is preferable
  to silent misbehaviour.
