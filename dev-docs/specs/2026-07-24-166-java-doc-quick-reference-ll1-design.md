# Java doc's "Quick reference example" grammar is not LL(1) — design

**Issue:** [166](../issues/166-java-doc-quick-reference-not-ll1.md)
**Date:** 2026-07-24

## Problem

`docs/language-guide/languages/java.md`'s "Quick reference example" uses:

```
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
```

`<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>` makes `Exp` left-recursive.
PLCC-ng's LL(1) parser rejects this outright (`LL(1) conflict: <Exp> on
lookahead NUM`), so the doc's claim that `echo "1 + 2" | plcc-rep` prints
`3` is false — the grammar never emits, let alone runs.

A rewrite fixing this was drafted while working on issues #162/#165, then
reverted (`426c0075`) as out of scope for that task — the revert commit's
message notes it renamed `Exp`/`AddExp`/`NumExp` and broke the "BNF to
Java constructs" table's references to the old names. This issue is
where that rewrite belongs, done properly: example and table updated
together, verified end-to-end.

## Scope

`docs/language-guide/languages/java.md` only. `javascript.md`, `python.md`,
and `haskell.md` have byte-for-byte the same `<Exp:AddExp> ::= <Exp:left>
PLUS <Exp:right>` left-recursion in their own quick reference examples and
tables, confirmed by grep. Each gets its own sibling issue (filed via
`bin/issues/new.bash`) rather than being folded into this one, per this
repo's convention of narrow, single-concern issues.

## Decision

Reuse the previously-drafted, previously-verified rewrite (`echo "1 + 2" |
plcc-rep` → `3`, confirmed while it existed pre-revert) rather than
designing a new grammar from scratch:

```
<Prog>         **= <Expr>
<Expr>         ::= <NUM:left> <ExprTail:tail>
<ExprTail:Add> ::= PLUS <NUM:right>
<ExprTail:End> ::=
```

Left-factoring moves the choice point off `Exp` itself: `Expr` is now a
single concrete rule (`NUM` followed by an optional tail), and the
alternation (`Add` vs. `End`) lives on `ExprTail`, which starts with
either `PLUS` or nothing — no FIRST/FIRST conflict.

This only parses a single optional addition (`1` or `1 + 2`, not
`1 + 2 + 3`) — accepted as sufficient, since the example's job is to
exercise each grammar construct once, not to demonstrate operator
chaining. All six construct categories the doc's table documents are
still present: concrete rule (`Expr`, `Prog`), alternative rule
(`ExprTail:Add`/`ExprTail:End`), named-nonterminal RHS (`ExprTail:tail`),
captured terminal RHS (`NUM:left`, `NUM:right`), uncaptured terminal RHS
(`PLUS`), and arbno (`Prog **= Expr`).

Renames from the current (broken) grammar: `Exp`→`Expr`, `AddExp`→`Add`,
`NumExp`→`End`, field `expList`→`exprList`.

## Changes

### 1. Quick reference example (grammar + Java fragments)

Replace the grammar block and all five semantic-section fragments:

```
Expr
%%%
public int eval() {
    return tail.eval(Integer.parseInt(left.lexeme));
}
%%%

ExprTail
%%%
public abstract int eval(int left);
%%%

Prog
%%%
public String _run() {
    java.util.List<String> lines = new java.util.ArrayList<>();
    for (Expr expr : exprList) {
        lines.add(String.valueOf(expr.eval()));
    }
    return String.join("\n", lines);
}
%%%

Add
%%%
public int eval(int left) {
    return left + Integer.parseInt(right.lexeme);
}
%%%

End
%%%
public int eval(int left) {
    return left;
}
%%%
```

`Expr.eval()` parses the leading number and hands it to `tail.eval(...)`
as an accumulator; `Add.eval(left)` folds in the captured `right` token;
`End.eval(left)` is the base case (no trailing `+`, return the
accumulator unchanged).

### 2. "BNF to Java constructs" table

Re-ground every row's "Example from spec" / "Example based on spec"
columns in the new grammar:

| Grammar Construct | Example from spec | Java Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one class | `<Prog>` in `<Prog> **= <Expr>` | Java class with public fields and constructor | `class Prog extends _Start { public ArrayList<Expr> exprList; ... }` |
| Alternative rule (LHS, with alt name) — base nonterminal becomes abstract | `<ExprTail:Add>` in `<ExprTail:Add> ::= PLUS <NUM:right>` | Java class extending the base nonterminal | `class Add extends ExprTail { public Token right; ... }` |
| Named non-terminal (RHS) | `<ExprTail:tail>` | `tail` — an `ExprTail` instance | `tail.eval(left)` |
| Captured terminal (RHS) | `<NUM:left>` | `left` — a `Token`; `.lexeme` for the string value | `Integer.parseInt(left.lexeme)` |
| Uncaptured terminal (RHS) | `PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Expr>` | `exprList` — `ArrayList<Expr>` | `for (Expr expr : exprList)` |

And the paragraph immediately below the table: `<Exp>` → `<Expr>` in its
illustrative default-naming example (`<NUM>` → `num` is unaffected).

### 3. Two stale references outside the table

Found by grepping the file for `Exp` after drafting the above — neither
is inside the quick reference example or its table, so easy to miss:

- Line ~136 ("`_run` entry point" section, abstract-class note):
  `` (see `Exp` in the quick reference example) `` → `` `ExprTail` `` —
  it's the abstract one in the new grammar; `Expr` itself is concrete.
- Lines ~179–180 ("Generated output" file tree): `AddExp.java` /
  `NumExp.java` → add `Expr.java` alongside the existing `Prog.java`,
  and change the two alternative-class entries to `Add.java` / `End.java`.

## Testing

Docs-only change; no automated test suite covers doc prose. Verification
is manual, matching the process that surfaced this bug in the first place
(task 5 of #162/#165: actually run the example end-to-end):

1. Copy the updated grammar + fragments verbatim into a scratch
   `spec.plcc`.
2. `echo "1 + 2" | plcc-rep --spec=spec.plcc` → expect `3`.
3. `echo "1" | plcc-rep --spec=spec.plcc` → expect `1` (exercises the
   `End` alternative, not just `Add`).

## Commit shape

Docs-only, no breaking change. Single commit (or a small stack) touching
only `docs/language-guide/languages/java.md`. Final commit on the branch
closes #166 via `bin/issues/close.bash 166`.

Follow-up, same branch or a later one: `bin/issues/new.bash` for the
`javascript.md`, `python.md`, and `haskell.md` equivalents of this bug,
plus a roadmap entry in the same commit per `dev-docs/issue-conventions.md`.

## Files changed

| File | Change |
| --- | --- |
| `docs/language-guide/languages/java.md` | Quick reference grammar + Java fragments rewritten (left-factored, renamed); "BNF to Java constructs" table re-grounded in new names; two stale `Exp`-family references outside the table corrected |
