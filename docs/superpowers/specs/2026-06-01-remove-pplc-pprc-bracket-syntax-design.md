# Design: Remove %%{ / %%} block delimiter syntax (issue 051)

## Summary

Remove the asymmetric `%%{` / `%%}` block delimiter syntax from the spec parser.
After this change only `%%%` is a block delimiter. Lines containing `%%{` or `%%}`
are treated as ordinary non-block lines and pass through the parser unchanged.

## Scope

All changes are confined to one module and its test file:

- `src/plcc/spec/rough/parse_blocks.py`
- `src/plcc/spec/rough/parse_blocks_test.py`

No new classes, no new error types, no changes to `BlockParser` or the `handler`
mechanism.

## Changes to `parse_blocks.py`

Remove the two compiled patterns and the `brackets` dict entry that reference them:

```python
# Remove these three lines:
PPLC = re.compile(r'^%%{(?:\s*#.*)?$')
PPRC = re.compile(r'^%%}(?:\s*#.*)?$')
# and the PPLC: PPRC entry in brackets
```

After the change `brackets` contains only the single entry `{PPP: PPP}`.

## Changes to `parse_blocks_test.py`

Remove the three tests that assert `%%{`/`%%}` are block delimiters:

- `test_curly_percent_block` (line 53)
- `test_nested_blocks_produce_single_block` (line 62)
- `test_mixed` (line 75) — remove entirely; its `%%%`-only behaviour is already
  covered by `test_triple_percent_block`

Add two tests asserting the pass-through behaviour:

- `test_pplc_is_a_plain_line` — a `%%{` line is yielded unchanged, no block formed
- `test_pprc_is_a_plain_line` — a `%%}` line is yielded unchanged, no block formed

## Backwards compatibility

This is a deliberate breaking change. Grammars that use `%%{`/`%%}` will need to
migrate to `%%%`. No migration tooling is provided at this time.

## Out of scope

- Error messages guiding users to migrate (`"use %%% instead of %%{ / %%}"`)
- Migration tooling
- Changes to any other module
