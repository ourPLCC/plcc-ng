# Design: Fix LL(1) Conflict Detection for Identical Predict Sets (Issue 048)

**Date:** 2026-05-30
**Branch:** fix/048-ll1-conflict-detection-misses-identical-predict-sets

## Problem

When two alternatives for the same non-terminal have identical predict sets, the LL(1)
conflict detector reports no conflict. For example:

```text
<expr>:Var   ::= <IDENT>
<expr>:Const ::= <IDENT>
```

Both alternatives produce the same production body `(<IDENT>,)`. Because `build_parsing_table`
stores productions in a `set`, the second `.add()` is a no-op — the set collapses to one
entry. `check_parsing_table_for_ll1` only flags cells where `len(set) > 1`, so the conflict
is never detected and `Var` is silently discarded.

The root cause: conflict detection is based on the number of *distinct production bodies*
in a cell, but it should be based on the number of *rules (alternatives)* that map to the cell.

## Design

### 1. `TableBuilder` — parallel rule-count dict

Add `_ruleCounts: defaultdict(int)` alongside the existing `_rawTable: defaultdict(set)`.

Every time a rule maps a production to a cell — in both
`_addProductionForEachTerminalInFirst` and `_addProductionForEachFollowIfEpsilonInFirst`
— increment `_ruleCounts[(nonterm, t)]` in addition to updating `_rawTable[(nonterm, t)]`.

Both dicts are passed to `Table` on construction.

### 2. `Table` — expose rule count

`Table.__init__` accepts a second argument `ruleCounts: dict`. Add method:

```python
def getRuleCount(self, X: object, a: object) -> int:
    return self._ruleCounts[(X, a)]
```

`getKeys()` is unchanged — both dicts share the same key space.

### 3. `check_parsing_table_for_ll1` — use rule count for detection

Change the conflict condition from:

```python
if len(parsingTable.getCell(X, a)) > 1:
```

to:

```python
if parsingTable.getRuleCount(X, a) > 1:
```

Pass the count to `LL1Error`:

```python
LL1Error(
    cell=(X, a),
    production=parsingTable.getCell(X, a),
    count=parsingTable.getRuleCount(X, a)
)
```

### 4. `LL1Error` — add `count` field

Add `count: int` parameter to `__init__`. Update the message:

```python
self.message = f"{count} rules in parsing table cell {cell}: {production}"
```

For non-identical conflicts: `count=2`, `production={'A', 'B'}` — same information as
before, plus explicit count.

For identical-body conflicts: `count=2`, `production={('IDENT',)}` — the one-element set
combined with `count=2` makes the conflict clear.

## Tests

### `build_parsing_table_test.py`

- Add a case where two rules have identical bodies mapping to the same cell.
- Assert `getRuleCount(nonterm, terminal) == 2`.

### `check_parsing_table_for_ll1_test.py`

- Update existing `Table` constructions to pass a `ruleCounts` dict.
- Add a case: cell with one production body but `ruleCount=2` → conflict reported with
  `count=2` and a one-element `production` set.
- Existing assertions on `errors[0].production` remain valid; add assertions on
  `errors[0].count`.

### `check_ll1_test.py`

- End-to-end test with a grammar that has two alternatives with identical predict sets
  (e.g., `<expr>:Var ::= <IDENT>` / `<expr>:Const ::= <IDENT>`).
- Assert `check_ll1` returns at least one error.

## Files Changed

- `src/plcc/spec/syntax/LL1Error.py` — add `count` field
- `src/plcc/spec/syntax/validations/ll1/build_parsing_table.py` — add `_ruleCounts`, pass to `Table`; `Table` gains `getRuleCount`
- `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1.py` — use `getRuleCount` for detection, pass count to `LL1Error`
- `src/plcc/spec/syntax/validations/ll1/build_parsing_table_test.py` — new test for identical-body rules
- `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py` — update `Table` constructions, new identical-body test
- `src/plcc/spec/syntax/validations/ll1/check_ll1_test.py` — end-to-end identical-predict-set test
