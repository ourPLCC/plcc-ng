# Design: plcc-scan multi-line mode (issue 063)

**Date:** 2026-06-05

## Problem

`plcc-scan` uses `SubmitOn.EOL`, which in interactive mode submits one line at a time to a fresh `plcc-tokens` subprocess. When a block token opens on one line but closes on a later line, the scanner exhausts its single-line input and emits `UnclosedBlockError` instead of spanning lines. Block tokens/skips are therefore broken in interactive use.

File and pipe input already work correctly — the whole content is read and submitted at once — so this is an interactive-mode-only defect.

## Decision

Switch `plcc-scan` from `SubmitOn.EOL` to `SubmitOn.EOF`, matching `plcc-parse` and `plcc-rep`. In interactive mode, input accumulates until the user presses ^D, then the full buffer is submitted to `plcc-tokens` as one unit, allowing the `Scanner` to match block tokens across line boundaries.

Trade-off accepted: per-line feedback in interactive mode is lost. Benefit: all interactive level-2 commands now share the same ^D-to-submit interaction model, which is simpler and more consistent.

## Changes

### `src/plcc/cmd/scan.py` (line 168)

```python
# before
runner = SourceRunner(submit_on=SubmitOn.EOL)

# after
runner = SourceRunner(submit_on=SubmitOn.EOF)
```

### `src/plcc/cmd/source_runner.py` (line 11)

Remove the stale `— plcc-scan` annotation from the `EOL` doc comment:

```python
# before
EOL = "eol"   # each newline submits — plcc-scan

# after
EOL = "eol"   # each newline submits
```

### `src/plcc/cmd/scan_test.py`

Add a test asserting `main()` constructs `SourceRunner` with `submit_on=SubmitOn.EOF`.

## Out of scope

- `plcc-tokens`, `Scanner`, `ScanHandler`, and the `SubmitOn` enum are unchanged.
- The `EOL` variant is kept in the enum; no callers use it after this change, but it is not removed.
