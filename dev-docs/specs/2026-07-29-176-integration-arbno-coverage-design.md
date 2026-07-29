# 176 — integration coverage for repetition rules at the `plcc-spec | plcc-ll1` boundary

**Date:** 2026-07-29
**Issue:** [176](../issues/done/176-integration-tier-has-no-arbno-coverage.md)

## Problem

`tests/bats/integration/` contains no repetition-rule (`**=`, internally
"arbno") coverage at all. Grammars using `**=` appear only in
`tests/bats/e2e/plcc-rep.bats`, which runs the entire
`plcc-spec | plcc-make | plcc-<lang>-emit | run` pipeline and asserts on
evaluated program output.

That leaves the `plcc-spec | plcc-ll1` boundary — where a decoded spec becomes
an LL(1) table, and where the per-repetition `arbno` metadata is computed —
covered at only two removes from itself: at the unit level
(`src/plcc/ll1/ll1_result_builder_test.py`, in-memory `Grammar` objects, no
subprocess) and at the e2e level (whole pipeline, asserting on `[1, 2, 3]`).

Issue [174](../issues/done/174-arbno-drops-mid-body-terminal.md)'s bug lived
exactly in that gap. `_handle_arbno` in
[spec_json_decoder.py](../../src/plcc/ll1/spec_json_decoder.py) built the
runtime `arbno.<nt>.rhs` list from capturing symbols only, silently dropping
every non-capturing terminal in a repetition body. The grammar still analyzed
as LL(1) (`is_ll1: true`, `conflicts: []`), so nothing complained until parse
time. A regression of that shape today is caught only by the e2e tier, which
reports it as a wrong evaluated value several stages downstream of the defect.

The `arbno` section is also where the repetition **lookahead** is computed, and
the two failure modes travel together: a dropped leading terminal both mangles
`rhs` and shifts `lookahead` onto the wrong symbol.

## Approach

Add targeted tests at the boundary itself: run `plcc-spec | plcc-ll1` as a
composed pipeline and assert directly on the `arbno` section of the resulting
JSON. This is the narrowest tier that can observe the defect — a unit test does
not exercise spec decoding through the CLI contract, and the e2e tier observes
it only as a downstream symptom.

Three repetition shapes are covered, because they are three distinct paths
through `_handle_arbno`:

| Shape | Grammar | Why it is distinct |
|---|---|---|
| Separator | `<Rands> **= <Expr:expr> +COMMA` | Separator branch; `rhs` is all-capturing, so #174 never touched it |
| Interior terminal | `<Decls> **= <SYMBOL> EQUALS <Exp>` | No separator; non-capturing terminal *between* two capturing symbols |
| Leading terminal | `<Items> **= BANG <Exp>` | No separator; non-capturing terminal *first*, so it corrupts `lookahead` too |

The first two have fixtures already. The third does not, and it is the shape
the issue names explicitly — so it needs one.

Two alternatives were considered and rejected:

- **Reuse the existing fixtures only.** Cheaper, but leaves the leading-terminal
  shape — the one that also corrupts `lookahead` — untested at every tier except
  the unit level.
- **Assert via JSON Schema.** `plcc-ll1`'s output schema does not describe the
  `arbno` section at all, so `check-jsonschema` validates it as "anything goes."
  Fixing that means editing `src/plcc/schemas/ll1.schema.json`, which changes the
  shipped package and reclassifies this issue away from `test`. Split out as
  [#179](../issues/done/179-ll1-schema-omits-arbno-section.md); a sibling gap in the
  `conflicts` section is [#180](../issues/180-ll1-schema-omits-conflict-type.md).
  This design therefore asserts structure with `python3 -c`, the same technique
  `spec-model.bats` already uses for `start`.

## Design

### New fixture

`tests/fixtures/arbno-leading-terminal.plcc`:

```
token BANG '!'
token NUM  '\d+'
skip  SPACE '\s+'
%
<Program> ::= <Items:items>
<Items>   **= BANG <Exp>
<Exp>     ::= <NUM:num>
```

Grammar only — no `%`-delimited semantics section. The fixture feeds
`plcc-spec` and stops there, so a language block would be unused weight.
`tests/fixtures/trivial.plcc` sets that precedent; the two existing arbno
fixtures carry Python sections only because the e2e tier evaluates them.

### Tests

All tests go in the existing `tests/bats/integration/spec-ll1.bats`. The
integration tier names one file per pipeline boundary — `spec-ll1`,
`spec-model`, `tokens-tree` — and these tests are at the boundary that file
already owns. It currently holds a single test, so it stays readable.

The file's existing `setup()` (`FIXTURES`, `LL1_SCHEMA`) needs no change.

| # | Fixture | Assertion |
|---|---|---|
| 1 | `trivial-arbno` | Pipeline exits 0 and output is schema-valid |
| 2 | `trivial-arbno` | `arbno.Rands` equals the full expected object: `rhs` of one entry (`Expr`/`exprList`/non-terminal), `separator == "COMMA"`, `lookahead == ["NUM", "PLUS"]` |
| 3 | `arbno-mid-body-terminal` | Pipeline exits 0 and output is schema-valid |
| 4 | `arbno-mid-body-terminal` | `arbno.Decls.rhs` equals the full expected three-entry list, with `EQUALS` (`field: null`, `is_terminal: true`) between `SYMBOL` and `Exp` |
| 5 | `arbno-mid-body-terminal` | `arbno.Decls.lookahead == ["SYMBOL"]` |
| 6 | `arbno-leading-terminal` | Pipeline exits 0 and output is schema-valid |
| 7 | `arbno-leading-terminal` | `arbno.Items.rhs` equals the full expected two-entry list, `BANG` first |
| 8 | `arbno-leading-terminal` | `arbno.Items.lookahead == ["BANG"]` |
| 9 | all three | Neither the repetition nonterminal nor its desugared continuation (`Rands`/`Rands#`, `Decls`/`Decls#`, `Items`/`Items#`) appears in `parse_table`, `first_sets`, or `follow_sets` |

Tests 4, 7, and 8 are the #174 regression guards. The two `rhs` tests compare by
whole-list equality rather than spot-checking one entry, so they fail on a
spurious *added* symbol as well as a dropped one.

Test 5 is deliberately **not** a #174 guard, despite asserting the same field as
test 8. In `<Decls> **= <SYMBOL> EQUALS <Exp>` the first body symbol is
capturing, so it survives the pre-fix filter and the lookahead comes out right
even while `rhs` is corrupt. Only a *leading* non-capturing terminal moves the
lookahead. Test 5 is a characterization test; test 8 is the guard.

Test 9 guards a different property: `_handle_arbno` expands each repetition
into right-recursive internal rules (`nt → syms nt#`, `nt# → syms nt# | ε`)
purely to drive LL(1) analysis. Those internal nonterminals are an
implementation detail and must not surface in the emitted table or sets. The
unit tier asserts this for one hand-built grammar; test 9 asserts it for real
decoded specs across all three shapes.

Schema validity (1, 3, 6) is worth asserting even though the schema is blind to
`arbno` — the rest of the document (`parse_table`, `first_sets`, `follow_sets`,
`predict_sets`) is fully described, and no arbno grammar is validated against it
today. Those tests get sharper for free once #179 lands.

## Testing

Run with `bin/test/integration.bash tests/bats/integration/spec-ll1.bats`.

Issue #174 is already fixed on this branch, so every test here passes on
arrival. Passing-on-arrival is not evidence a test detects anything, so the
guards are red-proofed by temporarily restoring the pre-fix behaviour: in
[spec_json_decoder.py](../../src/plcc/ll1/spec_json_decoder.py), the `arbno_rhs`
comprehension gets its old `if s.get("isCapturing", False)` filter back. That
one-line mutation reproduces both symptoms — the non-capturing terminal vanishes
from `rhs`, and, when that terminal led the body, `lookahead` recomputes from
the wrong symbol.

Under the mutation, exactly three tests must fail — 4, 7, and 8 — and every
other test must stay green. A run that reds more or fewer than those three means
the tests are not measuring what this design claims. Revert the mutation
afterwards and confirm all ten pass.

Tests 1, 2, 3, 5, 6, and 9 are characterization tests for behaviour with no
known defect; they are verified by passing against the current implementation.

The full `bin/test/functional.bash` runs before the branch is pushed.

## Consequences

- The `plcc-spec | plcc-ll1` boundary gains repetition coverage across all
  three body shapes, so a #174-class regression fails in the integration tier —
  precisely, on the exact field — instead of surfacing as a wrong evaluated
  value in e2e.
- One new fixture. It is grammar-only, so it cannot be reused by the e2e tier
  without adding a semantics section; that is the right trade until something
  needs it.
- No change to `src/`. Issue 176 stays classified `test` and does not bump the
  release version.
- The schema gaps found while designing this are recorded as
  [#179](../issues/done/179-ll1-schema-omits-arbno-section.md) and
  [#180](../issues/180-ll1-schema-omits-conflict-type.md), not fixed here.
