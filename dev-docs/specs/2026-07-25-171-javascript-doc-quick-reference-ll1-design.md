# JavaScript doc's "Quick reference example" grammar is not LL(1) — design

**Issue:** [171](../issues/done/171-javascript-doc-quick-reference-not-ll1.md)
**Date:** 2026-07-25
**Sibling of:** [166 (Java)](2026-07-24-166-java-doc-quick-reference-ll1-design.md) — reuses its
verified grammar shape; read it for the full derivation and the #170 background.

## Problem

`docs/language-guide/languages/javascript.md`'s "Quick reference example" uses:

```
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
```

`<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>` makes `Exp` left-recursive.
PLCC-ng's LL(1) parser rejects this outright (same FIRST/FIRST conflict as
#166), so the doc's claim that `echo "1 + 2" | plcc-rep` prints `3` is false —
the grammar never emits, let alone runs. This is byte-for-byte the same defect
#166 fixed in `java.md`; per this repo's narrow-issue convention it gets its own
issue (siblings #172 python, #173 haskell also exist).

## Decision

Reuse #166's fix verbatim in shape: left-factor by moving the alternation onto
the *operator*, not onto an optional trailing tail. `Expr` always requires
exactly `NUM op NUM` — no epsilon alternative nested inside `Expr` itself:

```
<Prog>     **= <Expr>
<Expr>     ::= <NUM:left> <Op:op> <NUM:right>
<Op:AddOp> ::= PLUS
<Op:SubOp> ::= MINUS
```

`Op:AddOp` and `Op:SubOp` are distinguished by their only token (`PLUS` vs. a new
`MINUS` token), so there is no FIRST/FIRST conflict, and neither `Expr` nor `Op`
ever derives the empty string. #166 established (and verified empirically) that
this shape does not trigger the #170 FOLLOW-set bug: the arbno's own internal
epsilon is still misflagged, but nothing inside `Expr` needs `FOLLOW(Expr)` to
contain `$`, so the corruption is inert. All six construct categories the page's
table documents survive: concrete rule (`Expr`, `Prog`), alternative rule
(`Op:AddOp`/`Op:SubOp`), named-nonterminal RHS (`Op:op`), captured terminal RHS
(`NUM:left`, `NUM:right`), uncaptured terminal RHS (`PLUS`), arbno
(`Prog **= Expr`).

This drops support for a bare `"1"` (no operator) — never claimed by the doc; it
existed only as #166's own stricter verification step.

Renames from the current (broken) grammar: `Exp`→`Expr`, `AddExp`→`AddOp` (now a
class over the *operator*), `NumExp`→removed (`Expr` is now the only concrete
expression shape), field `expList`→`exprList`. `Op`/`AddOp`/`SubOp` and the
`MINUS` token are new.

### JavaScript-specific decisions

These are the points where the port diverges from #166's Java version:

1. **Abstract base `Op` gets no fragment.** JavaScript has no `abstract`
   keyword. The issue directs following "how this page's existing `Exp` fragment
   expresses the abstract-base idea today" — and today the page gives the
   abstract `Exp` *no fragment at all*; abstractness is conveyed solely by the
   grammar (`<Op:AddOp>`/`<Op:SubOp>` make `Op` a base), the table's
   "alternative rule" row, and the Tips note. So `Op` gets no fragment, and each
   concrete subclass simply defines `apply`. (Java's version, by contrast, has
   an `Op` fragment with `public abstract int apply(...)`.)
2. **The Fragment-kinds `MathHelper` example is re-grounded on `Expr`.** That
   illustrative example (import + file fragments) currently references `NumExp`
   and `this.num.lexeme`, both of which the new grammar removes. It is rewritten
   to use `Expr` and `this.left.lexeme`/`this.right.lexeme`, preserving the same
   `import`/`file` demonstration. This example is a JS-page-only structure that
   #166's Java design did not have — the kind of out-of-example reference the
   issue warns a narrow fix would miss.
3. **The method name stays `apply`.** `this.op` is a class *instance*, not a
   function, so `this.op.apply(a, b)` invokes the class method and does not clash
   with `Function.prototype.apply`. Keeping `apply` matches the Java doc for
   cross-language consistency.

## Changes

### 1. Quick reference example (grammar + JavaScript fragments)

Replace the grammar block, add a `MINUS` token, and replace the fragments:

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
javascript

Expr
%%%
eval() {
    return this.op.apply(parseInt(this.left.lexeme), parseInt(this.right.lexeme));
}
%%%

Prog
%%%
_run() {
    return this.exprList.map(expr => String(expr.eval())).join('\n');
}
%%%

AddOp
%%%
apply(left, right) {
    return left + right;
}
%%%

SubOp
%%%
apply(left, right) {
    return left - right;
}
%%%
```

`Expr.eval()` parses both captured numbers and delegates the arithmetic to
`this.op.apply(...)`; `AddOp`/`SubOp` each implement `apply` for their one
operator. `Prog._run()` is structurally unchanged from the current doc (same
map-and-join pattern) except for the `Expr`/`exprList` rename. The doc's claim
below the block — "Running this with `echo "1 + 2" | plcc-rep` prints `3`." —
needs no wording change; it is simply now true. The separate "Running the quick
reference example" section (its `echo "1 + 2"` → `3` block) likewise stays as-is.

### 2. "BNF to JavaScript constructs" table

Re-ground every row's example columns in the new grammar:

| Grammar Construct | Example from spec | JavaScript Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one class | `<Prog>` in `<Prog> **= <Expr>` | ES6 class with constructor and fields | `class Prog extends _Start { constructor(exprList) { ... } }` |
| Alternative rule (LHS, with alt name) — base nonterminal becomes abstract | `<Op:AddOp>` in `<Op:AddOp> ::= PLUS` | ES6 class extending the base nonterminal | `class AddOp extends Op { ... }` |
| Named non-terminal (RHS) | `<Op:op>` in `<Expr> ::= <NUM:left> <Op:op> <NUM:right>` | `this.op` — an `Op` instance | `this.op.apply(left, right)` |
| Captured terminal (RHS) | `<NUM:left>` | `this.left` — a `Token`; `.lexeme` for the string value | `parseInt(this.left.lexeme)` |
| Uncaptured terminal (RHS) | `PLUS` in `<Op:AddOp> ::= PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Expr>` | `this.exprList` — `Array` of `Expr` | `this.exprList.map(e => e.eval())` |

The default-naming paragraph immediately below the table renames its
illustrative nonterminal: `<Exp>` → `this.exp` becomes `<Expr>` → `this.expr`
(`<NUM>` → `this.num` is unaffected).

### 3. Fragment-kinds `MathHelper` example

Rewrite from `NumExp`/`this.num` to `Expr`/`this.left`/`this.right`:

```
Expr:import
%%%
const { MathHelper } = require('./MathHelper');
%%%

Expr
%%%
eval() {
    return this.op.apply(MathHelper.parse(this.left.lexeme), MathHelper.parse(this.right.lexeme));
}
%%%

MathHelper:file
%%%
class MathHelper {
    static parse(s) { return parseInt(s, 10); }
}
module.exports = { MathHelper };
%%%
```

### 4. Other stale references outside the example and table

Found by grepping the whole file (per the issue's warning):

- **`_run` entry point example** (~line 122): `this.expList` → `this.exprList`.
  The surrounding prose ("`Prog` in the quick reference example") is unaffected —
  `Prog` is still the start class.
- **Generated output file tree** (~lines 176–177): `AddExp.js` / `NumExp.js` →
  `Expr.js` (alongside the existing `Prog.js`), `AddOp.js`, and `SubOp.js`. The
  abstract `Op.js` stays unlisted, matching the current doc's practice of
  omitting the abstract base from this illustrative, non-exhaustive list (it
  already omits `Exp.js`).
- **Tips** (~line 223): "Abstract classes (`Exp` in the quick reference example)"
  → `Op`.
- **Tips** (~line 224): "For `<Prog> **= <Exp>`, the field is `this.expList`" →
  "For `<Prog> **= <Expr>`, the field is `this.exprList`".

## Testing

Docs-only change; no automated suite covers doc prose. Verification is manual,
matching the process that surfaced this class of bug (actually running the
example end-to-end):

1. Copy the updated grammar + fragments verbatim into a scratch `spec.plcc`.
2. `echo "1 + 2" | plcc-rep --spec=spec.plcc` → expect `3`.
3. `echo "5 - 3" | plcc-rep --spec=spec.plcc` → expect `2` (exercises the
   `SubOp` alternative, not just `AddOp`).

Every `Expr` requires the same three tokens, so there is no epsilon/end-of-input
shape left to check separately.

## Commit shape

Docs-only, no breaking change. Work lands in the existing
`worktree-run-contract-impl` worktree (per direction). Single commit (or a small
stack) touching only `docs/language-guide/languages/javascript.md` plus this
design doc. Final commit on the branch closes #171 via
`bin/issues/close.bash 171` (moves the issue to `done/` and updates the roadmap).

## Files changed

| File | Change |
| --- | --- |
| `docs/language-guide/languages/javascript.md` | Quick reference grammar + JS fragments rewritten (operator-alternation left-factoring, new `MINUS` token, renamed, no `Op` fragment); "BNF to JavaScript constructs" table and default-naming paragraph re-grounded; Fragment-kinds `MathHelper` example re-grounded on `Expr`; Generated-output list and two Tips lines corrected |
| `dev-docs/specs/2026-07-25-171-javascript-doc-quick-reference-ll1-design.md` | This design doc |
