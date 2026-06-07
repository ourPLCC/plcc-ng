# tokens-cli UnclosedBlockError Handling Design

**Date:** 2026-06-04
**Issue:** 062

## Problem

`Scanner.scan` can yield `UnclosedBlockError` when EOF is reached inside a block token or skip (introduced in issue-060). `tokens_cli.py` only handles `Skip` and `LexError` explicitly; everything else falls through to `format_record`, which expects a `Token` and crashes on an `UnclosedBlockError`.

## Decision

Emit a soft JSONL error record (same stream as `LexError`) rather than a hard exit. Both callers of `plcc-tokens` — `plcc-scan` and `TreePipeline` — are designed around JSONL error records flowing through stdout. A hard exit would produce a generic "plcc-tokens failed" message with no location or rule information.

## `jsonl_formatter.py` — new function

Add `format_unclosed_block_error_record(obj: UnclosedBlockError) -> str` to `jsonl_formatter.py`. It raises `TypeError` for anything other than `UnclosedBlockError`, matching the guard on `format_error_record`.

Emitted record shape:

```json
{
  "kind": "error",
  "stage": "plcc-tokens",
  "severity": "error",
  "source": { "file": "...", "line": N, "column": N },
  "lexeme": "<open pattern regex>",
  "message": "unclosed block 'RULE_NAME': no closing pattern found"
}
```

- `source` — from `obj.line` and `obj.column` (the opening delimiter's position)
- `lexeme` — `obj.rule.pattern` (the open delimiter regex)
- `message` — names the rule; the close pattern is already in the spec, so it need not repeat in the message

## `tokens_cli.py` — dispatch change

Add imports for `UnclosedBlockError` and `format_unclosed_block_error_record`. Insert one branch in the `for obj in scanner.scan(lines)` loop, after the `LexError` branch:

```python
if isinstance(obj, UnclosedBlockError):
    print(format_unclosed_block_error_record(obj), flush=True)
    continue
```

`last_source` tracking is unchanged — after `UnclosedBlockError` the scanner is exhausted, so the EOF sentinel will use whatever `last_source` was set by the last successful token or skip.

## Testing

**`jsonl_formatter_test.py`:**
- Happy path: correct `kind`, `stage`, `severity`, `source`, `lexeme`, and `message` fields for a valid `UnclosedBlockError`
- Guard: raises `TypeError` when passed a non-`UnclosedBlockError` (e.g. a `LexError`)

**`tokens_cli_test.py`:**
- A spec with a block token rule and input containing only the open delimiter (no closing delimiter) produces a single `kind == "error"` record with correct `stage`, `severity`, `source`, and a `message` containing the rule name

No changes to `scanner_test.py` or `UnclosedBlockError_test.py` — the scanner already has coverage for yielding `UnclosedBlockError`; this fix is entirely in the CLI and formatter layers.
