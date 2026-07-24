# LL(1) FOLLOW-Set Missing EOF Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix `build_follow_sets.py` so a nonterminal's nullability (can-derive-empty-string) is correctly recognized regardless of which of its productions was registered first, so `**=` (arbno) rules whose repeated element has a nested epsilon alternative correctly get end-of-input in their FOLLOW sets.

**Architecture:** Single-file source fix plus its tests, one atomic commit. `_canDeriveEmpty`'s current implementation (`_canDeriveEmptyString`/`_allRulesCanDeriveEmpty`, ~15 lines) recomputes nullability itself, buggily, by only ever looking at `getForms(symbol)[0]`. `build_first_sets.py` already computes nullability correctly for every symbol (as `epsilon ∈ firstSets[symbol]`), and `FollowSetBuilder` already receives `firstSets` in its constructor but never uses it for this. Delete the buggy recomputation; replace `_canDeriveEmpty` with a direct lookup into `firstSets`.

**Tech Stack:** Python 3, pytest. No new dependencies.

## Global Constraints

- Design of record: `dev-docs/specs/2026-07-24-170-arbno-follow-set-missing-eof-design.md`. If anything here seems to contradict it, the spec wins — stop and reconcile before continuing.
- Follow CONTRIBUTING.md's TDD loop: write the failing tests, confirm the failures, write the minimal fix, confirm the passes, then run the full suite before committing.
- `_canDeriveEmptyString` and `_allRulesCanDeriveEmpty` are confirmed unreferenced anywhere outside `build_follow_sets.py` (verified via `grep -rn "_canDeriveEmpty\|_allRulesCanDeriveEmpty\|FollowSetBuilder" src/` during design) — safe to delete entirely, not just patch.
- Docs/e2e regression is explicitly out of scope for this fix — unit-level tests only, per direction during brainstorming.
- Final commit on the branch closes #170 via `bin/issues/close.bash 170`.

---

### Task 1: Fix FOLLOW-set nullability check and add regression tests

**Files:**
- Modify: `src/plcc/spec/syntax/validations/ll1/build_follow_sets.py:68-83` (`_canDeriveEmpty`, `_canDeriveEmptyString`, `_allRulesCanDeriveEmpty`)
- Test: `src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py`

**Interfaces:**
- Consumes: nothing new — `FollowSetBuilder.__init__` already stores `self.firstSets = firsts` (the dict returned by `build_first_sets`, where `epsilon ∈ firstSets[symbol]` iff `symbol` is nullable); `self.grammar.getEpsilon()` is the existing epsilon sentinel object.
- Produces: `_canDeriveEmpty(symbols)` keeps its exact existing signature and its one call site (`_updateWithSingleOccuranceOfNonterminalInProduction`, unchanged) — only its internal correctness changes. `build_follow_sets(grammar, firsts)` (the public module function) and `FollowSetBuilder` itself are otherwise unchanged; nothing downstream needs to know this task happened.

- [ ] **Step 1: Write the three failing tests**

Add to `src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py`, at the end of the file (after `test_left_recursive_nonterminal_inside_nullable_does_not_crash`, before the `setup` helper function):

```python
def test_follow_propagates_eof_through_nullable_registered_second():
    """
    Regression test for issue #170: a nonterminal's nullability must be
    recognized even when its epsilon-producing alternative is registered
    after a non-empty one - the order arbno's internal desugaring always
    uses for its continuation nonterminal. Y needs its own production
    (`Y B`) so the Grammar model classifies it as a nonterminal at all -
    without one, Y auto-classifies as a terminal and never gets a FOLLOW
    entry computed in the first place, which would make this test pass
    for the wrong reason (an empty set is not `{'A', eof}`, but it would
    also not literally raise - always assert against a nonzero-length
    expected set to catch this class of test-authoring mistake).
    """
    grammar, firsts, follows = setup([
        'Start Y Z',
        'Y B',
        'Z A',
        'Z',
    ])
    assert follows['Y'] == {'A', grammar.getEof()}


def test_follow_propagates_eof_regardless_of_alternative_registration_order():
    """
    Same grammar, Z's two alternatives registered in opposite order in
    each of the two separate Grammar instances below. Compare each
    result against its OWN grammar's getEof() (not against each other
    directly) - Grammar.getEof() returns a fresh sentinel object() per
    instance, so follows-sets from two different setup() calls are never
    == to each other even when they're semantically identical.
    """
    g1, _, follows_epsilon_first = setup([
        'Start Y Z',
        'Y B',
        'Z',
        'Z A',
    ])
    g2, _, follows_epsilon_second = setup([
        'Start Y Z',
        'Y B',
        'Z A',
        'Z',
    ])
    assert follows_epsilon_first['Y'] == {'A', g1.getEof()}
    assert follows_epsilon_second['Y'] == {'A', g2.getEof()}


def test_follow_propagates_eof_through_arbno_desugared_continuation():
    """
    Mirrors _handle_arbno's desugaring of `<Prog> **= <Expr>` where Expr
    itself has a nested epsilon alternative (issue #166's original,
    abandoned grammar shape) - the continuation nonterminal (here Prog#)
    is always registered non-empty-form-first.
    """
    grammar, firsts, follows = setup([
        'Prog Expr Prog#',
        'Prog',
        'Prog# Expr Prog#',
        'Prog#',
        'Expr NUM ExprTail',
        'ExprTail PLUS NUM',
        'ExprTail',
    ])
    assert grammar.getEof() in follows['ExprTail']
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `bin/test/units.bash src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py -v`

Expected: the three new tests FAIL —
- `test_follow_propagates_eof_through_nullable_registered_second`: `follows['Y']` is `{'A'}`, missing `grammar.getEof()`.
- `test_follow_propagates_eof_regardless_of_alternative_registration_order`: the first assertion (`follows_epsilon_first['Y'] == {'A', g1.getEof()}`) PASSES — `Z`'s epsilon form is registered first there, and happens to be picked up correctly by the buggy `[0]`-indexed check (iterating an empty production is vacuously "all nullable"). The second assertion (`follows_epsilon_second['Y'] == {'A', g2.getEof()}`) FAILS — epsilon form registered second, missed by the bug, so `follows_epsilon_second['Y']` is just `{'A'}`. Either way the test as a whole fails, on its second assertion.
- `test_follow_propagates_eof_through_arbno_desugared_continuation`: `grammar.getEof() not in follows['ExprTail']`.

All other tests in the file still PASS (in particular, confirm `test_left_recursive_nonterminal_inside_nullable_does_not_crash` still passes at this point — it should, since Step 2 doesn't touch the source yet).

- [ ] **Step 3: Apply the fix**

Current code (`src/plcc/spec/syntax/validations/ll1/build_follow_sets.py:68-83`):

```python
    def _canDeriveEmpty(self, symbols):
        return all(self._canDeriveEmptyString(symbol, set()) for symbol in symbols)

    def _canDeriveEmptyString(self, symbol, computing):
        if symbol in computing:
            return False
        if self.grammar.isNonterminal(symbol):
            computing.add(symbol)
            result = self._allRulesCanDeriveEmpty(symbol, computing)
            computing.discard(symbol)
            return result
        return False

    def _allRulesCanDeriveEmpty(self, symbol, computing):
        if all(self._canDeriveEmptyString(rule, computing) for rule in self.grammar.getForms(symbol)[0]):
            return True
```

Change to:

```python
    def _canDeriveEmpty(self, symbols):
        return all(self.grammar.getEpsilon() in self.firstSets[symbol] for symbol in symbols)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `bin/test/units.bash src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py -v`

Expected: all tests in the file PASS, including the three new ones and the pre-existing `test_left_recursive_nonterminal_inside_nullable_does_not_crash` (still passes — trivially now, since the new `_canDeriveEmpty` does no recursion at all, so there's nothing left to guard against).

- [ ] **Step 5: Run the full unit suite as a final check**

Run: `bin/test/units.bash`

Expected: all tests PASS, 0 failures, count at or above the pre-work baseline (1203 passed, 3 skipped, per the last full run on this branch).

- [ ] **Step 6: Commit**

```bash
git add src/plcc/spec/syntax/validations/ll1/build_follow_sets.py \
        src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py
git commit -m "$(cat <<'EOF'
fix(ll1): recognize nullability regardless of production registration order

_allRulesCanDeriveEmpty only checked a nonterminal's first-registered
production (getForms(symbol)[0]) instead of all of them, so a
nonterminal whose epsilon alternative wasn't registered first was
wrongly treated as non-nullable - breaking FOLLOW-set propagation of
end-of-input through it. This reliably broke any `**=` (arbno) rule
whose repeated element has a nested epsilon alternative, since
_handle_arbno always registers its internal continuation nonterminal's
non-empty form before its epsilon form.

build_first_sets.py already computes nullability correctly and
independently for every symbol (epsilon in firstSets[symbol] iff
nullable), and FollowSetBuilder already receives firstSets but never
reused it for this check. Delete the buggy duplicate computation
(_canDeriveEmptyString, _allRulesCanDeriveEmpty - confirmed unreferenced
elsewhere) and reuse firstSets directly instead. As a side effect, this
also makes the RecursionError-on-left-recursion guard from 5cc5a05a
unnecessary (no recursion left in this path at all) - left in place
since it's harmless and the test that exercises it still passes.

Design: dev-docs/specs/2026-07-24-170-arbno-follow-set-missing-eof-design.md
EOF
)"
```

---

## After this plan

Issue 170 closes as the final commit of this branch, per CLAUDE.md's issue-closing convention:

```bash
bin/issues/close.bash 170
```

This moves `dev-docs/issues/170-arbno-follow-set-missing-eof.md` to
`dev-docs/issues/done/` and updates `dev-docs/roadmap.md`. Verify with
`bin/issues/check.bash` afterward.
