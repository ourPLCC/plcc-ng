# FOLLOW set nullable-tail fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `FollowSetBuilder` so FOLLOW-set computation walks forward through every nullable symbol after a nonterminal occurrence, instead of stopping after the immediate next symbol — closing the gap that silently drops parse-table entries for empty alternatives (issue #188).

**Architecture:** Single-method control-flow fix in `src/plcc/spec/syntax/validations/ll1/build_follow_sets.py`. No new files, no changes to `build_first_sets.py` or `Grammar.py` — nullability data is already correct there.

**Tech Stack:** Python, pytest (`bin/test/units.bash`).

## Global Constraints

- Follow the TDD inner loop from CONTRIBUTING.md: write the failing test first, confirm it fails, write minimal code to pass, confirm it passes, then commit.
- Test tier: unit only (`src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py`), per the approved design — no bats/e2e test is added for this issue.
- Commit message for the code fix: `fix(ll1): walk forward through nullable symbols when computing FOLLOW sets` (see design doc, `dev-docs/specs/2026-08-12-follow-set-nullable-tail-design.md`, for the full body).
- Close issue #188 with `bin/issues/close.bash 188` as the final commit of this branch, per `dev-docs/issue-conventions.md`.

---

### Task 1: Fix the FOLLOW-set nullable-tail walk

**Files:**
- Modify: `src/plcc/spec/syntax/validations/ll1/build_follow_sets.py:44-50`
- Test: `src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py`

**Interfaces:**
- Consumes: `FollowSetBuilder._addFirstOfNextSymbol(nextSymbol, nonterminal)` (existing, unchanged) and `FollowSetBuilder._canDeriveEmpty(symbols)` (existing, unchanged, takes a list of symbols and returns `bool`) and `FollowSetBuilder._addFollowOfLHS(lhs, nonterminal)` (existing, unchanged).
- Produces: no new public interface. `build_follow_sets(grammar, firsts)` (module-level function, already defined at the top of the file) keeps its existing signature and return type (`dict[str, set]`) — this task only changes the *values* it computes for FOLLOW sets that involve a nullable non-final symbol.

There is currently one test file for this module,
`src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py`, which
already defines a `setup(lines)` helper:

```python
def setup(lines):
    g = Grammar()
    for line in [line.split() for line in lines]:
        g.addRule(line[0], line[1:])
    firsts = build_first_sets(g)
    follows = build_follow_sets(g, firsts)
    return g, firsts, follows
```

Each `lines` entry is `"<lhs> <rhs-symbol-1> <rhs-symbol-2> ..."` (space-separated; an entry with no symbols after the lhs, e.g. `"A"`, is an epsilon/empty production for `A`). Reuse this helper — do not write a new one.

- [ ] **Step 1: Write the failing test**

Open `src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py`. Add the following test function anywhere above the `setup(lines)` definition at the bottom of the file (e.g. directly above `def setup(lines):`):

```python
def test_follow_set_walks_past_nullable_symbol_to_next_non_nullable():
    """
    Regression test for issue #188: the forward walk from a nonterminal's
    occurrence must continue past a nullable next symbol and add FIRST of
    each subsequent symbol until it hits one that cannot derive empty,
    rather than stopping after the single next symbol.

    S -> A B C, A -> a | epsilon, B -> b | epsilon, C -> c.
    B is nullable, so FOLLOW(A) must include FIRST(B) - {epsilon} = {b}
    AND FIRST(C) = {c}, not just {b}.
    """
    grammar, firsts, follows = setup([
        'S A B C',
        'A a',
        'A',
        'B b',
        'B',
        'C c',
    ])
    assert follows['A'] == {'b', 'c'}
```

If a test with the same name and a different grammar already exists in the file from earlier exploratory work, replace it with the exact version above rather than keeping both — they exercise the same grammar shape and assertion.

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/test/units.bash src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py -k test_follow_set_walks_past_nullable_symbol_to_next_non_nullable -v`

Expected: FAIL. The assertion `follows['A'] == {'b', 'c'}` fails because the current buggy code only produces `{'b'}` for `follows['A']` (it stops after adding FIRST of the immediate next symbol `B` and never reaches `C`'s FIRST set).

- [ ] **Step 3: Write minimal implementation**

Open `src/plcc/spec/syntax/validations/ll1/build_follow_sets.py`. Find `_updateWithSingleOccuranceOfNonterminalInProduction` (currently lines 44-50):

```python
    def _updateWithSingleOccuranceOfNonterminalInProduction(self, lhs, rules, index, nonterminal):
        if self._isLastOccuranceInRule(rules, index):
            self._addFollowOfLHS(lhs, nonterminal)
        else:
            self._addFirstOfNextSymbol(rules[index + 1], nonterminal)
            if self._canDeriveEmpty(rules[index + 1:]):
                self._addFollowOfLHS(lhs, nonterminal)
```

Replace the `else` branch so it reads:

```python
    def _updateWithSingleOccuranceOfNonterminalInProduction(self, lhs, rules, index, nonterminal):
        if self._isLastOccuranceInRule(rules, index):
            self._addFollowOfLHS(lhs, nonterminal)
        else:
            for j in range(index + 1, len(rules)):
                self._addFirstOfNextSymbol(rules[j], nonterminal)
                if not self._canDeriveEmpty([rules[j]]):
                    break
            else:
                self._addFollowOfLHS(lhs, nonterminal)
```

Do not change any other method in the file. `_addFirstOfNextSymbol` and `_canDeriveEmpty` are called exactly as before, just from inside the loop instead of once.

- [ ] **Step 4: Run test to verify it passes**

Run: `bin/test/units.bash src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py -v`

Expected: PASS — all tests in the file pass, including the new one and the 13 pre-existing tests (`test_example`, `test_test_yourself_3`, `test_derives_epsilon`, `test_follow_set_one_rule`, `test_follow_set_captured_nonterminal`, `test_follow_set_one_nonterminal`, `test_derive_empty`, `test_follow_set_empty_rule`, `test__follow_set_with_terminal_after_captured_rule`, `test_left_recursive_nonterminal_inside_nullable_does_not_crash`, `test_follow_propagates_eof_through_nullable_registered_second`, `test_follow_propagates_eof_regardless_of_alternative_registration_order`, `test_follow_propagates_eof_through_arbno_desugared_continuation`).

- [ ] **Step 5: Run the full unit tier for a broader regression check**

Run: `bin/test/units.bash`

Expected: all tests pass, no failures introduced elsewhere (other modules — e.g. `build_parsing_table.py`, `check_ll1.py` — consume `build_follow_sets`'s output, so this confirms nothing downstream broke).

- [ ] **Step 6: Commit**

```bash
git add src/plcc/spec/syntax/validations/ll1/build_follow_sets.py src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py
git commit -m "$(cat <<'EOF'
fix(ll1): walk forward through nullable symbols when computing FOLLOW sets

FOLLOW-set computation added FIRST of only the immediate next symbol
after a nonterminal occurrence, then jumped straight to checking
whether the entire remainder was nullable - skipping every symbol in
between. A nonterminal followed by one nullable symbol and then a
non-nullable one lost the non-nullable symbol's FIRST set entirely,
silently truncating FOLLOW and dropping parse-table entries for empty
alternatives.

Fixes #188
EOF
)"
```

---

### Task 2: Close issue #188

**Files:**
- Modify (via script, not by hand): `dev-docs/issues/done/188-follow-set-omits-nullable-tail.md` → moved to `dev-docs/issues/done/`
- Modify (via script, not by hand): `dev-docs/roadmap.md`

**Interfaces:**
- Consumes: `bin/issues/close.bash <id>` (existing script, takes the numeric issue ID as its one argument).
- Produces: nothing consumed by later tasks — this is the final task in the plan.

- [ ] **Step 1: Run the close script**

Run: `bin/issues/close.bash 188`

This moves `dev-docs/issues/done/188-follow-set-omits-nullable-tail.md` to `dev-docs/issues/done/`, removes its entry from the Open Issues section of `dev-docs/roadmap.md` (and the `### Fix` heading too, only if #188 was the last entry under it — check `dev-docs/roadmap.md` after running; `#160` and `#186` are also filed under `### Fix` as of this writing, so the heading should remain), rewrites cross-links to the issue's new path, and stages the changes.

- [ ] **Step 2: Verify issue-tracker consistency**

Run: `bin/issues/check.bash`

Expected: exits 0, no drift reported.

- [ ] **Step 3: Review staged changes**

Run: `git status` and `git diff --staged`

Confirm: `dev-docs/issues/done/188-follow-set-omits-nullable-tail.md` shows as renamed/moved into `dev-docs/issues/done/`, and `dev-docs/roadmap.md` no longer lists `#188` under Open Issues.

- [ ] **Step 4: Commit**

```bash
git commit -m "docs(issues): close issue 188 (FOLLOW set omits nullable tail), update roadmap"
```
