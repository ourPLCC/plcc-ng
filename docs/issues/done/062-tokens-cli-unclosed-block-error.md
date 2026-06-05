# 062 - tokens-cli-unclosed-block-error

**Type:** bug
**Date:** 2026-06-04

## Description

`Scanner.scan` can now yield `UnclosedBlockError` (introduced in issue-060) when EOF is reached while inside a block token or skip. `tokens_cli.py` only handles `Skip` and `LexError` explicitly; anything else is assumed to be a `Token` and passed to `format_record`. An `UnclosedBlockError` will fall through to that path and crash at runtime (either on the `obj.line.file` access or inside `format_record`, which expects a `Token`).

## Steps to Reproduce

1. Create a source file with an unclosed block, e.g. a file containing only `<<<hello` with no closing `>>>`.
2. Run `plcc-tokens` against a spec that includes `token BODY '<<<' '>>>'`.
3. Observe a crash (AttributeError or similar) instead of a formatted error record.

## Notes

`UnclosedBlockError` should be routed through `format_error_record` (like `LexError`) in `tokens_cli.py`, or the CLI should raise it as a hard error. The error type carries `line`, `column`, and `rule` fields sufficient to produce a useful error message.

Discovered during review of issue-060 (block lexical rule implementation).
