# 166 - Java language guide's "Quick reference example" grammar is not LL(1)

**Type:** docs
**Date:** 2026-07-23

## Description

`docs/language-guide/languages/java.md`'s "Quick reference example" — the
grammar used throughout the rest of that page, including the "BNF to Java
constructs" table below it — does not actually parse. `<Exp:AddExp> ::=
<Exp:left> PLUS <Exp:right>` makes `Exp` left-recursive, which PLCC-ng's
LL(1) parser cannot handle. The doc's own claim ("Running this with `echo
"1 + 2" | plcc-rep` prints `3`.") is false as written.

Found while implementing the `_run()` contract fix (issues #162/#165):
task 5 of that work added a step to actually run every doc example
end-to-end before/after changing `_run()`'s signature, and this is the
first time anyone appears to have done that for this specific example.

## Steps to Reproduce

1. Copy the "Quick reference example" grammar from
   `docs/language-guide/languages/java.md` verbatim into a `spec.plcc`.
2. `echo "1 + 2" | plcc-rep --spec=spec.plcc`
3. Actual: `plcc-make: error: grammar is not LL(1)` — `LL(1) conflict:
   <Exp> on lookahead NUM` (a FIRST/FIRST conflict, since both
   `<Exp> ::= <Exp>left PLUS <Exp>right` and `<Exp> ::= <NUM>` start with
   `NUM` once `Exp`'s left-recursion is expanded). Expected per the doc:
   prints `3`.

## Notes

This needs left-factoring the grammar into a non-left-recursive shape
(e.g. `<Expr> ::= <NUM:left> <ExprTail:tail>` with `<ExprTail:Add> ::=
PLUS <NUM:right>` / `<ExprTail:End> ::=`, restructuring `eval()` to an
accumulator-style pass), which changes the rule names the "BNF to Java
constructs" table right below the example refers to (`Exp`, `AddExp`,
`NumExp`, `expList`). Both the example and that table need to change
together, correctly, as one reviewed piece of work — not bundled into an
unrelated task.

A rewrite along these lines was drafted (and verified to actually run:
`echo "1 + 2" | plcc-rep` → `3`) while working on #162/#165, then reverted
out of that work as out of scope. It renamed `Exp`→`Expr`,
`AddExp`→`Add`, `NumExp`→`End`, and changed the field/list name to
`exprList`. Whoever picks this up should start there rather than from
scratch, but must also update the "BNF to Java constructs" table's
references to the old names, which the draft did not do.
