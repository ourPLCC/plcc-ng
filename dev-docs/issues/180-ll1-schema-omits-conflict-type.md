# 180 - ll1 schema omits conflict_type

**Type:** fix
**Date:** 2026-07-29

## Description

`plcc-ll1` emits a `conflict_type` field on every entry of the
`conflicts` array, but
[ll1.schema.json](../../src/plcc/schemas/ll1.schema.json) does not
declare it. The `conflicts` item schema lists
`required: ["nonterminal", "lookahead", "productions"]` and defines
properties for exactly those three.

Since the schema does not set `additionalProperties: false`, the extra
field is silently accepted and unvalidated. A `conflict_type` that went
missing, changed type, or took an unexpected value would pass schema
validation unnoticed — even though
[format_conflict_message.py](../../src/plcc/ll1/format_conflict_message.py)
branches on it to choose between the FIRST/FIRST and FIRST/FOLLOW
diagnostic wording.

## Steps to Reproduce

1. Write a grammar with an LL(1) conflict:
   ```
   token X 'x'
   token Y 'y'
   skip SPACE '\s+'
   %
   <Program:One> ::= X
   <Program:Two> ::= X Y
   ```
2. Run `plcc-spec conflict.plcc | plcc-ll1` and observe the conflict entry:
   ```json
   {
     "nonterminal": "Program",
     "lookahead": "X",
     "conflict_type": "first_first",
     "productions": [ ... ]
   }
   ```
3. Grep `src/plcc/schemas/ll1.schema.json` for `conflict_type` — no match.

## Notes

- Known values are `first_first` and `first_follow`; unit tests in
  `src/plcc/ll1/ll1_result_builder_test.py` assert both. An `enum` of the
  two is a tighter and more useful declaration than a bare `string`.
- Add it to the conflict item's `required` list — it is emitted on every
  conflict, not conditionally.
- Do **not** add `additionalProperties: false` while fixing this, for the
  same reason as [#179](179-ll1-schema-omits-arbno-section.md): no schema
  in `src/plcc/schemas/` uses it today.
- Found while surveying schema coverage for
  [#176](176-integration-tier-has-no-arbno-coverage.md). Same class of gap
  as [#179](179-ll1-schema-omits-arbno-section.md) — the two could
  reasonably land in one PR.
