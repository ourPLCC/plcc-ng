# LL(1) FOLLOW-set computation drops end-of-input for late-registered nullable productions — design

**Issue:** [170](../issues/done/170-arbno-follow-set-missing-eof.md)

## Problem

`build_follow_sets.py`'s nullability check, `_allRulesCanDeriveEmpty`, only
examines a nonterminal's *first-registered* production:

```python
def _allRulesCanDeriveEmpty(self, symbol, computing):
    if all(self._canDeriveEmptyString(rule, computing) for rule in self.grammar.getForms(symbol)[0]):
        return True
```

`self.grammar.getForms(symbol)[0]` is a single production (a list of its
symbols); the check should be existential over *all* of a nonterminal's
productions (at least one alternative fully nullable), not a check
confined to whichever one happens to be registered first. When a
nonterminal's epsilon-producing alternative isn't first, the checker
wrongly concludes the nonterminal can never derive empty — which breaks
FOLLOW-set propagation of end-of-input (`$`) through it wherever that
nonterminal appears followed by more symbols in some other production.

This reliably bites any `**=` (arbno) rule whose repeated element itself
has a nested epsilon alternative: `_handle_arbno` (`spec_json_decoder.py`)
always registers its internal continuation nonterminal's non-empty form
before its epsilon form, so the auto-generated continuation nonterminal
always trips this check. Confirmed in issue #166's original (later
abandoned) grammar: `echo "1" | plcc-rep` failed with `no production for
'ExprTail'` because `FOLLOW(ExprTail)` was missing end-of-input.

## Decision

`build_first_sets.py` already computes nullability correctly and
independently: for every symbol (terminal or nonterminal), `epsilon ∈
firstSets[symbol]` iff that symbol can derive the empty string — computed
by iterating *all* of a nonterminal's productions (`build_first_sets.py`'s
`_update`, called with the symbol's full `getForms(symbol)`, not a single
indexed production). `FollowSetBuilder` already receives `firstSets` as a
constructor argument (`self.firstSets = firsts`) but never reuses it for
this check — it recomputes nullability itself, incorrectly.

Delete the duplicate, buggy computation and reuse the already-correct
data instead of re-deriving it:

```python
def _canDeriveEmpty(self, symbols):
    return all(self.grammar.getEpsilon() in self.firstSets[symbol] for symbol in symbols)
```

This replaces `_canDeriveEmpty`'s current body and lets `_canDeriveEmptyString`
and `_allRulesCanDeriveEmpty` be deleted entirely (confirmed via
`grep -rn "_canDeriveEmpty\|_allRulesCanDeriveEmpty\|FollowSetBuilder" src/`
that neither is referenced anywhere outside `build_follow_sets.py`).

This is the more thorough fix over the issue's own minimally-suggested
patch (making `_allRulesCanDeriveEmpty` existential over `getForms(symbol)`
instead of `getForms(symbol)[0]`) — chosen because it removes the
duplicate nullability logic altogether rather than leaving a
parallel-but-hopefully-now-correct implementation next to the one that's
already known correct. It also has a side benefit: `_canDeriveEmptyString`'s
`computing` set exists purely to guard against infinite recursion on
left-recursive grammars (see `test_left_recursive_nonterminal_inside_nullable_does_not_crash`).
Since the new `_canDeriveEmpty` does no recursion at all — it's a direct
lookup into an already-fully-computed table — that failure mode is
structurally impossible now, not just guarded against.

## Changes

### `src/plcc/spec/syntax/validations/ll1/build_follow_sets.py`

Replace:

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

with:

```python
    def _canDeriveEmpty(self, symbols):
        return all(self.grammar.getEpsilon() in self.firstSets[symbol] for symbol in symbols)
```

No other method in the file changes; `_canDeriveEmpty`'s call site
(`_updateWithSingleOccuranceOfNonterminalInProduction`) and signature are
unchanged.

### `src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py`

Three new tests, using the file's existing `setup()` helper
(space-separated grammar lines; first token is the LHS, remaining tokens
the RHS, no RHS tokens meaning an epsilon production):

1. **The issue's own minimal repro**, epsilon alternative registered
   *second* (the order that currently breaks). `Y` needs its own
   production (`Y B`) so the `Grammar` model classifies it as a
   nonterminal at all — without one it auto-classifies as a terminal and
   never gets a FOLLOW entry computed in the first place:
   ```python
   def test_follow_propagates_eof_through_nullable_registered_second():
       grammar, firsts, follows = setup([
           'Start Y Z',
           'Y B',
           'Z A',
           'Z',
       ])
       assert follows['Y'] == {'A', grammar.getEof()}
   ```

2. **Order-independence proof** — same grammar, epsilon alternative
   registered *first* in one `Grammar` instance and *second* in another,
   asserting each matches its own expectation. Compared against each
   instance's own `getEof()` separately, not against each other —
   `Grammar.getEof()` returns a fresh sentinel `object()` per instance,
   so two different `setup()` calls' FOLLOW sets are never `==` to each
   other even when semantically identical:
   ```python
   def test_follow_propagates_eof_regardless_of_alternative_registration_order():
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
   ```

3. **Arbno's real internal desugared shape**, mirroring `_handle_arbno`'s
   actual output for `<Prog> **= <Expr>` where `Expr` has a nested
   epsilon alternative (issue #166's original, abandoned grammar):
   ```python
   def test_follow_propagates_eof_through_arbno_desugared_continuation():
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

## Testing

Docs/e2e regression explicitly out of scope (per direction) — this is an
internal algorithm bug with no spec-syntax surface, so a unit test is the
right level. Follow CONTRIBUTING.md's TDD loop:

1. Add the three tests above; run `bin/test/units.bash
   src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py -v` and
   confirm all three fail against the current (buggy) code.
2. Apply the fix; re-run and confirm all three pass, and that the file's
   existing tests (`test_left_recursive_nonterminal_inside_nullable_does_not_crash`
   in particular) still pass.
3. Run the full `bin/test/units.bash` to confirm no regressions elsewhere.

## Commit shape

Single `fix(ll1)` commit (source + tests together, per this repo's usual
pattern for small, atomic bug fixes — see e.g. `5cc5a05a`, the prior fix
to this same file). Not a breaking change: this only makes previously
under-computed FOLLOW sets more complete/correct; nothing that currently
compiles LL(1)-successfully can start failing because of it (a superset
of previously-empty parse-table entries can only make previously-rejected
grammars newly-accepted, never the reverse — the fix strictly adds
missing follow-set members, never removes wrongly-present ones). Final
commit on the branch closes #170 via `bin/issues/close.bash 170`.

## Files changed

| File | Change |
| --- | --- |
| `src/plcc/spec/syntax/validations/ll1/build_follow_sets.py` | `_canDeriveEmpty` reimplemented to reuse `firstSets`; `_canDeriveEmptyString` and `_allRulesCanDeriveEmpty` deleted |
| `src/plcc/spec/syntax/validations/ll1/build_follow_sets_test.py` | Three new regression tests for issue #170 |
