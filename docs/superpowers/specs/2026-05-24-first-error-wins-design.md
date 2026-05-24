# Design: First-Error-Only for plcc-parse and plcc-rep

**Date:** 2026-05-24

---

## Context

`plcc-parser-table` collects lex error records from `plcc-tokens` but silently
overwrites `error_record` on each one, then emits only the last. So for input
`ab` (both characters unrecognized), the user sees the error for `b` instead of
`a`. The 2026-05-15 error-handling design explicitly deferred fixing this.

The right behavior is:
- `plcc-parse` and `plcc-rep`: show only the **first** error (lex or parse),
  so the user has one clear thing to fix.
- `plcc-scan`: unchanged — it already shows all lex errors correctly.
- `plcc-parser-table`: pass **all** lex errors through faithfully; it is a
  pipeline component and should not enforce display policy.

---

## Design

### 1. `plcc-parser-table` (`src/plcc/parser/table_cli.py`)

Remove the `error_record` accumulation pattern. Instead, emit each lex error
record to stdout immediately as it is read from stdin, and set a boolean flag.
After reading all input, if the flag is set, skip the parse loop (same policy
as today — a token stream with holes cannot be reliably parsed).

Before:
```python
error_record = None
for line in sys.stdin:
    ...
    if record.get("kind") == "error":
        error_record = record          # silently overwrites
    else:
        tokens.append(record)

if error_record is not None:
    print(json.dumps(error_record))   # emits only the last
    sys.exit(0)
```

After:
```python
has_lex_error = False
for line in sys.stdin:
    ...
    if record.get("kind") == "error":
        print(json.dumps(record), flush=True)   # emit immediately
        has_lex_error = True
    else:
        tokens.append(record)

if has_lex_error:
    sys.exit(0)
```

### 2. `ParseHandler.feed()` (`src/plcc/cmd/parse.py`)

Add `break` after printing the first error record. Trees that arrive before the
error are still rendered; everything after is dropped.

```python
for record, _ in items:
    if record.get("kind") == "error":
        print_parse_error(record, default_stage="plcc-parse")
        self.had_error = True
        break                          # stop at first error
    elif record.get("kind") == "tree":
        _print_tree(record, indent=0)
```

### 3. `RepHandler.feed()` (`src/plcc/cmd/rep.py`)

Same change — `break` after the first error. Return value remains `True` so the
REPL re-prompts normally.

```python
for record, raw in items:
    if record.get("kind") == "error":
        print_parse_error(record, default_stage="plcc-rep")
        break                          # stop at first error
    elif record.get("kind") == "tree":
        ...
```

No shared abstraction — the duplication is one `break` in two files (YAGNI).

---

## Behavior by scenario

| Input       | Before                         | After                        |
|-------------|--------------------------------|------------------------------|
| `ab`        | error for `b` (last)           | error for `a` (first)        |
| `a2`        | error for `a` (only one)       | unchanged                    |
| `abc`       | error for `c` (last)           | error for `a` (first)        |
| `3 2 1`     | one parse error (cascade fixed)| unchanged                    |
| `plcc-scan` | all errors shown               | unchanged                    |

---

## Compatibility: future algorithmic trace

A future trace feature will attach additional diagnostic information to parse
errors. This design is compatible provided the trace is either:
- **Embedded in the error record** (e.g., a `trace` field): no conflict — the
  `break` carries the full record.
- **Emitted as records before the error**: no conflict — they arrive before
  the `break` triggers.

Trace records emitted *after* the error record would be cut off by the `break`.
That format should be avoided.

---

## Files changed

| File | Change |
|---|---|
| `src/plcc/parser/table_cli.py` | Replace `error_record` accumulation with immediate emit + flag |
| `src/plcc/cmd/parse.py` | `break` after first error in `ParseHandler.feed()` |
| `src/plcc/cmd/rep.py` | `break` after first error in `RepHandler.feed()` |
| `src/plcc/parser/table_cli_test.py` | Update: multiple lex errors all appear in output; add first-lex-error scenario |
| `src/plcc/cmd/parse_test.py` | Add: `ab` reports `a`; multiple lex errors show only first |
| `src/plcc/cmd/rep_test.py` | Same as parse_test |

---

## Verification

1. Run the test suite: `bin/test-unit`
2. Manually: `plcc-parse` with input `ab` should report `a`, not `b`
3. Manually: `plcc-parse` with input `abc` should report only `a`
4. Manually: `plcc-scan` with input `ab` should still report both `a` and `b`
5. Manually: `plcc-rep` with input `ab` should report only `a`, then re-prompt
