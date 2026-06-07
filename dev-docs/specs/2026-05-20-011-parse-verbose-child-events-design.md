# Design: Fix verbose child events uncaptured in plcc-parse and plcc-rep

**Issue:** 011  
**Date:** 2026-05-20  
**Branch:** fix/011-verbose-child-events

## Problem

`plcc-parse` and `plcc-rep` both spawn `plcc-tokens` and `plcc-trees` via `TreePipeline`.
When the user passes `-v`, those child processes emit JSON verbose events to stderr.
Because `TreePipeline` spawns them with `stderr=None` (inherited), the raw JSON lines
go directly to the terminal without passing through `VerboseContext.reformat_child_events()`.

The result is garbled output: reformatted text lines from `plcc-make` mixed with raw
`{"stage":...}` JSON lines from `plcc-tokens` and `plcc-trees`.

Confirmed with manual testing: both `plcc-parse -v` and `plcc-rep -v` exhibit the bug
on the current codebase.

## Approach

Thread `VerboseContext` into `TreePipeline`. The pipeline already owns the subprocess
lifecycle and the suppression decision (eof-probe case returns `None`), so it is the
right place to also own verbose event reformatting. The `plcc-make` path in `parse.py`
and `rep.py` already uses this pattern (`stderr=PIPE` → `parse_child_events` →
`reformat_child_events`).

## Changes

### `cmd/pipeline.py`

- `TreePipeline.__init__` gains `verbose=None` (`VerboseContext | None`).
- Both `Popen` calls change from `stderr=None` to `stderr=subprocess.PIPE`.
- After `tree_proc.communicate()` returns, read `tokens_proc.stderr`:

  ```python
  tree_out, tree_err = tree_proc.communicate()
  tokens_proc.wait()
  tokens_err = tokens_proc.stderr.read()
  ```

- At the two `return None` points (no records; eof-probe suppression), events are
  silently dropped — the pipeline will re-run with accumulated input and emit fresh
  events at that time.
- On a real return (records list), reformat if verbose is set:

  ```python
  if self._verbose:
      combined = tokens_err + tree_err  # tokens upstream → roughly chronological
      events = self._verbose.parse_child_events(combined.decode('utf-8', errors='replace'))
      self._verbose.reformat_child_events(events)
  return list(zip(records, raws))
  ```

- Add a comment noting the theoretical deadlock: if `tokens_proc` wrote more than ~64 KB
  to stderr before `tree_proc.communicate()` drained it, tokens could block. Verbose
  output for a single tokenization run is a handful of JSON lines (well under 1 KB),
  so this is not a practical risk.

### `cmd/parse.py`

- `ParseHandler.__init__` gains `verbose=None`, passes it to `TreePipeline`.
- `main()` passes `verbose` when constructing `ParseHandler`.

### `cmd/rep.py`

- `RepHandler.__init__` gains `verbose=None`, passes it to `TreePipeline`.
- `main()` passes `verbose` when constructing `RepHandler`.

### `cmd/_test_helpers.py`

- `_proc()` gains `stderr=b""` kwarg and sets `p.stderr = io.BytesIO(stderr)`.
- All existing tests pass unchanged (default `stderr=b""`).

## Tests

New tests in **`pipeline_test.py`**:

- `test_run_reformats_child_verbose_events_when_verbose_set` — tokens proc emits a
  JSON event on stderr; pipeline constructed with a `VerboseContext`; assert the event
  appears reformatted on stderr.
- `test_run_suppresses_child_verbose_events_on_eof_probe` — `eof=False` with an
  eof-only error; assert nothing is printed to stderr even when verbose is set.
- `test_run_works_without_verbose` — `verbose=None` (default), child emits stderr
  noise, assert no crash and nothing reformatted.

Smoke tests in **`parse_test.py`** and **`rep_test.py`**:

- One test each confirming `ParseHandler` / `RepHandler` accept and forward `verbose`
  without error (existing fixture constructors gain `verbose=None` default, no other
  changes to existing tests).

## Out of scope

- `plcc-rep`'s interpreter subprocess (`plcc-lang-run`) is spawned with `stderr=None`
  in `rep.py`. That is a separate process with a different communication pattern and is
  not addressed here.
- No changes to `verbose.py` — existing `parse_child_events` and
  `reformat_child_events` are used as-is.
