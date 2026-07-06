# Design: Thread altName through the LL(1) pipeline (issue 045)

**Date:** 2026-05-26
**Issue:** [045 — Alternative class name lost in LL(1) pipeline](../issues/done/045-altname-lost-in-ll1-pipeline.md)

## Problem

When a PLCC grammar uses the alternative class syntax (`<expr>:Add ::= ...`), every parse tree
node is emitted with `"rule": "expr"` (the base nonterminal) instead of `"rule": "Add"` (the
alternative class name). The Java deserializer maps every node to a single class, producing wrong
runtime behavior.

The `altName` field is present in `spec.json` under `rule["lhs"]["altName"]`, but
`spec_json_decoder.decode()` never reads it, so it never reaches the parse table or the parser.

## Data model

Introduce a `Rule` dataclass in `spec_json_decoder.py`:

```python
@dataclass
class Rule:
    alt: str | None          # node class name (e.g. "Add"); None means use the nonterminal name
    fields: list[str | None] # per-symbol field names; None means the symbol is elided
```

This replaces the current `field_map: {(nt, prod_tuple): list[str|None]}` with
`productions: {(nt, prod_tuple): Rule}`. The two pieces of per-production metadata — field names
and alt name — are unified into one object rather than carried as parallel dicts with the same key.

`Rule` is defined in `spec_json_decoder.py` and imported by `ll1_result_builder.py`. It is a
Python-only internal object; it is never serialized to JSON.

## Parse table cell format

Each cell in `parse_table` (and each entry in `conflicts[*].productions`) changes from a bare
list to a dict:

**Before:**
```json
[{"symbol": "PLUS", "field": null}, {"symbol": "expr", "field": "left"}]
```

**After:**
```json
{"alt": "Add", "production": [{"symbol": "PLUS", "field": null}, {"symbol": "expr", "field": "left"}]}
```

`"alt"` is always present. It is `null` when the rule has no alternative class name, in which
case the parser uses the nonterminal name for the tree node. The same cell shape is used for
both `parse_table` entries and `conflicts` entries — both go through `_prod_entry`.

## Layer changes

### `spec_json_decoder.py`

- Define the `Rule` dataclass.
- `decode()` reads `rule["lhs"]["altName"]` for each rule and constructs
  `Rule(alt=altName, fields=[...])`, storing it in `productions` under `(nt, prod_tuple)`.
- `_handle_arbno()` writes only to `arbno_rules`; it does not add entries to `productions` (arbno rules are handled by a separate codepath in the parser and do not need `Rule` metadata).
- Return remains a 3-tuple: `(grammar, productions, arbno_rules)`.

### `ll1_result_builder.py`

- `build_ll1_result(grammar, productions, arbno_rules=None)` — parameter renamed from
  `field_map` to `productions`.
- `_prod_entry(nt, prod, productions, eps)` looks up `productions.get((nt, prod))` to obtain the
  `Rule`, then builds `{"alt": rule.alt, "production": [...]}`.
- No change to `build_ll1_result`'s return signature or the rest of the output structure.

### `predictive_parser.py`

Two lines change in `_parse_regular()`:

```python
# Before
builder = NodeBuilder(sym)
for entry in production:

# After
builder = NodeBuilder(production.get("alt") or sym)
for entry in production["production"]:
```

No other changes to the parser.

### `ll1_cli.py`

No changes. `decode()` still returns a 3-tuple; the rename from `field_map` to `productions`
is internal to the two modules that use it.

## Test changes

### `spec_json_decoder_test.py`

- All assertions on `field_map` values update to assert `Rule` objects:
  `productions[("E", ("NUM",))] == Rule(alt=None, fields=["num"])`.
- New tests covering rules where the LHS has an `altName` set, asserting `rule.alt == "Add"`.

### `ll1_result_builder_test.py`

- Fixture helpers build `productions` with `Rule` values instead of bare lists.
- Cell-format assertions update to the new shape, e.g.:
  `{"alt": None, "production": [{"symbol": "NUM", "field": None}]}`.
- The epsilon cell (`== []`) becomes `{"alt": None, "production": []}`.

### `predictive_parser_test.py`

- All inline `_*_LL1` fixtures update their cell values to the new dict shape.
- New test: grammar with alt names asserts `tree["rule"] == "Add"` not `"expr"`.

### `table_cli_test.py`

- All inline `_*_LL1` fixtures update their cell values to the new dict shape.
- No logic changes.

## Files changed

| File | Change |
|------|--------|
| `src/plcc/ll1/spec_json_decoder.py` | Define `Rule`; build `productions`; read `altName` |
| `src/plcc/ll1/ll1_result_builder.py` | Consume `productions`; new cell format in `_prod_entry` |
| `src/plcc/parser/predictive_parser.py` | Use `cell["alt"]` and `cell["production"]` |
| `src/plcc/ll1/spec_json_decoder_test.py` | Assert `Rule` objects; add altName tests |
| `src/plcc/ll1/ll1_result_builder_test.py` | Update fixtures and cell assertions |
| `src/plcc/parser/predictive_parser_test.py` | Update fixtures; add alt-name tree test |
| `src/plcc/parser/table_cli_test.py` | Update fixtures |
