# FOLLOW set nullable-tail design

**Date:** 2026-08-12
**Issue:** [188](../issues/done/188-follow-set-omits-nullable-tail.md) (FOLLOW set omits the nullable tail, breaking empty alternatives)
**Approach:** single commit, one-method fix

## Scope

`FollowSetBuilder._updateWithSingleOccuranceOfNonterminalInProduction` in
`src/plcc/spec/syntax/validations/ll1/build_follow_sets.py` under-computes
FOLLOW sets: when a nonterminal is followed by a nullable symbol, it adds
FIRST of only that one next symbol instead of walking forward through every
nullable symbol until it reaches one that cannot derive empty. Empty
alternatives whose predict set depends on the resulting FOLLOW set silently
lose parse-table entries, while `plcc-ll1` still reports `is_ll1: true`.

Nullability data itself is already correct — `build_first_sets.py` computes
it existentially across all of a nonterminal's alternatives, and
`_canDeriveEmpty` in `build_follow_sets.py` already reuses those FIRST sets
rather than re-deriving nullability. No changes are needed there. This is
purely a control-flow fix in the one method above.

Distinct from issue [170](../issues/done/170-arbno-follow-set-missing-eof.md),
which fixed nullability being tested against only a nonterminal's
first-registered production. That fix already landed; this is the separate
forward-walk defect in the same function.

## What changes

**`src/plcc/spec/syntax/validations/ll1/build_follow_sets.py`**

Replace the `else` branch of `_updateWithSingleOccuranceOfNonterminalInProduction`
(currently: add FIRST of the immediate next symbol, then separately check
whether the *entire remainder* is nullable) with a forward walk from
`index + 1`: add FIRST (minus epsilon) of each subsequent symbol, stopping at
the first one that cannot derive empty. If every symbol from `index + 1`
onward is nullable, also add FOLLOW(lhs) — the standard textbook algorithm.

```python
else:
    for j in range(index + 1, len(rules)):
        self._addFirstOfNextSymbol(rules[j], nonterminal)
        if not self._canDeriveEmpty([rules[j]]):
            break
    else:
        self._addFollowOfLHS(lhs, nonterminal)
```

Both helper methods used here (`_addFirstOfNextSymbol`, `_canDeriveEmpty`)
are unchanged; only the control flow around them changes.

**`src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py`**

Add one unit test at the `build_follow_sets` level, per the issue's
suggested minimal grammar:

- `test_follow_set_walks_past_nullable_symbol_to_next_non_nullable`:
  `S -> A B C`, `A -> a | ε`, `B -> b | ε`, `C -> c`. Asserts
  `FOLLOW(A) == {'b', 'c'}` (not `{'b'}`).

No end-to-end/bats regression test — the defect is fully isolated and
exercised at the `build_follow_sets` level, and the issue's own author
recommended the unit test as the primary regression guard.

The pre-existing `test_derive_empty` test's expected `follows["exp"]` and
`follows["word"]` also gained `"TWO"` as a direct, correct consequence of
this fix — the old expected values encoded the pre-fix under-approximation
being corrected here.

## Out of scope

- The end-to-end `ClassDecl` grammar repro from the issue's "Steps to
  Reproduce" — useful for manual verification, not added as an automated
  test.
- Any change to `build_first_sets.py`, `Grammar.py`, or nullability
  computation — already correct.
- Issue [187](../issues/187-rep-lacks-output-and-clean-exit-records.md) and
  [186](../issues/186-rep-deadlocks-on-partial-stdout-line.md) — unrelated
  `plcc-rep` issues, not touched here.

## Commit message

```
fix(ll1): walk forward through nullable symbols when computing FOLLOW sets

FOLLOW-set computation added FIRST of only the immediate next symbol
after a nonterminal occurrence, then jumped straight to checking
whether the entire remainder was nullable — skipping every symbol in
between. A nonterminal followed by one nullable symbol and then a
non-nullable one lost the non-nullable symbol's FIRST set entirely,
silently truncating FOLLOW and dropping parse-table entries for empty
alternatives.
```
