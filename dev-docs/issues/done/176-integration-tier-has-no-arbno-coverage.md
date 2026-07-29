# 176 - Integration tier has no repetition-rule (arbno) coverage

**Type:** test
**Date:** 2026-07-28

## Description

`tests/bats/integration/` has no coverage at all for repetition rules
(`**=`, internally called "arbno"). Grammars using `**=` only appear
in `tests/bats/e2e/plcc-rep.bats` (`setup_arbno_build`,
`setup_mid_body_arbno_build`), which exercises the full
`plcc-spec | plcc-make | plcc-<lang>-emit | run` pipeline.

The `plcc-spec | plcc-ll1` boundary — where a decoded spec becomes an
LL(1) table, including arbno lookahead computation — is exactly where
issue #174's bug lived (a leading non-capturing terminal in a
repetition body producing the wrong lookahead). That boundary has no
targeted integration test; the only coverage is at the far end of the
pipeline (e2e) and, since #174, at the unit level
(`src/plcc/ll1/ll1_result_builder_test.py`). A regression in the
`plcc-spec`/`plcc-ll1` composition for arbno grammars would only be
caught by the (slower, coarser) e2e tier.

## Notes

- Existing integration test for the neighboring boundary:
  `tests/bats/integration/spec-ll1.bats` — a similar test file for
  arbno grammars, feeding `plcc-spec` output into `plcc-ll1` for a
  grammar like `<Items> **= BANG <Exp>` (a leading non-capturing
  terminal), would close this gap.
- Existing arbno fixtures: `tests/fixtures/trivial-arbno.plcc` and
  `tests/fixtures/arbno-mid-body-terminal.plcc` — these or similar
  grammars could be reused or adapted for the integration tier.
- Not urgent: the e2e tier does exercise this behavior today. This is
  about closing a test-pyramid gap so future regressions are caught
  faster and more precisely.
