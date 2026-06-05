# Design: Remove Lexical Block (Second Pattern) — Issue 068

**Date:** 2026-06-05
**Branch:** 068-remove-lexical-second-pattern

## Summary

Remove the optional second pattern from lexical token/skip rules. Each rule must have exactly one regex pattern. This eliminates the block-scanning subsystem introduced in issues 059–064.

The `plcc-scan` EOF-submit mode (introduced in issue 063) is intentionally preserved.

## Lexical Spec Layer

**`Parser.py`:** Remove `_parseOptionalPattern` and its call in `_processLine`. After the first pattern is parsed, the existing end-of-line check already raises `UnexpectedContent` for anything non-whitespace/non-comment — no new error needed. Remove `close_pattern` from the `RuleClass(...)` constructor call.

**`TokenRule.py` / `SkipRule.py`:** Remove the `close_pattern` field. Remove the `BlockOpened` branch in `make_match` — both methods always return a `Token` or `Skip` directly.

**`LexicalRule.py`:** Remove `close_pattern` and `make_block_result` from the protocol.

**Tests:** Remove block-specific cases from `parse_lexical_test.py`, `TokenRule_test.py`, `SkipRule_test.py`. Update `test_junk_at_the_end_of_a_line` to expect `UnexpectedContent` (previously `PatternDelimiterExpected`, because junk was parsed as a malformed second pattern).

## Scan Layer

**Delete entirely:** `BlockOpened.py`, `BlockOpened_test.py`, `UnclosedBlockError.py`, `UnclosedBlockError_test.py`.

**`scanner.py`:** Remove the `BlockOpened` import, the `isinstance(result, BlockOpened)` branch in `_scanLine`, and the entire `_scanBlock` method. `_scanLine` becomes a simple loop: on `LexError` advance one character; otherwise advance by lexeme length.

**`scan/__init__.py`:** Remove `BlockOpened` and `UnclosedBlockError` exports.

**Tests:** Remove all block-related cases from `scanner_test.py` and `matcher_test.py`.

## Tokens / Schema Layer

**`spec_loader.py`:** Remove the `close_pattern` kwarg when constructing `TokenRule`/`SkipRule` from JSON.

**`spec.schema.json`:** Remove `close_pattern` from the token/skip rule schema.

**`jsonl_formatter.py`:** Remove `format_unclosed_block_error_record`.

**`tokens_cli.py`:** Remove the `UnclosedBlockError` import and its dispatch branch.

**Tests:** Remove block-related cases from `jsonl_formatter_test.py` and `tokens_cli_test.py`.

**`tests/bats/commands/plcc-scan.bats`:** Remove the block-token trace test.

## Behavioral Notes

- `token BODY '<<<' '>>>'` was previously valid; after this change it raises `UnexpectedContent` on the second pattern.
- `test_junk_at_the_end_of_a_line` changes its expected error from `PatternDelimiterExpected` to `UnexpectedContent` — the new behavior is more accurate.
- `plcc-scan` stays in EOF-submit mode; interactive behavior is unchanged.

## Out of Scope

- Updating `cmd/scan.py` or `source_runner.py` (EOF-submit mode is kept as-is).
- Any changes to the BNF/syntax spec layer.
