# 179 — describe the `arbno` section in the ll1 output schema

**Date:** 2026-07-29
**Issue:** [179](../issues/done/179-ll1-schema-omits-arbno-section.md)

## Problem

`plcc-ll1` always emits a top-level `arbno` key. `build_ll1_result` in
[ll1_result_builder.py](../../src/plcc/ll1/ll1_result_builder.py) builds it
unconditionally and returns it alongside `parse_table` and the rest — `{}` when
the grammar has no repetition rules, otherwise one entry per `**=` nonterminal.

[ll1.schema.json](../../src/plcc/schemas/ll1.schema.json) never mentions it. The
key is absent from both `required` and `properties`. No schema in
`src/plcc/schemas/` sets `additionalProperties: false`, so the undeclared key is
silently accepted, and every `check-jsonschema --schemafile ll1.schema.json`
call in the test suite validates the entire `arbno` section as "anything goes."
A malformed, truncated, or wrong-shaped `arbno` passes.

That is the section carrying repetition-rule parse data: the `rhs` symbol list,
the separator, and the computed `lookahead`. Issue
[#174](../issues/done/174-arbno-drops-mid-body-terminal.md)'s bug lived exactly
there — a non-capturing terminal dropped from `rhs`, and a `lookahead` computed
from the wrong symbol — and schema validation could not have caught it. Issue
[#176](../issues/done/176-integration-tier-has-no-arbno-coverage.md) added
integration assertions for that shape with `python3 -c`, precisely because the
schema was blind to it.

## Approach

Declare the section the emitter already produces. The shape is fixed by two
functions and needs no negotiation:

- `_handle_arbno` in
  [spec_json_decoder.py](../../src/plcc/ll1/spec_json_decoder.py) builds
  `arbno_rules[nt] = {"rhs": [...], "separator": ...}`, where each `rhs` entry is
  `{"field": str | None, "symbol": str, "is_terminal": bool}` and `separator` is
  the separator token's name or `None`.
- `build_ll1_result` merges each entry with a computed
  `"lookahead": list[str]`.

So the schema addition is descriptive, not prescriptive: no production code
changes, and no output changes. Only the description was missing.

The one design question with real weight is how to prove the new clause
constrains anything. A schema addition that no test can distinguish from its
absence is indistinguishable from not making it. The suite has no negative
schema test anywhere today, so that pattern gets established here: take real
`plcc-ll1` output, delete one required key, and assert `check-jsonschema`
rejects it.

Two alternatives were considered and rejected:

- **Assert only the issue's repro** (delete `arbno.<nt>.lookahead`). Cheapest,
  but leaves the `separator` and `rhs`-item clauses unproven — three of the
  seven required keys would be asserted by no test at all.
- **Validate in a Python unit test** with the `jsonschema` library, which would
  run in the millisecond TDD loop rather than in bats. Rejected on two counts:
  `jsonschema` is not a declared dependency (it arrives transitively under
  `check-jsonschema`), and validating with a different implementation than the
  one the suite actually runs would prove the schema against the wrong
  validator.

## Design

### Schema

Add `"arbno"` to the top-level `required` array, and this to `properties`:

```json
"arbno": {
  "type": "object",
  "additionalProperties": {
    "type": "object",
    "required": ["rhs", "separator", "lookahead"],
    "properties": {
      "rhs": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["symbol", "field", "is_terminal"],
          "properties": {
            "symbol":      { "type": "string" },
            "field":       { "type": ["string", "null"] },
            "is_terminal": { "type": "boolean" }
          }
        }
      },
      "separator": { "type": ["string", "null"] },
      "lookahead": { "type": "array", "items": { "type": "string" } }
    }
  }
}
```

Three decisions embedded there:

- **`arbno` is `required`, not optional.** The emitter always returns the key;
  `{}` for a grammar with no repetition rules is still the key present with an
  empty value, not the key absent.
- **Nullable keys are still `required`.** `field` and `separator` are typed
  `["string", "null"]` and listed in `required`. Requiredness and nullability
  are separate axes, and the file already draws them that way — the
  `parse_table` and `conflicts` production items require `field` while typing it
  nullable.
- **No `additionalProperties: false`.** Per the issue: none of the five schemas
  in `src/plcc/schemas/` use it, and adding it here would be an unrelated
  tightening with its own blast radius. The `additionalProperties: {…}` map form
  used to key by nonterminal is the same idiom `first_sets`, `follow_sets`, and
  `parse_table` already use.

### Tests

All tests go in the existing
[tests/bats/commands/plcc-ll1.bats](../../tests/bats/commands/plcc-ll1.bats).
This is the narrowest tier that can produce real output with a non-empty
`arbno`: the schema is `plcc-ll1`'s own output contract, and the file's
`setup()` already establishes the precedent of building input with `plcc-spec`
before invoking the command under test.

`setup()` gains one line — a second spec JSON built from
`tests/fixtures/arbno-mid-body-terminal.plcc`. That fixture's `Decls` entry is
the only one that exercises every value shape at once:

```json
"Decls": {
  "rhs": [
    { "field": "symbolList", "symbol": "SYMBOL", "is_terminal": true  },
    { "field": null,         "symbol": "EQUALS", "is_terminal": true  },
    { "field": "expList",    "symbol": "Exp",    "is_terminal": false }
  ],
  "separator": null,
  "lookahead": ["SYMBOL"]
}
```

Both `true` and `false` for `is_terminal`, a populated and a null `field`, and a
null `separator`. The existing `trivial.plcc` spec in `setup()` yields
`"arbno": {}` and is useless as a subject.

| # | Test | Assertion |
|---|---|---|
| 1 | Positive control | `plcc-ll1` output for the repetition grammar exits 0 and validates against the schema |
| 2 | Negative, loop-driven | For each of the seven required keys, the output with that key deleted is **rejected** |

Test 1 is not redundant with the integration tier's schema-valid assertions. It
is the control for test 2: without it, every mutant could be rejected for a
reason unrelated to the deleted key, and test 2 would pass while proving
nothing. It also pins the accepting half of the nullable-but-required decision —
`Decls` carries `field: null` and `separator: null`, and those must validate.

Test 2 covers all seven required keys the new clause introduces:

```text
arbno
arbno.Decls.rhs
arbno.Decls.separator
arbno.Decls.lookahead
arbno.Decls.rhs.0.symbol
arbno.Decls.rhs.0.field
arbno.Decls.rhs.0.is_terminal
```

Index `0` is `SYMBOL`, whose `field` is the non-null `"symbolList"`. JSON
Schema's `required` does not distinguish null from non-null values, so deleting
the one entry that has a value is sufficient; the null-valued `field` at index
`1` is covered by test 1's accepting direction.

Mechanically the test mirrors the existing loop at
[spec-ll1.bats:99-115](../../tests/bats/integration/spec-ll1.bats#L99-L115):
`for` over cases, the case passed to `python3` through the environment. Two
deliberate differences:

- Each mutant is written to a file under `BATS_TEST_TMPDIR` and passed to
  `check-jsonschema` **by path**, not piped. No JSON is ever interpolated into a
  shell string.
- The deleter walks a dotted path, treating an integer segment as a list index,
  and lets `del` raise on a path that does not exist. A typo'd path therefore
  fails the test through a non-zero `python3` exit rather than silently emitting
  an unmutated document.

Per CONTRIBUTING, no `mktemp` and no `teardown` — bats creates and removes
`BATS_TEST_TMPDIR` per test.

## Testing

Run with `bin/test/commands.bash tests/bats/commands/plcc-ll1.bats`.

**Red proof comes first.** Test 2 is written and run against the *unmodified*
schema, where all seven deletions must be accepted — so the test must fail, and
must fail on the first path in the loop. A test that goes green only after the
schema lands is the whole point of the exercise; one that was green before it
would mean the loop is measuring something else. Test 1 passes before and after,
as a control should.

Then `bin/test/integration.bash tests/bats/integration/spec-ll1.bats`, to
confirm the four schema-valid assertions already there still pass against the
now-stricter schema. Those tests validate real output from all three repetition
fixtures; if the new clause misdescribes the emitted shape, that is where it
shows.

`bin/test/functional.bash` runs before the branch is pushed. No runtime code
loads `src/plcc/schemas/` — the schemas are consumed only by `check-jsonschema`
in the bats tiers — so no packaging or e2e concern follows from editing one.

## Consequences

- Two test files validate against this schema today:
  `tests/bats/commands/plcc-ll1.bats` (two calls) and
  `tests/bats/integration/spec-ll1.bats` (four). The four in `spec-ll1.bats`
  start constraining the `arbno` section for free, across all three repetition
  fixtures — a regression that mangles `rhs` *shape* (rather than its contents)
  now reds there without anyone writing an assertion for it. The two in
  `plcc-ll1.bats` run on `trivial.plcc`, whose `arbno` is `{}`; they gain only
  the top-level presence check.
- The suite gains its first negative schema test. Issue
  [#180](../issues/done/180-ll1-schema-omits-conflict-type.md) is the same class of
  gap in the `conflicts` section and can follow the pattern established here.
- The schema still describes `arbno` structurally, not semantically. It cannot
  see a `lookahead` computed from the wrong symbol, or a symbol dropped from
  `rhs` — both stay well-formed. The integration assertions added by #176 remain
  the guard for those, and this change does not replace them.
- The change touches `src/`, so the issue is typed `fix` rather than `test` and
  a `fix(schema): …` commit bumps the patch version. Its user-visible effect is
  nil — no runtime code reads the schema — so there is no
  `docs/whats-new.md` entry.
