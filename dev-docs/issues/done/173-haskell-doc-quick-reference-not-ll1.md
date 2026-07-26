# 173 - Haskell language guide's "Quick reference example" grammar is not LL(1)

**Type:** docs
**Date:** 2026-07-24

## Description

`docs/language-guide/languages/haskell.md`'s "Quick reference example" has
the same left-recursive grammar as issue #166's Java version:
`<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>` makes `Exp` left-recursive,
which PLCC-ng's LL(1) parser rejects outright. The doc's claimed output for
`echo "1 + 2" | plcc-rep` is false as written, same as #166.

## Steps to Reproduce

1. Copy the "Quick reference example" grammar from
   `docs/language-guide/languages/haskell.md` verbatim into a `spec.plcc`.
2. `echo "1 + 2" | plcc-rep --spec=spec.plcc`
3. Actual: `plcc-make: error: grammar is not LL(1)` (same FIRST/FIRST
   conflict as #166). Expected per the doc: prints `3`.

## Notes

Same root cause as #166 — see
`dev-docs/specs/2026-07-24-166-java-doc-quick-reference-ll1-design.md` for
the grammar shape to reuse: `<Prog> **= <Expr>`, `<Expr> ::= <NUM:left>
<Op:op> <NUM:right>`, `<Op:AddOp> ::= PLUS`, `<Op:SubOp> ::= MINUS`
(requires a new `MINUS` token). This left-factors by moving the
alternation onto the operator rather than making the second operand
optional — deliberately avoid an optional/epsilon-tail shape (e.g.
`<ExprTail:Add> ::= PLUS <NUM:right>` / `<ExprTail:End> ::=` under
`Prog`'s arbno): that shape was tried first for #166 and hit a real,
separately-filed PLCC-ng parser bug (#170 — LL(1) FOLLOW-set computation
drops end-of-input for a nullable nonterminal not registered first,
which every `**=` rule whose repeated element has a nested epsilon
alternative triggers). The operator-alternation grammar's repeated
element (`Expr`) has no nested epsilon alternative of its own, so #170's
defect (which is still technically present, as it is in any `**=`
rule's internal desugaring) has nothing to corrupt and produces no
observable parsing failure.

This page's own "Fragment kinds" section documents that Haskell fragment
class names must be module names — the abstract rule name (`Exp`) or a
lone concrete name (`Prog`), never a concrete alternative name (`AddExp`,
`NumExp`). That means Haskell's `apply` implementations for
`AddOp`/`SubOp` live as pattern-matched clauses inside a single `Op`
fragment (`apply (AddOp) l r = ...` / `apply (SubOp) l r = ...`, exact
pattern syntax per however this page's existing `Exp`/`AddExp`/`NumExp`
fragment already does it), not as separate per-class fragments the way
Java/JS/Python do it. Whoever picks this up should design the
left-factored grammar's Haskell fragment(s) around that constraint from
the start, rather than porting #166's per-class fragment structure and
hitting a "fragment tagged 'AddOp': AddOp is a concrete alternative of
Op" error.

Also update this page's own "BNF to Haskell constructs" table, its
"Generated output" file list (`AddExp.hs`/`NumExp.hs` → new names), and
any other stale `Exp`/`AddExp`/`NumExp`/`expList` references — grep the
whole file first, the way #166's design doc did, since #166 found two
such references that lived outside the example and its table and would
have been missed by a narrower fix.
