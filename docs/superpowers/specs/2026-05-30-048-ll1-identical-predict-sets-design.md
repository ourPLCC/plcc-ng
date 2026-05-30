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

### 1. `TableBuilder` — list instead of set

Change `_rawTable` from `defaultdict(set)` with `.add()` to `defaultdict(list)` with
`.append()`. Every rule that maps to a cell appends its production body, including
duplicates. No other logic changes in `TableBuilder`.

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

- Update existing assertions to use list equality or `len`/`set` comparisons where
  previously set equality was assumed.
- Add a case where two rules have identical bodies: assert the cell list has two entries.

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
- `src/plcc/spec/syntax/validations/ll1/build_parsing_table.py` — `defaultdict(list)` + `.append()`; `getCell` returns list
- `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1.py` — pass `count` and `set(cell)` to `LL1Error`
- `src/plcc/spec/syntax/validations/ll1/build_parsing_table_test.py` — update for list semantics, add identical-body test
- `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py` — update `Table` constructions, add identical-body test
- `src/plcc/spec/syntax/validations/ll1/check_ll1_test.py` — add identical-predict-set end-to-end test
