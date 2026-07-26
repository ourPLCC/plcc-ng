# Python doc's "Quick reference example" grammar is not LL(1) — design

**Issue:** [172](../issues/done/172-python-doc-quick-reference-not-ll1.md)
**Date:** 2026-07-26
**Sibling of:** [166 (Java)](2026-07-24-166-java-doc-quick-reference-ll1-design.md) and
[171 (JavaScript)](2026-07-25-171-javascript-doc-quick-reference-ll1-design.md) — reuses their
verified grammar shape; read #166 for the full derivation and the #170 background.

## Problem

`docs/language-guide/languages/python.md`'s "Quick reference example" uses:

```
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
```

`<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>` makes `Exp` left-recursive.
PLCC-ng's LL(1) parser rejects this outright — reproduced verbatim:

```
plcc-make: error: grammar is not LL(1)

LL(1) conflict: <Exp> on lookahead NUM
```

so the doc's claim that `echo "1 + 2" | plcc-rep` prints `3` is false — the grammar
never emits, let alone runs. This is byte-for-byte the same defect #166 fixed in
`java.md` and #171 in `javascript.md`; per this repo's narrow-issue convention it
gets its own issue.

## Decision

Reuse #166/#171's fix verbatim in shape: left-factor by moving the alternation onto
the *operator*, not onto an optional trailing tail. `Expr` always requires exactly
`NUM op NUM` — no epsilon alternative nested inside `Expr` itself:

```
<Prog>     **= <Expr>
<Expr>     ::= <NUM:left> <Op:op> <NUM:right>
<Op:AddOp> ::= PLUS
<Op:SubOp> ::= MINUS
```

`Op:AddOp` and `Op:SubOp` are distinguished by their only token (`PLUS` vs. a new
`MINUS` token), so there is no FIRST/FIRST conflict, and neither `Expr` nor `Op`
ever derives the empty string. #166 established (and this design re-verified
empirically) that this shape does not trigger the #170 FOLLOW-set bug: the arbno's
own internal epsilon is still misflagged, but nothing inside `Expr` needs
`FOLLOW(Expr)` to contain `$`, so the corruption is inert. All six construct
categories the page's table documents survive: concrete rule (`Expr`, `Prog`),
alternative rule (`Op:AddOp`/`Op:SubOp`), named-nonterminal RHS (`Op:op`), captured
terminal RHS (`NUM:left`, `NUM:right`), uncaptured terminal RHS (`PLUS`), arbno
(`Prog **= Expr`).

This drops support for a bare `"1"` (no operator) — never claimed by the doc; it
existed only as #166's own stricter verification step.

Renames from the current (broken) grammar: `Exp`→`Expr`, `AddExp`→`AddOp` (now a
class over the *operator*), `NumExp`→removed (`Expr` is now the only concrete
expression shape), field `expList`→`exprList`. `Op`/`AddOp`/`SubOp` and the `MINUS`
token are new.

### Python-specific decisions

These are the points where the port diverges from the Java (#166) and JavaScript
(#171) versions:

1. **Abstract base `Op` gets no fragment.** Python has no `abstract` keyword. The
   issue directs following how this page's existing `Exp` fragment expresses the
   abstract-base idea today — and today the page gives the abstract `Exp` *no
   fragment at all*; abstractness is conveyed solely by the grammar
   (`<Op:AddOp>`/`<Op:SubOp>` make `Op` a base) and the table's "alternative rule"
   row. So `Op` gets no fragment, and each concrete subclass simply defines `apply`.
   (This matches #171's JavaScript choice; Java's version, by contrast, has an `Op`
   fragment with `public abstract int apply(...)`.)
2. **The method name stays `apply`.** `apply` is not a reserved word or dunder in
   Python 3 (it was a builtin removed in Python 2→3, but is free as a method name);
   `self.op` is an `Op` *instance*, so `self.op.apply(a, b)` invokes the class
   method cleanly. Keeping `apply` matches the Java/JS docs for cross-language
   consistency. `Expr.eval()` does
   `return self.op.apply(int(self.left.lexeme), int(self.right.lexeme))`.
3. **The Fragment-kinds `WholeExp` example needs NO change.** Unlike JavaScript's
   `MathHelper` example (which #171 had to re-ground because it referenced
   `NumExp`/`this.num`), Python's Fragment-kinds "### Example" uses a self-contained
   `WholeExp` class with a `self.whole` field, invented for that section and
   unconnected to the quick-reference grammar. It is left untouched. This is the
   notable divergence from #171.
4. **The `self.num` Tips line stays.** The Tips note "`self.num.lexeme` is always a
   string. Use `int(self.num.lexeme)` ..." is a generic illustration of a `<NUM>`
   capture — the default-naming paragraph still documents `<NUM>` → `self.num` as
   the generic lowercasing rule — not a reference to the quick-reference grammar
   (which now captures as `<NUM:left>`/`<NUM:right>`). It is left untouched.

### Representation-framing note (deliberately out of scope)

The real `plcc-python-emit` output is *plain* classes with an `__init__` (e.g.
`class Prog(_Start)` with `self.exprList = exprList`), not `@dataclass` classes. The
page's existing "BNF to Python constructs" table already frames the generated code
as "Python dataclass", a pre-existing idealization unrelated to this issue. Per the
brainstorming skill's "don't propose unrelated refactoring," this design preserves
that framing and only re-grounds the *names*, exactly as #166/#171 re-grounded their
tables in each page's own established idiom. Correcting the dataclass-vs-plain-class
framing, if wanted, belongs in its own issue.

## Changes

### 1. Quick reference example (grammar + Python fragments)

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
Python

Prog
%%%
def _run(self):
    return '\n'.join(str(expr.eval()) for expr in self.exprList)
%%%

Expr
%%%
def eval(self):
    return self.op.apply(int(self.left.lexeme), int(self.right.lexeme))
%%%

AddOp
%%%
def apply(self, left, right):
    return left + right
%%%

SubOp
%%%
def apply(self, left, right):
    return left - right
%%%
```

`Expr.eval()` parses both captured numbers and delegates the arithmetic to
`self.op.apply(...)`; `AddOp`/`SubOp` each implement `apply` for their one operator.
`Prog._run()` is structurally unchanged from the current doc (same join-over-
comprehension pattern) except for the `Expr`/`exprList` rename. The doc's claim
below the block — "Running this with `echo "1 + 2" | plcc-rep` prints `3`." — needs
no wording change; it is simply now true. The separate "Running the quick reference
example" section (its `echo "1 + 2"` → `3` block) likewise stays as-is.

### 2. "BNF to Python constructs" table

Re-ground every row's example columns in the new grammar (keeping the page's
existing dataclass framing per the note above):

| Grammar Construct | Example from spec | Python Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one class | `<Prog>` in `<Prog> **= <Expr>` | Python dataclass with fields | `@dataclass class Prog(_Start): exprList: List[Expr]` |
| Alternative rule (LHS, with alt name) — base nonterminal becomes abstract | `<Op:AddOp>` in `<Op:AddOp> ::= PLUS` | Python dataclass extending the base nonterminal | `@dataclass class AddOp(Op): ...` |
| Named non-terminal (RHS) | `<Op:op>` in `<Expr> ::= <NUM:left> <Op:op> <NUM:right>` | `self.op` — an `Op` instance | `self.op.apply(left, right)` |
| Captured terminal (RHS) | `<NUM:left>` | `self.left` — a `Token`; `.lexeme` for the string value | `int(self.left.lexeme)` |
| Uncaptured terminal (RHS) | `PLUS` in `<Op:AddOp> ::= PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Expr>` | `self.exprList` — `List[Expr]` | `[e.eval() for e in self.exprList]` |

The default-naming paragraph immediately below the table renames its illustrative
nonterminal: `<Exp>` → `self.exp` becomes `<Expr>` → `self.expr` (`<NUM>` →
`self.num` is unaffected — it stays as the generic lowercasing illustration).

### 3. Other stale references outside the example and table

Found by grepping the whole file (per the issue's warning):

- **`_run` entry point example** (~line 109): `self.expList` → `self.exprList` and
  the comprehension variable `exp` → `expr`. The surrounding prose ("`Prog` in the
  quick reference example") is unaffected — `Prog` is still the start class.
- **Generated output file tree** (~lines 159–160): `AddExp.py` / `NumExp.py` →
  `Expr.py` (alongside the existing `Prog.py`), `AddOp.py`, and `SubOp.py`. The
  abstract `Op.py` stays unlisted, matching the current doc's practice of omitting
  the abstract base from this illustrative, non-exhaustive list (it already omits
  `Exp.py`, even though the emitter does write it).

No Tips lines need changing: unlike #171's JavaScript page, Python's Tips section
names no quick-reference class (`Op`/`Exp`/`expList`) — its abstract-class note is
generic ("Abstract classes have no constructor"), and its `self.num` note is a
generic capture illustration (see Python-specific decision 4).

## Testing

Docs-only change; no automated suite covers doc prose. Verification is manual,
matching the process that surfaced this class of bug (actually running the example
end-to-end). Already performed against a scratch `spec.plcc` holding the exact
grammar + fragments above:

1. Broken (current-doc) spec → `plcc-make: error: grammar is not LL(1)` /
   `LL(1) conflict: <Exp> on lookahead NUM` (reproduces the issue).
2. `echo "1 + 2" | plcc-rep --spec=spec.plcc` → `3`.
3. `echo "5 - 3" | plcc-rep --spec=spec.plcc` → `2` (exercises the `SubOp`
   alternative, not just `AddOp`).

Every `Expr` requires the same three tokens, so there is no epsilon/end-of-input
shape left to check separately.

## Commit shape

Docs-only, no breaking change. Work lands in the existing `worktree-run-contract-impl`
worktree (per direction), on its current branch — no new branch/worktree. Per user
direction this issue skips a separate plan doc (the change is a mechanical third
sibling of two already-executed plans); a small commit stack touches only
`docs/language-guide/languages/python.md` plus this design doc. Final commit on the
branch closes #172 via `bin/issues/close.bash 172` (moves the issue to `done/` and
updates the roadmap).

## Files changed

| File | Change |
| --- | --- |
| `docs/language-guide/languages/python.md` | Quick reference grammar + Python fragments rewritten (operator-alternation left-factoring, new `MINUS` token, renamed, no `Op` fragment); "BNF to Python constructs" table and default-naming paragraph re-grounded; `_run`-entry-point example and Generated-output list corrected. `WholeExp` Fragment-kinds example and `self.num` Tips line deliberately unchanged. |
| `dev-docs/specs/2026-07-26-172-python-doc-quick-reference-ll1-design.md` | This design doc |
