# 045 - Alternative class name lost in LL(1) pipeline

**Type:** bug
**Date:** 2026-05-26

## Description

When a PLCC grammar uses the alternative class syntax (`<expr>:Add ::= ...`), all parse tree
nodes are emitted with `"rule": "expr"` (the base nonterminal name) instead of `"rule": "Add"`
(the alternative class name). The Java deserializer then maps every node to a single class,
producing wrong runtime behavior.

**Reproduction:** Use the Activity 3 prefix-expression grammar from the workshops. Enter
`+ 2 3`. Expected: `Add\n5`. Actual: `Div\n0` (or similar wrong class and value).

Inspecting `plcc-trees` output confirms all nodes carry `"rule": "expr"`.

## Root Cause

The `altName` field **is** present in `spec.json` under `rule["lhs"]["altName"]`, but
`spec_json_decoder.decode()` (`src/plcc/ll1/spec_json_decoder.py`) never reads it.
As a result:

- `ll1.json` parse table has no alt name information — each cell is just a list of RHS symbols.
- `predictive_parser.py` constructs `NodeBuilder(sym)` where `sym` is always the base
  nonterminal (`"expr"`), never the alternative class name.

The fix requires threading `altName` through three layers:

1. `spec_json_decoder.py` — collect an `alt_map: {(nt, prod_tuple): altName}` and return it.
2. `ll1_result_builder.py` — include `"alt"` in each parse table cell
   (changing cell format from a bare list to `{"alt": "Add", "production": [...]}`).
3. `predictive_parser.py` — use `cell["alt"]` when constructing `NodeBuilder`.

Tests in `spec_json_decoder_test.py`, `ll1_result_builder_test.py`,
`predictive_parser_test.py`, and `table_cli_test.py` need updating for the new cell format.
