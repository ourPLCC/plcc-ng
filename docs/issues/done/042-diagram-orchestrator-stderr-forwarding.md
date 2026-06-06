# 042 - plcc-diagram stderr forwarding bypasses VerboseContext

**Type:** refactor
**Date:** 2026-05-25

## Description

`plcc-diagram` (the orchestrator) forwards child stderr with raw byte writes:

```python
if make_result.stderr:
    sys.stderr.buffer.write(make_result.stderr)
```

This pattern has two issues:

1. **VerboseContext bypass.** When `-v` flags are passed, child processes emit structured JSONL events. Raw byte-forwarding drops that structure at the orchestrator level, so the parent's verbose output is inconsistently formatted.

2. **Buffer coupling.** `sys.stderr.buffer` is the underlying binary stream of `sys.stderr`. It works in CPython but couples the code to the TextIOWrapper assumption. Decoding first (`make_result.stderr.decode()` + `sys.stderr.write(...)`) is more portable.

The same pattern appears for all four subprocess calls in `diagram.py` (`make_result`, `emit_result`, `build_result`, `run_result`).

## Notes

- A proper fix would decode child JSONL events and re-emit them through the parent's `VerboseContext`, similar to how `child_flags` already wires verbose level propagation downward.
- Alternatively, a simpler fix (no JSONL parsing) would just decode bytes to text before writing to `sys.stderr`.
- This was introduced in the fix/xdg-open-missing branch (commit adff700) as part of decoupling diagram ops from `plcc-make`. The pattern was directly specified in the implementation plan, so it's a known limitation rather than an oversight.
- The `--through=model` invocation of `plcc-make` may itself use VerboseContext-aware stderr; once that path is consistent, the diagram orchestrator should follow suit.
