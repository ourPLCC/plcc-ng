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

The root cause: the `set` was chosen to store productions per cell, but deduplication is
exactly the bug. Two rules with identical bodies are still two distinct alternatives — and
that is a conflict.

## Design

### 1. `TableBuilder` — list instead of set, predict set computed explicitly

Change `_rawTable` from `defaultdict(set)` with `.add()` to `defaultdict(list)` with
`.append()`. Every rule that maps to a cell appends its production body, including
duplicates across rules. `len(cell)` is then the rule count directly.

Replace the two existing methods `_addProductionForEachTerminalInFirst` and
`_addProductionForEachFollowIfEpsilonInFirst` with a single `_predictSet` method that
computes the full set of lookahead terminals for a rule before touching the table:

```python
def _updateCellsForEachRule(self):
    for nonterm, prod in self._grammar.getRulesIterator():
        for t in self._predictSet(nonterm, prod):
            self._rawTable[(nonterm, t)].append(prod)

def _predictSet(self, nonterm, prod):
    terminals = set(self._FIRST[prod]) - {self._grammar.getEpsilon()}
    if self._grammar.getEpsilon() in self._FIRST[prod]:
        terminals |= self.FOLLOW[nonterm]
    return terminals
```

This approach is necessary for two reasons:

1. **FIRST/FOLLOW overlap**: if `FIRST(α)` contains both ε and a terminal `t` that is also
   in `FOLLOW(A)`, the old two-method approach would append the same production to cell
   `(A, t)` twice — once via FIRST, once via FOLLOW. With a set this was harmless
   deduplication; with a list it is a false conflict. Computing the predict set as a Python
   `set` first and then appending once per terminal eliminates the overlap.

2. **ε leaking into the table**: the old `_addProductionForEachTerminalInFirst` iterated
   over `FIRST[prod]` without filtering out ε, so ε itself could be inserted as a table key.
   The new `_predictSet` explicitly excludes ε.

The predict set formula — `FIRST(α) \ {ε}`, plus `FOLLOW(A)` when `ε ∈ FIRST(α)` — is
the standard LL(1) definition, now stated directly in code.

### 2. `Table.getCell` — returns a list

`getCell(X, a)` now returns a `list[tuple]` instead of a `set[tuple]`. The list preserves
one entry per contributing rule, so `len(cell)` is the rule count directly.

### 3. `check_parsing_table_for_ll1` — unchanged condition, correct semantics

The condition `len(parsingTable.getCell(X, a)) > 1` is unchanged. It now fires correctly
for identical-body rules because the list does not deduplicate. Pass both the count and the
distinct productions to `LL1Error`:

```python
cell_entries = parsingTable.getCell(X, a)
if len(cell_entries) > 1:
    LL1Error(
        cell=(X, a),
        production=set(cell_entries),
        count=len(cell_entries)
    )
```

### 4. `LL1Error` — add `count` field

Add `count: int` parameter to `__init__`. Update the message:

```python
self.message = f"{count} rules in parsing table cell {cell}: {production}"
```

For non-identical conflicts: `count=2`, `production={'A', 'B'}`.
For identical-body conflicts: `count=2`, `production={('IDENT',)}` — count makes the
conflict clear even though the set has one element.

## Tests

### `build_parsing_table_test.py`

- Update existing assertions to compare `set(table.getCell(...))` to the expected set of
  productions, since `getCell` now returns a list and order is not guaranteed.
- Add a case where two rules have identical bodies mapping to the same cell: assert
  `len(table.getCell(...)) == 2`.
- Add a case where a rule's FIRST set contains ε and a terminal `t` that is also in
  FOLLOW — assert no false conflict (cell has exactly one entry for that rule).

### `check_parsing_table_for_ll1_test.py`

- Update `Table` constructions to pass lists instead of sets for cell values.
- Add a case: cell with two identical production bodies → conflict reported with `count=2`
  and a one-element `production` set.
- Existing assertions on `errors[0].production == {'V', 'E'}` remain valid since
  `production=set(cell_entries)`.

### `check_ll1_test.py`

- Add an end-to-end test with a grammar where two alternatives have identical predict sets.
- Assert `check_ll1` returns at least one error.

## Files Changed

- `src/plcc/spec/syntax/LL1Error.py` — add `count` field
- `src/plcc/spec/syntax/validations/ll1/build_parsing_table.py` — `defaultdict(list)` + `.append()`; replace two add-methods with `_predictSet`; `getCell` returns list
- `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1.py` — pass `count` and `set(cell)` to `LL1Error`
- `src/plcc/spec/syntax/validations/ll1/build_parsing_table_test.py` — update for list semantics; add identical-body and FIRST/FOLLOW overlap tests
- `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py` — update `Table` constructions, add identical-body test
- `src/plcc/spec/syntax/validations/ll1/check_ll1_test.py` — add identical-predict-set end-to-end test
