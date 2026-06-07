# Parse Trace Design (Issue 030)

**Date:** 2026-05-28
**Branch:** feat/030-parse-trace-flag

## Goal

Add `--trace` / `-t` to `plcc-parse` for educational and diagnostic use. The trace shows the table-driven LL(1) parse algorithm step by step — predict, shift, complete — indented to reflect nesting depth. On a parse failure, the trace is shown automatically (without `--trace`) so students can see what the parser was doing when it failed.

This is a human-facing report tool, not a data pipeline. All output — trace, tree, and errors — goes to stdout.

## Behavior

| Invocation | Outcome | stdout |
|---|---|---|
| `plcc-parse --trace`, success | trace + tree | parse-step lines, then tree |
| `plcc-parse --trace`, failure | trace + error | parse-step lines, then error |
| `plcc-parse` *(no flag)*, failure | auto-trace + error | parse-step lines, then error |
| `plcc-parse` *(no flag)*, success | tree only | tree (unchanged) |

## Architecture

Pipeline: `plcc-parse` → subprocess `[plcc-tokens | plcc-trees → plcc-parser-table]` → JSONL back to `plcc-parse`.

A new JSONL record kind — `parse-step` — is emitted by `plcc-parser-table` on its stdout, before the `tree` or `error` record it belongs to. These flow through the existing pipeline unchanged and are rendered as plain text by `plcc-parse`.

Flag propagation: `plcc-parse --trace` → `plcc-trees --trace` → `plcc-parser-table --trace`.

`plcc-parser-table` always creates a `Tracer` (enabling the automatic failure trace). The `--trace` flag controls whether to also flush trace events on success.

## Components

### `Tracer` class (`predictive_parser.py`)

Lives alongside `parse()`. Manages depth internally via push/pop so no depth counter needs to thread through the recursive parser.

```python
class Tracer:
    def push(self, sym): ...       # entering a nonterminal
    def pop(self): ...             # leaving a nonterminal
    def predict(self, sym, lookahead, production): ...
    def shift(self, token): ...
    def complete(self, rule): ...

    @property
    def events(self): ...          # list of dicts, in emission order
```

`parse()` gains `tracer=None`. When present:
- `_parse_regular`: calls `tracer.predict(sym, lookahead, production_name)`, then `tracer.push(sym)` before the production body, `tracer.pop()` + `tracer.complete(rule)` after (pop first so complete records the outer depth, matching its paired predict).
- `_parse_arbno`: calls `tracer.predict(sym, lookahead, production=None)` at the start of each iteration (no parse table lookup; `production=None` signals "another iteration"), `tracer.push/pop` around each iteration body.
- `expect()`: calls `tracer.shift(token)` on a match.

Each event is stored as a dict with `"event"`, `"depth"`, and relevant fields.

### `parse-step` JSONL records

Emitted by `plcc-parser-table` to stdout before the associated `tree` or `error` record:

```json
{"kind": "parse-step", "event": "predict", "sym": "expr", "lookahead": "NUM", "production": "expr:Num", "depth": 0}
{"kind": "parse-step", "event": "shift", "name": "NUM", "lexeme": "3", "source": {...}, "depth": 1}
{"kind": "parse-step", "event": "complete", "rule": "expr:Num", "depth": 0}
```

### `plcc-parser-table` changes

Add `-t` / `--trace` flag. The main parse loop always creates a fresh `Tracer` per program. After each `parse()` call:

- **Success + `--trace`**: emit `parse-step` records, then `tree` record.
- **Success, no `--trace`**: emit `tree` record only.
- **`ParseError`**: always emit `parse-step` records, then `error` record.

Tracer is reset between programs in the multi-program parse loop.

### `plcc-trees` changes

Add `-t` / `--trace` flag. Forward it to the parser plugin via child command flags alongside verbose flags.

### `plcc-parse` changes

Add `-t` / `--trace` flag. Pass it through `child_flags` to `TreePipeline` → `plcc-trees` → `plcc-parser-table`.

In `ParseHandler.feed()`, add a handler for `kind == "parse-step"` that calls `_print_parse_step(record)`. Unknown kinds continue to be silently ignored.

`TreePipeline` accepts and forwards the trace flag in the child flags it passes to `plcc-trees`.

### Plain-text rendering (`_print_parse_step`)

Indentation: `"  " * depth`. Event keyword left-padded to 8 characters.

```
predict  expr     lookahead=PLUS → expr:Add
  shift    PLUS '+' [1:1]
  predict  expr     lookahead=NUM → expr:Num
    shift    NUM '3' [1:6]
  complete expr:Num
  predict  expr     lookahead=NUM → expr:Num
    shift    NUM '5' [1:8]
  complete expr:Num
complete expr:Add
```

The tree is printed immediately after the last trace line (no blank line separator needed; the structural difference is clear).

## Testing

- **Unit — `Tracer`**: instantiate, call push/pop/predict/shift/complete in sequence, assert `events` list matches expected dicts including depth values.
- **Unit — `parse()` with tracer**: pass a real `Tracer` to the existing grammar fixtures in `predictive_parser_test.py`; assert event sequences match the known parse for each grammar (trivial, nested, arbno).
- **Unit — `table_cli`**: with `--trace`, verify `parse-step` JSONL records are emitted before the tree record; on `ParseError` without `--trace`, verify they are emitted before the error record.
- **Integration (bats) — `plcc-parse --trace`**: on a successful parse, stdout contains trace lines followed by the tree; on a parse failure without the flag, stdout contains trace lines followed by the error message.
