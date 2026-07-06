# Design: Fix 047 — Sticky grammar not persisted on syntax error

**Date:** 2026-05-29
**Issue:** [047](../issues/done/047-sticky-grammar-not-persisted-on-syntax-error.md)

## Problem

When a grammar file has a syntax error, `plcc-make` fails before `write_grammar` is
called, so `build/.grammar` is never written (or remains stale). A subsequent invocation
without `--grammar-file` falls back to `grammar.plcc` instead of retrying the grammar
the user was working on.

## Approach

Move the single `write_grammar` call to immediately after `build_dir.mkdir(exist_ok=True)`,
before any build stages run. Remove the two now-redundant calls (fast path and slow-path
success). This ensures the user's intent is recorded regardless of build outcome.

The wipe-on-change logic (already in place) runs before `mkdir`, so the directory is
always in the correct state when `write_grammar` is called.

## Changes

### `src/plcc/cmd/make.py`

- After `build_dir.mkdir(exist_ok=True)`, insert `write_grammar(build_dir, grammar)`.
- Remove `write_grammar(build_dir, grammar)` from the fast path (currently line 145).
- Remove `write_grammar(build_dir, grammar)` from after the slow-path success (currently line 195).

No other source files change.

## Tests

### `src/plcc/cmd/make_test.py`

Add one new test:

**`test_grammar_written_before_build_stages_run`** — Creates a `tmp_path` with a grammar
file whose content causes `plcc-spec` to fail. Calls `run_main(['--grammar-file=bad.plcc'])`,
catches `SystemExit`, then asserts `read_grammar(build)` returns `"bad.plcc"`.

Existing coverage already handles:
- wipe-then-write when grammar changes (`test_explicit_grammar_differs_from_stored_wipes_build`)
- no-wipe when grammar is the same (`test_explicit_grammar_same_as_stored_does_not_wipe`)
- stored grammar recalled on subsequent run (existing stored-grammar tests)
