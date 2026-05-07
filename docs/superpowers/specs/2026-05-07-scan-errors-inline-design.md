# Design: Scan errors reported inline instead of deferred until EOF

**Issue:** 001-scan-errors-deferred-until-eof  
**Date:** 2026-05-07  
**Status:** Approved

## Problem

`plcc-tokens` sends lex errors to stderr via `verbose.emit_error()`. `plcc-scan`
drains that stderr with a single blocking `proc.stderr.read()` in a background
thread, so all errors accumulate until the subprocess exits. In interactive use,
errors never appear until the user types `^D`, and are lost entirely on `^C`.

## Decision: errors are data, not tool failures

A `LexError` is not a malfunction of `plcc-tokens` — it is a result: the scanner
encountered an unrecognized character and produced a record describing it, just
as it produces a token record for a recognized one. The tool succeeded; the input
contained an unrecognized character.

Consequences:
- Lex errors go into `plcc-tokens` stdout as `{"kind":"error"}` JSONL records,
  interleaved with `{"kind":"token"}` records in stream order.
- `plcc-tokens` exits 0 when scanning completes, regardless of lex errors.
  It can still exit nonzero for tool-level failures (bad spec file, I/O error).
- `--continue-on-error` is dropped: continuing after a lex error is now the
  default and only behavior.

## Error record format

```json
{
  "kind": "error",
  "stage": "plcc-tokens",
  "severity": "error",
  "pos": {"file": "<stdin>", "line": 1, "column": 3},
  "lexeme": "@",
  "message": "unrecognized character"
}
```

- `kind` distinguishes error records from token records in the stream.
- `stage` identifies the origin (already expected by `table_cli_test.py`).
- `lexeme` carries the offending character, mirroring the `lexeme` field on token records.
- `pos` matches the shape used throughout the rest of the pipeline.

## Component changes

### `src/plcc/tokens/jsonl_formatter.py`

Add `format_error_record(lex_error)` alongside the existing `format_record(token)`:

```python
def format_error_record(obj):
    return json.dumps({
        'kind': 'error',
        'stage': 'plcc-tokens',
        'severity': 'error',
        'pos': {
            'file': obj.line.file,
            'line': obj.line.number,
            'column': obj.column,
        },
        'lexeme': obj.line.string[obj.column - 1],
        'message': 'unrecognized character',
    })
```

### `src/plcc/tokens/tokens_cli.py`

In the LexError branch:
- Replace `verbose.emit_error(...)` with `print(format_error_record(obj), flush=True)`.
- Remove `had_error` flag and the trailing `if had_error: sys.exit(1)`.
- Remove `--continue-on-error` from the docstring and argument parsing.

The tool always continues scanning after a lex error and always exits 0 on
normal completion.

### `src/plcc/cmd/scan.py`

- Remove `--continue-on-error` from the `plcc-tokens` subprocess call.
- In the `for raw in proc.stdout:` loop, add a handler for `kind == "error"`:

```python
elif record.get("kind") == "error":
    loc = _location_str(record.get("pos", {}))
    lexeme = record.get("lexeme", "?")
    print(f"{loc}: error: unrecognized character '{lexeme}'", flush=True)
```

This prints inline with token lines on stdout. The stderr drain thread is
unchanged — it still handles tool-level diagnostic events from `plcc-tokens`.

## Test changes

### `src/plcc/tokens/tokens_cli_test.py`

- **Remove:** `test_lex_error_goes_to_stderr_and_exits_nonzero`
- **Remove:** `test_lex_error_json_format`
- **Remove:** `test_continue_on_error_continues_after_bad_char`
- **Remove:** `test_continue_on_error_bad_char_only_exits_nonzero`
- **Remove:** `test_continue_on_error_valid_input_exits_zero`
- **Remove:** `test_default_still_exits_on_first_error`
- **Add:** `test_lex_error_emits_error_record_to_stdout` — assert stdout contains a
  `{"kind":"error"}` record with correct fields; assert stderr is empty (at default
  verbosity); assert exit 0.

### `src/plcc/tokens/jsonl_formatter_test.py`

- **Add:** `test_formats_error_record` — construct a `LexError`, call
  `format_error_record`, assert the resulting dict has the correct shape and values.

## What does not change

- `src/plcc/parser/table_cli.py` — already handles `kind == "error"` records
  (passes them through); no change needed.
- `src/plcc/cmd/parse.py` and `src/plcc/cmd/rep.py` — pipe `plcc-tokens` stdout
  directly to downstream; error records propagate naturally and the downstream
  parser already handles them.
- The stderr drain thread in `scan.py` — unchanged; still collects tool-level
  diagnostic output.
