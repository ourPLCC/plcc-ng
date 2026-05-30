# Issue 048 — LL(1) Identical Predict Set Conflict Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the LL(1) conflict detector to catch alternatives whose predict sets are identical, and expose the rule count on every conflict error.

**Architecture:** Change `TableBuilder._rawTable` from `defaultdict(set)` to `defaultdict(list)` so each contributing rule appends its production body independently — identical bodies no longer collapse. Replace the two existing add-methods with a single `_predictSet` helper that computes the correct lookahead terminal set per rule (FIRST \ {ε} ∪ FOLLOW when ε ∈ FIRST), which also eliminates both ε-leaking and FIRST/FOLLOW double-counting bugs. Update `LL1Error` to carry a `count` field; `check_parsing_table_for_ll1` derives `count` from `len(entries)` and `production` from `set(entries)`.

**Tech Stack:** Python 3, pytest (via `pdm test`), `bin/test/units.bash` as the TDD runner.

---

## File Map

| Action | Path | Responsibility |
| ------ | ---- | -------------- |
| Modify | `src/plcc/spec/syntax/LL1Error.py` | Add `count` field; update message |
| Modify | `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1.py` | Pass `count` and `set(entries)` to `LL1Error` |
| Modify | `src/plcc/spec/syntax/validations/ll1/build_parsing_table.py` | `defaultdict(list)`, `_predictSet`, remove two old add-methods |
| Modify | `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py` | Add count assertions; update `Table` constructions to use lists; add identical-body test |
| Modify | `src/plcc/spec/syntax/validations/ll1/build_parsing_table_test.py` | Fix set-equality assertions; add identical-body test; add FIRST/FOLLOW overlap test |
| Modify | `src/plcc/spec/syntax/validations/ll1/check_ll1_test.py` | Add identical predict set end-to-end test |

---

## Task 1: Add `count` to `LL1Error` and update `check_parsing_table_for_ll1`

**Files:**

- Modify: `src/plcc/spec/syntax/LL1Error.py`
- Modify: `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1.py`
- Modify: `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py`

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py`:

```python
def test_conflict_reports_count():
    table = Table({
        ('X', 'a'): ['V', 'E']
    })
    errors = check_parsing_table_for_ll1(table)
    assert errors[0].count == 2

def test_identical_productions_in_same_cell_yield_error():
    table = Table({
        ('X', 'a'): ['V', 'V']
    })
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 1
    assert errors[0].cell == ('X', 'a')
    assert errors[0].production == {'V'}
    assert errors[0].count == 2
```

Note: `Table` accepts any dict, including dicts with list values — no change to `Table` is needed yet. `len(['V', 'V']) == 2 > 1` so a conflict is detected; the tests fail only because `LL1Error` lacks a `count` attribute.

- [ ] **Step 2: Run the tests and confirm they fail**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py -v
```

Expected: `AttributeError: 'LL1Error' object has no attribute 'count'`

- [ ] **Step 3: Update `LL1Error` to accept `count`**

Replace the full contents of `src/plcc/spec/syntax/LL1Error.py` with:

```python
from dataclasses import dataclass


@dataclass
class LL1Error:
    def __init__(self, cell, production, count):
        self.cell = cell
        self.production = production
        self.count = count
        self.message = f"{count} rules in parsing table cell {cell}: {production}"
```

- [ ] **Step 4: Update `check_parsing_table_for_ll1` to pass `count` and `set(entries)` to `LL1Error`**

Replace the full contents of `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1.py` with:

```python
from ...LL1Error import LL1Error
from .build_parsing_table import Table


def check_parsing_table_for_ll1(parsingTable: Table) -> list[LL1Error]:
    errorList = []
    for X, a in parsingTable.getKeys():
        entries = parsingTable.getCell(X, a)
        if len(entries) > 1:
            errorList.append(LL1Error((X, a), set(entries), len(entries)))
    return errorList
```

`set(entries)` works correctly whether `entries` is a list or a set: for non-identical productions it gives the full set; for identical productions it collapses to a one-element set. `len(entries)` counts contributing rules regardless.

- [ ] **Step 5: Run the tests and confirm they pass**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Run the full unit suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/spec/syntax/LL1Error.py \
        src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1.py \
        src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py
git commit -m "fix(ll1): add count to LL1Error and pass it from check_parsing_table_for_ll1"
```

---

## Task 2: Fix `build_parsing_table` to use list + `_predictSet`

**Files:**

- Modify: `src/plcc/spec/syntax/validations/ll1/build_parsing_table.py`
- Modify: `src/plcc/spec/syntax/validations/ll1/build_parsing_table_test.py`
- Modify: `src/plcc/spec/syntax/validations/ll1/check_ll1_test.py`

- [ ] **Step 1: Write the failing end-to-end test**

Add to `src/plcc/spec/syntax/validations/ll1/check_ll1_test.py`:

```python
def test_identical_predict_sets_are_ll1_conflict():
    g = Grammar()
    g.addRule('a', ['x'])
    g.addRule('a', ['x'])
    errors = check_ll1(g)
    assert errors
```

- [ ] **Step 2: Write the failing unit test for identical bodies**

Add to `src/plcc/spec/syntax/validations/ll1/build_parsing_table_test.py` (`build_follow_sets` is already imported at the top of that file):

```python
def test_two_rules_with_identical_bodies_produce_two_cell_entries():
    grammar = createGrammar([
        'E x',
        'E x'
    ])
    firsts = build_first_sets(grammar)
    follows = build_follow_sets(grammar, firsts)
    table = build_parsing_table(firsts, follows, grammar)
    assert len(table.getCell('E', 'x')) == 2
```

- [ ] **Step 3: Write the FIRST/FOLLOW overlap regression test**

This test documents that a rule whose predict set is computed via both FIRST and FOLLOW (because ε ∈ FIRST and the same terminal appears in FOLLOW) must appear only once in the cell — not twice. It currently passes with the set-based implementation; it would fail with a naive list change that keeps the two old add-methods. Add to `src/plcc/spec/syntax/validations/ll1/build_parsing_table_test.py`:

```python
def test_first_follow_overlap_does_not_create_false_conflict():
    # Grammar: C → A x | A → B | B → x | B → (epsilon)
    # FIRST(A→B) = {x, ε}; FOLLOW(A) = {x}
    # Rule (A→B) predicts x via both FIRST and FOLLOW — must appear in cell (A,x) only once.
    grammar = createGrammar([
        'C A x',
        'A B',
        'B x',
        'B'
    ])
    firsts = build_first_sets(grammar)
    follows = build_follow_sets(grammar, firsts)
    table = build_parsing_table(firsts, follows, grammar)
    assert len(table.getCell('A', 'x')) == 1
```

- [ ] **Step 4: Run the tests and confirm the new tests fail (and the regression test passes)**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/ll1/check_ll1_test.py \
                    src/plcc/spec/syntax/validations/ll1/build_parsing_table_test.py -v
```

Expected:

- `test_identical_predict_sets_are_ll1_conflict` — FAIL (no conflict detected)
- `test_two_rules_with_identical_bodies_produce_two_cell_entries` — FAIL (`len == 1`, not 2)
- `test_first_follow_overlap_does_not_create_false_conflict` — PASS (already correct with set)
- `test_productions_which_share_both_rule_and_firstSet_terminals_result_in_multiple_cell_entries` — PASS

- [ ] **Step 5: Replace `build_parsing_table.py` with list-based implementation**

Replace the full contents of `src/plcc/spec/syntax/validations/ll1/build_parsing_table.py` with:

```python
from collections import defaultdict

from .Grammar import Grammar


class Table:
    def __init__(self, table):
        self._table = table

    def getCell(self, X: object, a: object) -> list[tuple[object]]:
        return self._table[(X, a)]

    def getKeys(self):
        return self._table.keys()


def build_parsing_table(
        FIRST: dict[object, set[object]],
        FOLLOW: dict[object, set[object]],
        g: Grammar) -> Table:
    b = TableBuilder()
    b.setGrammar(g)
    b.setFIRST(FIRST)
    b.setFOLLOW(FOLLOW)
    return b.build()


class TableBuilder:
    def __init__(self):
        self._grammar = None
        self._FIRST = None
        self._FOLLOWS = None
        self._rawTable = None

    def setGrammar(self, grammar: Grammar):
        self._grammar = grammar

    def setFIRST(self, FIRST: dict[object, set[object]]):
        self._FIRST = FIRST

    def setFOLLOW(self, FOLLOW: dict[object, set[object]]):
        self.FOLLOW = FOLLOW

    def build(self) -> Table:
        self._rawTable = defaultdict(list)
        for nonterm, prod in self._grammar.getRulesIterator():
            for t in self._predictSet(nonterm, prod):
                self._rawTable[(nonterm, t)].append(prod)
        return Table(self._rawTable)

    def _predictSet(self, nonterm, prod) -> set:
        terminals = set(self._FIRST[prod]) - {self._grammar.getEpsilon()}
        if self._grammar.getEpsilon() in self._FIRST[prod]:
            terminals |= self.FOLLOW[nonterm]
        return terminals
```

Key changes from the original:

- `_rawTable` is `defaultdict(list)`; productions are appended, not added to a set.
- The two methods `_addProductionForEachTerminalInFirst` and `_addProductionForEachFollowIfEpsilonInFirst` are replaced by `_predictSet`, which computes the full lookahead terminal set for a rule as a Python `set` before touching the table. Iterating over a set means each terminal is processed exactly once per rule, eliminating both ε-leaking and FIRST/FOLLOW double-counting.

- [ ] **Step 6: Fix the existing assertion in `build_parsing_table_test.py`**

`getCell` now returns a list, so the set-equality assertions in the existing test must use `set(table.getCell(...))`. Replace the existing test function body:

```python
def test_productions_which_share_both_rule_and_firstSet_terminals_result_in_multiple_cell_entries():
    grammar = createGrammar([
        'S B c',
        'S D B',
        'B a b',
        'B c S',
        'D d',
        'D'
    ])
    firsts = build_first_sets(grammar)
    follows = build_follow_sets(grammar, firsts)
    table = build_parsing_table(firsts, follows, grammar)
    assert set(table.getCell('S', 'a')) == {('B', 'c'), ('D', 'B')}
    assert set(table.getCell('S', 'c')) == {('B', 'c'), ('D', 'B')}
    assert set(table.getCell('S', 'd')) == {('D', 'B')}
    assert set(table.getCell('B', 'a')) == {('a', 'b')}
    assert set(table.getCell('B', 'c')) == {('c', 'S')}
    assert set(table.getCell('D', 'a')) == {()}
    assert set(table.getCell('D', 'c')) == {()}
    assert set(table.getCell('D', 'd')) == {('d',)}
```

- [ ] **Step 7: Run the full unit suite and confirm all tests pass**

```bash
bin/test/units.bash
```

Expected: all tests PASS.

- [ ] **Step 8: Commit**

```bash
git add src/plcc/spec/syntax/validations/ll1/build_parsing_table.py \
        src/plcc/spec/syntax/validations/ll1/build_parsing_table_test.py \
        src/plcc/spec/syntax/validations/ll1/check_ll1_test.py
git commit -m "fix(ll1): use list in parsing table and _predictSet to detect identical predict set conflicts"
```

---

## Task 3: Align `check_parsing_table_for_ll1_test.py` to list semantics

The `Table` in `check_parsing_table_for_ll1_test.py` is constructed directly with hard-coded dicts. These currently use sets (from before the fix). Update them to use lists to match what `TableBuilder` now produces, and add `count` assertions to existing tests so the behaviour is fully documented at the unit level.

**Files:**

- Modify: `src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py`

- [ ] **Step 1: Replace the full test file**

```python
from collections import defaultdict

from .build_parsing_table import Table
from .check_parsing_table_for_ll1 import check_parsing_table_for_ll1


def test_more_than_one_entry_yields_error():
    table = Table({
        ('X', 'a'): ['V', 'E']
    })
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 1
    assert errors[0].cell == ('X', 'a')
    assert errors[0].production == {'V', 'E'}
    assert errors[0].count == 2


def test_no_incorrect_cells_yields_no_errors():
    table = Table({
        ('X', 'a'): ['V'],
        ('A', 'b'): ['d'],
        ('A', 'c'): ['e']
    })
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 0


def test_each_cell_with_duplicate_yields_an_error():
    table = Table({
        ('X', 'a'): ['V', 'E'],
        ('A', 'b'): ['d'],
        ('A', 'c'): ['e', 'E']
    })
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 2
    assert errors[0].cell == ('X', 'a')
    assert errors[0].production == {'V', 'E'}
    assert errors[0].count == 2
    assert errors[1].cell == ('A', 'c')
    assert errors[1].production == {'e', 'E'}
    assert errors[1].count == 2


def test_conflict_reports_count():
    table = Table({
        ('X', 'a'): ['V', 'E']
    })
    errors = check_parsing_table_for_ll1(table)
    assert errors[0].count == 2


def test_identical_productions_in_same_cell_yield_error():
    table = Table({
        ('X', 'a'): ['V', 'V']
    })
    errors = check_parsing_table_for_ll1(table)
    assert len(errors) == 1
    assert errors[0].cell == ('X', 'a')
    assert errors[0].production == {'V'}
    assert errors[0].count == 2
```

Note: the stale `defaultdict` import at the top of the original file is removed (it was never used meaningfully).

- [ ] **Step 2: Run the tests and confirm they all pass**

```bash
bin/test/units.bash src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py -v
```

Expected: all tests PASS.

- [ ] **Step 3: Run the full unit suite**

```bash
bin/test/units.bash
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py
git commit -m "test(ll1): align check_parsing_table_for_ll1_test to list semantics and add count assertions"
```
