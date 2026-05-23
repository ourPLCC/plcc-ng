# Scanner Newline Support

**Date:** 2026-05-22

## Problem

The original PLCC scanner delivers the newline character (`\n`) to the scanner so that grammar patterns can match or error on it. For example, a grammar with `token NUM '\d+'` and no whitespace skip will produce `!ERROR(
)` when a bare newline appears in the input.

Our implementation strips the trailing `\n` from every line before handing it to the scanner, so `\n` is never visible to patterns. This is a behavioral divergence from the original PLCC.

## Goal

Make `\n` visible to scanner patterns in `plcc-tokens`, matching original PLCC behavior.

## Design

### Root change

**File:** `src/plcc/tokens/tokens_cli.py`, function `_lines_from_stream`

Remove the `.rstrip('\n')` call so each line is passed to `Line` with its trailing newline intact:

```python
# before
yield Line(string=raw.rstrip('\n'), number=i, file=file)

# after
yield Line(string=raw, number=i, file=file)
```

Python opens files and `sys.stdin` in text mode by default, which normalizes `\r\n` → `\n` on all platforms. No explicit normalization is needed.

The last line of a file that has no trailing newline will not end with `\n` — that is correct and unchanged behavior.

### source_line display fix

**File:** `src/plcc/tokens/jsonl_formatter.py`, function `format_record`

The `source_line` field in `--trace` output is for human display. Strip the trailing `\n` before serializing it so trace output remains readable:

```python
# before
record['source_line'] = obj.line.string

# after
record['source_line'] = obj.line.string.rstrip('\n')
```

### Test updates

**File:** `src/plcc/tokens/tokens_cli_test.py`

Several tests use `_SPEC` (only `token NUM '\d+'`, no whitespace skip) with inputs like `'42\n'` and assert exactly one non-sentinel record. After the root change, the trailing `\n` produces a `LexError`, adding a second non-sentinel record.

Fix: switch those tests to `_SPEC_WITH_SKIP` (which includes `skip WS '\s+'`), so the trailing newline is silently consumed and the existing count assertions remain valid. Affected tests:

- `test_outputs_token_jsonl` — asserts exactly 1 non-sentinel record
- `test_lex_error_and_token_appear_in_stream_order` — asserts exactly 2 non-sentinel records
- `test_stdin_labels_tokens_with_dash` — asserts exactly 1 non-eof record
- `test_named_file_arg_labels_tokens_with_filename` — asserts exactly 1 non-eof record

`test_lex_error_emits_error_record_to_stdout` uses `'@\n'` and asserts exactly 1 error record. Fix: change input to `'@'` (no trailing newline) so the test remains focused on the `@` error case.

New tests to add:

- A grammar with an explicit `token NL '\n'` pattern can match newlines as tokens.
- A grammar with no newline handler produces a `LexError` for `\n`, matching original PLCC behavior.

## Behavioral summary

| Grammar has…         | Before this change              | After this change                              |
|----------------------|---------------------------------|------------------------------------------------|
| `skip WS '\s+'`      | `\n` silently ignored           | `\n` matched by `\s+`, silently ignored (no change) |
| `token NL '\n'`      | `\n` never seen, pattern useless | `\n` matched as `NL` token                   |
| No newline handler   | `\n` silently ignored           | `LexError` for `\n` (matches original PLCC)   |

## Out of scope

- `scan/source.py` — only used in its own test, not in the production scan pipeline.
- `lines/parse_from_string.py` — uses `str.splitlines()` which strips newlines; this is correct for spec/grammar parsing, not source scanning.
