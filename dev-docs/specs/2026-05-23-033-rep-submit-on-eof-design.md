# Design: 033 — plcc-rep switch to SubmitOn.EOF

## Summary

Switch `plcc-rep`'s interactive input mode from `SubmitOn.EOL` to `SubmitOn.EOF`,
aligning it with `plcc-parse`. Enter always accumulates; ^D submits. No other code
changes.

## Change

**`src/plcc/cmd/rep.py:120`** — one line:

```python
# before
runner = SourceRunner(submit_on=SubmitOn.EOL)

# after
runner = SourceRunner(submit_on=SubmitOn.EOF)
```

## Unchanged

- `RepHandler.feed()` — already mirrors `ParseHandler.feed()` exactly: same
  `eof=False` default, same `if items is None: return False`, same `return True`.
- `rep_test.py` — already mirrors `parse_test.py` structure.
- `TreePipeline` — no change.
- `SourceRunner` — no change.

## UX

In interactive mode every Enter accumulates and shows `...`. `^D` submits the buffer
for evaluation. Even a single-line expression like `42` requires `42↵ ^D`. This is
the accepted trade-off for consistency with `plcc-parse`.

## Scope

All changes are confined to `src/plcc/cmd/rep.py`, line 120.
