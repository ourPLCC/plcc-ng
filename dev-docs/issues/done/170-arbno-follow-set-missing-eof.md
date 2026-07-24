# 170 - LL(1) FOLLOW-set computation drops end-of-input for nullable nonterminals not registered first

**Type:** fix
**Date:** 2026-07-24

## Description

`build_follow_sets.py`'s nullability check only looks at a nonterminal's
*first-registered* production, not all of its alternatives. When a
nonterminal can derive the empty string but its epsilon-producing
alternative isn't the first one added to the grammar, the checker wrongly
concludes the nonterminal is never nullable — which breaks FOLLOW-set
propagation of end-of-input (`$`) through it, and produces a parse table
missing an entry for a legitimately empty derivation at end-of-input.

In practice this reliably bites any `**=` (arbno) rule whose repeated
element itself has a nested epsilon alternative: `_handle_arbno` (in
`spec_json_decoder.py`) always registers the repeated element's non-empty
continuation form before its epsilon form (`Prog# ::= Expr Prog#` added
before `Prog# ::= ε`), so the auto-generated `Prog#` nonterminal always
hits this bug's first-production-only check. There is no spec-authoring
workaround: the offending nonterminal (`Prog#`) is internally generated,
its production order isn't under the spec author's control, and
reordering the *user-written* alternatives (e.g. putting the epsilon
alternative first in the spec) doesn't change it.

Found while implementing issue #166's fix: the left-factored quick
reference grammar drafted for that issue (`<Prog> **= <Expr>`, `<Expr>
::= <NUM:left> <ExprTail:tail>`, `<ExprTail:Add> ::= PLUS <NUM:right>`,
`<ExprTail:End> ::=`) parses `"1 + 2"` correctly but rejects `"1"` alone
with `plcc-parser-table: error: unexpected end of file, no production
for 'ExprTail'`, even though `"1"` should validly exercise the `End`
(epsilon) alternative at end-of-input.

## Steps to Reproduce

1. Using the grammar above (or any `<X> **= <Y>` where `Y` itself has a
   nested epsilon alternative reachable only after consuming at least one
   token), run `echo "1" | plcc-rep --spec=spec.plcc`.
2. Actual: `plcc-parser-table: -:1:1: error: unexpected end of file, no
   production for 'ExprTail'`. Expected: `1` (an `Expr` with no trailing
   `+NUM` is valid — it's exactly what `ExprTail`'s epsilon alternative
   is for).
3. Confirmed via the generated `ll1.json`: `follow_sets` shows
   `"Expr": ["NUM"]` and `"ExprTail": ["NUM"]` — the end-of-input marker
   is missing from both; it should be present in each.
4. Confirmed independently with a minimal non-arbno grammar exercising
   the same code path directly (`Start -> Y Z`, `Z -> A`, `Z -> ε`): the
   FOLLOW-set computation drops end-of-input/`A` from `FOLLOW(Y)` in the
   same way — nothing arbno-specific about the underlying defect; arbno's
   internal desugaring just guarantees the triggering production order
   on every use.

## Notes

Root cause, precisely located: `_allRulesCanDeriveEmpty` in
`src/plcc/spec/syntax/validations/ll1/build_follow_sets.py:81-83`:

```python
def _allRulesCanDeriveEmpty(self, symbol, computing):
    if all(self._canDeriveEmptyString(rule, computing) for rule in self.grammar.getForms(symbol)[0]):
        return True
```

`self.grammar.getForms(symbol)[0]` takes only `symbol`'s first-registered
production (a list of its symbols) and checks whether *all* of them are
nullable. But "can this nonterminal derive empty" is existential over its
*productions* (at least one alternative fully nullable), not just a
universal check within whichever production happens to be first. The fix
is to iterate all productions and return true if any one of them is
fully nullable, e.g.:

```python
def _allRulesCanDeriveEmpty(self, symbol, computing):
    return any(
        all(self._canDeriveEmptyString(s, computing) for s in production)
        for production in self.grammar.getForms(symbol)
    )
```

For `_handle_arbno`'s desugaring of `<nt> **= <rhs>` (`spec_json_decoder.py:41-53`),
the generated continuation nonterminal `nt#` always has its non-empty
form (`nt# ::= rhs nt#`) registered via `grammar.addRule` before its
epsilon form (`nt# ::= ε`), so `getForms("nt#")[0]` is always the
non-empty one — guaranteeing this bug fires for any arbno rule whose
repeated element (`rhs`) is not itself always-nullable. `FOLLOW(nt#)`'s
missing propagation of the start symbol's `$` then cascades into
`FOLLOW` of whatever nonterminal precedes `nt#` in the desugared grammar
(here, `Expr`), and from there into anything that inherits `Expr`'s
FOLLOW set by being the last symbol in one of `Expr`'s own productions
(here, `ExprTail`).

Whoever picks this up should add a unit test at the `build_follow_sets`
level directly (not just an end-to-end `plcc-rep` regression) using the
minimal repro above (`Start -> Y Z`, `Z -> A | ε`, asserting `A` (or the
grammar's EOF marker, whichever the test harness uses as the start
symbol's terminator) ends up in `FOLLOW(Y)`), plus the arbno-specific
end-to-end case from issue #166's grammar once that issue's own fix
lands. Issue #166 worked around this bug by choosing a grammar with no
epsilon alternatives at all, rather than blocking on this fix.
