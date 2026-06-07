# Design: 042 — diagram orchestrator stderr forwarding

**Date:** 2026-06-05
**Issue:** 042-diagram-orchestrator-stderr-forwarding

## Problem

`plcc-diagram` (the orchestrator in `src/plcc/cmd/diagram.py`) forwards child process
stderr with raw binary writes:

```python
if make_result.stderr:
    sys.stderr.buffer.write(make_result.stderr)
```

This appears four times — once per subprocess call (`plcc-make`, `plcc-diagram-emit`,
`plcc-diagram-build`, `plcc-diagram-run`). It has two problems:

1. **VerboseContext bypass.** When `-v` is active, children emit structured JSONL events.
   Raw byte-forwarding drops that structure, so the parent cannot reformat them according
   to its own `--verbose-format` setting.

2. **Buffer coupling.** `sys.stderr.buffer` is the underlying binary stream. Decoding
   first is more portable and consistent with every other orchestrator in the codebase.

## Existing pattern

Three other orchestrators already use the correct approach:

- `src/plcc/cmd/make.py` (lines 108, 126–127, 232–233)
- `src/plcc/cmd/parse.py` (lines 85, 95–96)
- `src/plcc/cmd/rep.py` (lines 93, 102–103)

The pattern is:

```python
child_flags = verbose.child_flags_for_orchestrator(min_level=0)
# ...subprocess call with stderr=subprocess.PIPE...
events = verbose.parse_child_events(result.stderr.decode('utf-8', errors='replace'))
verbose.reformat_child_events(events)
```

`child_flags_for_orchestrator` forces `--verbose-format=json` on children so their
stderr is parseable JSONL. `parse_child_events` handles non-JSON lines (plain-text
errors from processes that don't use VerboseContext) by preserving them as-is.

## Changes

### `src/plcc/cmd/diagram.py`

**1. Replace `child_flags` assignment (line 62):**

```python
# before
child_flags = verbose.child_flags()

# after
child_flags = verbose.child_flags_for_orchestrator(min_level=0)
```

**2. Replace each of the four raw stderr writes:**

```python
# before
if result.stderr:
    sys.stderr.buffer.write(result.stderr)

# after
if result.stderr:
    events = verbose.parse_child_events(result.stderr.decode('utf-8', errors='replace'))
    verbose.reformat_child_events(events)
```

The `if result.stderr:` guard is retained, consistent with the same pattern in
`parse.py`, `rep.py`, and `make.py`.

## Testing

New unit tests in `src/plcc/cmd/diagram_test.py`:

- Plain-text stderr from a child is forwarded to `sys.stderr`.
- JSONL events in child stderr are reformatted through the parent's verbose context
  (text output format verified).
- Empty child stderr produces no output.

The existing tests stub `m.stderr = b''` so they continue to pass unchanged.
