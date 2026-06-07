# Stop Error Cascade in plcc-parser-table

**Date:** 2026-05-21

---

## Motivation

`plcc-parser-table` currently advances the cursor by one token after every non-eof
`ParseError` and retries from the next position. For input like `3 2 1` against a
grammar that expects `INT PLUS INT`, this produces three parse attempts: an error at
token 1 (failed on token 2), an error at token 2 (failed on token 3), and a possible
tree for token 3 if it is a valid expression on its own. A student sees multiple error
messages and possibly a spurious tree from a single wrong expression.

The original justification was consistency with `plcc-tokens`, which advances past an
unrecognised character and continues. But a lex error at one character doesn't contaminate
neighbouring characters, whereas a parse error at one token typically implicates the
surrounding ones. The analogy doesn't hold.

---

## Requirements

1. A `ParseError`-based syntax error produces exactly one error record and stops
   further parsing of the current input. (The `consumed == 0` epsilon-advance path
   is a separate mechanism and is not changed by this fix.)
2. Multiple valid programs in one source (needed by side-effecting course languages)
   continue to produce multiple trees — the success-path loop is preserved.
3. Interactive sessions (plcc-rep, plcc-parse at a TTY) do not exit on a parse error.
   The user is re-prompted and can enter a new expression.
4. The "need more input" continuation (eof error → `...` prompt) is unchanged.

---

## Design

### The change

One word in `parser/table_cli.py`. In the `except ParseError` handler, replace
`cursor += 1` with `break`:

```python
# Before
except ParseError as e:
    record = {"kind": "error", "message": str(e), "stage": "plcc-parser-table", "source": e.source}
    if e.found:
        record["found"] = e.found
    print(json.dumps(record), flush=True)
    if e.found == "eof":
        break
    cursor += 1   # cascade: skip token, retry

# After
except ParseError as e:
    record = {"kind": "error", "message": str(e), "stage": "plcc-parser-table", "source": e.source}
    if e.found:
        record["found"] = e.found
    print(json.dumps(record), flush=True)
    break         # stop: eof and non-eof errors both terminate the loop
```

The `if e.found == "eof": break` branch is now unreachable and is removed.

No other runtime code paths change.

---

## Behavior by scenario

### Interactive sessions

| Input | Before | After |
|---|---|---|
| `3 + 2` | one tree, back to `>>>` | unchanged |
| `3 +` (incomplete) | eof error → `...` continuation | unchanged |
| `3 2 1` | error + error + maybe tree, back to `>>>` | one error, back to `>>>` |
| error then new expression | session continues | unchanged |

The session never exits on a parse error. `feed()` returns `True` on any genuine-error
record; `SourceRunner` resets the buffer and re-prompts. This property is unchanged
because it is governed by `pipeline.py` and `source_runner.py`, neither of which is
modified.

### Non-interactive (batch files / stdin pipe)

| Input | Before | After |
|---|---|---|
| `3 + 2\n4 + 5` (two valid programs) | two trees | unchanged |
| `3 2 1` | multiple errors, maybe a tree | one error |
| `3 + 2\nbad\n4 + 5` | tree + error + tree | tree + error; `4 + 5` not reached |

In the last row, stopping after the error is correct for side-effecting programs:
program 3 likely depends on program 2's side effects, so running it after program 2
failed would be misleading.

### Grammar-dependent note

If the grammar accepts a single `NUM` as a valid expression (e.g.
`<exp> ::= <NUM> | <NUM> <OP> <NUM>`), then `3 2 1` produces three trees through
the success path regardless of this change. That is correct behaviour — the grammar
defines what a program is, and three valid programs were submitted. The grammar is the
right place to enforce what constitutes a complete program.

---

## Why no other files need to change

- **`pipeline.py`**: the `only_eof_errors` heuristic checks whether all error records
  have `found == "eof"`. With the cascade removed, a non-eof error still sets
  `any_genuine_error = True`, so the heuristic returns the record list immediately.
  An eof error still sets `only_eof_errors = True`, so `pipeline.py` returns `None`
  when `eof=False` (continuation mode). Both paths are unaffected.
- **`source_runner.py`**: continuation and re-prompt logic is driven by whether
  `feed()` returns `True` or `False`, which is driven by `pipeline.py`'s return
  value. No change propagates here.
- **`parse.py` / `rep.py`**: both handlers process whatever record list the pipeline
  returns. Fewer records per invocation changes nothing about how each record is
  handled.

---

## Testing

Changes in `parser/table_cli_test.py`:

1. **Error stops the loop** — `3 2 1` for a grammar expecting `INT PLUS INT`:
   assert exactly one error record, no trees.
2. **Multiple valid programs still work** — `3 + 2` then `4 + 5`: assert two trees,
   no errors.
3. **Error after success stops** — `3 + 2` then `bad`: assert one tree then one
   error; no second tree.
4. **Eof error unchanged** — incomplete `3 +`: assert one error with
   `found == "eof"`.

Existing tests that expected cascaded errors from a single bad input are updated to
expect a single error.

---

## Files changed

| File | Change |
|---|---|
| `src/plcc/parser/table_cli.py` | Replace `cursor += 1` with `break`; remove unreachable `if e.found == "eof"` branch |
| `src/plcc/parser/table_cli_test.py` | Update cascade tests; add the four tests above |
