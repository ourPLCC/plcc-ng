# Java doc's "Quick reference example" grammar is not LL(1) — design

**Issue:** [166](../issues/166-java-doc-quick-reference-not-ll1.md)
**Date:** 2026-07-24 (revised same day — see "Revision" below)

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

## Revision: the first rewrite attempt uncovered a real parser bug

The original version of this design (below, in spirit) reused the
`426c0075`-reverted draft's left-factored grammar verbatim:

```
<Prog>         **= <Expr>
<Expr>         ::= <NUM:left> <ExprTail:tail>
<ExprTail:Add> ::= PLUS <NUM:right>
<ExprTail:End> ::=
```

Implementing it and actually running both cases the plan required
(`"1 + 2"` and bare `"1"`) showed `"1 + 2"` → `3` (correct) but bare
`"1"` → `plcc-parser-table: error: unexpected end of file, no
production for 'ExprTail'` (should be `1`). Root cause, confirmed twice
independently (once by re-deriving it directly, once by a separate
research pass, both landing on the same file and line): `_allRulesCanDeriveEmpty`
in `src/plcc/spec/syntax/validations/ll1/build_follow_sets.py:81-83`
only checks a nonterminal's *first-registered* production for
nullability, not all of its alternatives. Arbno's internal desugaring
(`_handle_arbno` in `spec_json_decoder.py`) always registers its
continuation nonterminal's non-empty form before its epsilon form, so
every `**=` rule whose repeated element has a nested epsilon alternative
hits this — the end-of-input marker never propagates into that
alternative's FOLLOW set, so the parse table has no entry for "stop
here, input's done." Filed as its own bug: **[#170](../issues/170-arbno-follow-set-missing-eof.md)**.

There is no way to keep the original left-factored grammar (`ExprTail`
with an epsilon `End` alternative, under `Prog`'s arbno) and avoid this
bug — the blocking nonterminal is internally generated, not under the
spec author's control. Per direction, this issue does not block on
#170 landing; instead, the grammar below was redesigned so that its
**repeated element (`Expr`) has no nested epsilon alternative of its
own**. Precisely: every `**=` rule's internal desugaring contains an
epsilon production (`Prog ::= ε`), including this one, and #170's buggy
nullability check still misflags it — but that corruption is inert here,
because nothing inside `Expr` ever needs `FOLLOW(Expr)` to contain `$`
for correctness (there's no epsilon *choice point* nested inside `Expr`
the way `ExprTail:End` was). So the bug is still technically hit, just
never observable. Verified empirically: the redesigned grammar parses `"1 + 2"`
→ `3`, `"5 - 3"` → `2`, and even a two-expression single input
(`"1 + 2 5 - 3"` → `3` then `2`, exercising the arbno list with more
than one element) — all before writing a single line of the doc itself.

The rest of this document describes the redesigned (working) grammar.

## Scope

`docs/language-guide/languages/java.md` only. `javascript.md`, `python.md`,
and `haskell.md` have byte-for-byte the same `<Exp:AddExp> ::= <Exp:left>
PLUS <Exp:right>` left-recursion in their own quick reference examples and
tables, confirmed by grep. Each gets its own sibling issue (filed via
`bin/issues/new.bash`) rather than being folded into this one, per this
repo's convention of narrow, single-concern issues.

## Decision

Left-factor by moving the alternation to the *operator*, not to an
optional trailing tail. `Expr` always requires exactly `NUM op NUM` — no
epsilon alternative nested inside `Expr` itself:

```
<Prog>     **= <Expr>
<Expr>     ::= <NUM:left> <Op:op> <NUM:right>
<Op:AddOp> ::= PLUS
<Op:SubOp> ::= MINUS
```

`Op:AddOp` and `Op:SubOp` are distinguished by their first (and only)
token — `PLUS` vs. a new `MINUS` token — so there's no FIRST/FIRST
conflict, and (unlike the reverted draft) neither `Expr` nor `Op` ever
needs to derive the empty string, so issue #170's bug — though still
technically present in the arbno's own internal desugaring, as it is for
any `**=` rule — has nothing to corrupt here and produces no observable
parsing failure. This is a small, deliberate scope addition beyond "just
remove the optionality" (it also adds subtraction) because it was the
simplest way to keep an `Alternative rule` demonstration in the example
without a nested epsilon alternative: an alternation needs at least two
productions distinguished by lookahead, and `Op`'s two one-token
productions are the minimal way to get that without optionality.

This drops support for a bare `"1"` (no operator) as valid input — that
was never something the doc claimed in the first place; it was only
introduced as this issue's own stricter verification step (added
because the original bug was caught by nobody testing the doc's example
end-to-end). All six construct categories the doc's table documents are
still present: concrete rule (`Expr`, `Prog`), alternative rule
(`Op:AddOp`/`Op:SubOp`), named-nonterminal RHS (`Op:op`), captured
terminal RHS (`NUM:left`, `NUM:right`), uncaptured terminal RHS (`PLUS`),
and arbno (`Prog **= Expr`).

Renames from the current (broken) grammar: `Exp`→`Expr`, `AddExp`→`AddOp`
(now a class over the *operator*, not the whole expression), `NumExp`→
removed (no longer needed — `Expr` itself is now the only concrete
"expression" shape), field `expList`→`exprList`. `Op`/`AddOp`/`SubOp` and
the `MINUS` token are new; `NumExp`'s role (a bare-number expression) no
longer exists.

## Changes

### 1. Quick reference example (grammar + Java fragments)

Replace the grammar block and add a `MINUS` token; replace all five
semantic-section fragments:

```
token NUM   '\d+'
token PLUS  '\+'
token MINUS '-'
skip  SPACE '\s+'
%
<Prog>     **= <Expr>
<Expr>     ::= <NUM:left> <Op:op> <NUM:right>
<Op:AddOp> ::= PLUS
<Op:SubOp> ::= MINUS
%
Java

Op
%%%
public abstract int apply(int left, int right);
%%%

Expr
%%%
public int eval() {
    return op.apply(Integer.parseInt(left.lexeme), Integer.parseInt(right.lexeme));
}
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

AddOp
%%%
public int apply(int left, int right) {
    return left + right;
}
%%%

SubOp
%%%
public int apply(int left, int right) {
    return left - right;
}
%%%
```

`Expr.eval()` parses both captured numbers and delegates the arithmetic
to `op.apply(...)`; `AddOp`/`SubOp` each implement `apply` for their one
operator. `Prog._run()` is structurally unchanged from the current doc
(same iterate-and-join pattern) except for the `Expr`/`exprList` rename.

The doc's existing claim two lines below the block — "Running this with
`echo "1 + 2" | plcc-rep` prints `3`." — needs no wording change; it's
simply now true.

### 2. "BNF to Java constructs" table

Re-ground every row's "Example from spec" / "Example based on spec"
columns in the new grammar:

| Grammar Construct | Example from spec | Java Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one class | `<Prog>` in `<Prog> **= <Expr>` | Java class with public fields and constructor | `class Prog extends _Start { public ArrayList<Expr> exprList; ... }` |
| Alternative rule (LHS, with alt name) — base nonterminal becomes abstract | `<Op:AddOp>` in `<Op:AddOp> ::= PLUS` | Java class extending the base nonterminal | `class AddOp extends Op { ... }` |
| Named non-terminal (RHS) | `<Op:op>` in `<Expr> ::= <NUM:left> <Op:op> <NUM:right>` | `op` — an `Op` instance | `op.apply(left, right)` |
| Captured terminal (RHS) | `<NUM:left>` | `left` — a `Token`; `.lexeme` for the string value | `Integer.parseInt(left.lexeme)` |
| Uncaptured terminal (RHS) | `PLUS` in `<Op:AddOp> ::= PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Expr>` | `exprList` — `ArrayList<Expr>` | `for (Expr expr : exprList)` |

The paragraph immediately below the table (illustrative default-naming
example, `<Exp>` → `exp`) needs its illustrative nonterminal renamed to
match: `<Expr>` → `expr` (`<NUM>` → `num` is unaffected).

### 3. Two stale references outside the table

Found by grepping the file for `Exp` after drafting the above — neither
is inside the quick reference example or its table, so easy to miss:

- Line ~136 ("`_run` entry point" section, abstract-class note):
  `` (see `Exp` in the quick reference example) `` → `` `Op` `` — it's
  the abstract one in the new grammar.
- Lines ~179–180 ("Generated output" file tree): `AddExp.java` /
  `NumExp.java` → `Expr.java` (added, alongside the existing `Prog.java`,
  matching the existing pattern of listing concrete-class files) and
  `AddOp.java` / `SubOp.java` (the two concrete alternatives; the
  abstract `Op.java` stays unlisted, matching the original doc's own
  practice of omitting the abstract base file from this illustrative,
  non-exhaustive list).

## Testing

Docs-only change; no automated test suite covers doc prose. Verification
is manual, matching the process that surfaced this bug in the first place
(task 5 of #162/#165: actually run the example end-to-end) — and this
issue's own experience shows why the *specific* cases matter, not just
"it runs":

1. Copy the updated grammar + fragments verbatim into a scratch
   `spec.plcc`.
2. `echo "1 + 2" | plcc-rep --spec=spec.plcc` → expect `3`.
3. `echo "5 - 3" | plcc-rep --spec=spec.plcc` → expect `2` (exercises the
   `SubOp` alternative, not just `AddOp`).

(Unlike the reverted draft, there is no longer an epsilon alternative to
separately verify at end-of-input — every `Expr` requires the same three
tokens, so there's no third shape left to check.)

## Commit shape

Docs-only, no breaking change. Single commit (or a small stack) touching
only `docs/language-guide/languages/java.md`. Final commit on the branch
closes #166 via `bin/issues/close.bash 166`.

Follow-up, same branch or a later one: `bin/issues/new.bash` for the
`javascript.md`, `python.md`, and `haskell.md` equivalents of this bug,
plus a roadmap entry in the same commit per `dev-docs/issue-conventions.md`.
(Issue #170, the FOLLOW-set bug this revision uncovered and worked
around, was filed separately and already has its own roadmap entry.)

## Files changed

| File | Change |
| --- | --- |
| `docs/language-guide/languages/java.md` | Quick reference grammar + Java fragments rewritten (left-factored via operator alternation, new `MINUS` token, renamed); "BNF to Java constructs" table re-grounded in new names; two stale `Exp`-family references outside the table corrected |
