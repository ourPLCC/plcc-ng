# Haskell doc's "Quick reference example" grammar is not LL(1) — design

**Issue:** [173](../issues/done/173-haskell-doc-quick-reference-not-ll1.md)
**Date:** 2026-07-26
**Sibling of:** [166 (Java)](2026-07-24-166-java-doc-quick-reference-ll1-design.md),
[171 (JavaScript)](2026-07-25-171-javascript-doc-quick-reference-ll1-design.md),
[172 (Python)](2026-07-26-172-python-doc-quick-reference-ll1-design.md) — reuses their
verified grammar shape; read #166 for the full derivation and the #170 background.
This is the fourth and final sibling.

## Problem

`docs/language-guide/languages/haskell.md`'s "Quick reference example" uses:

```
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
```

`<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>` makes `Exp` left-recursive.
PLCC-ng's LL(1) parser rejects this outright — the syntactic section is byte-for-byte
identical to the Python/Java/JS broken specs, which reproduce as:

```
plcc-make: error: grammar is not LL(1)

LL(1) conflict: <Exp> on lookahead NUM
```

The LL(1) check is purely syntactic and language-independent, so the doc's claim that
`echo "1 + 2" | plcc-rep` prints `3` is false — the grammar never emits, let alone
builds or runs.

## Decision

Reuse the siblings' fix verbatim in shape: left-factor by moving the alternation onto
the *operator*, not onto an optional trailing tail. `Expr` always requires exactly
`NUM op NUM` — no epsilon alternative nested inside `Expr` itself:

```
<Prog>     **= <Expr>
<Expr>     ::= <NUM:left> <Op:op> <NUM:right>
<Op:AddOp> ::= PLUS
<Op:SubOp> ::= MINUS
```

`Op:AddOp` and `Op:SubOp` are distinguished by their only token (`PLUS` vs. a new
`MINUS` token), so there is no FIRST/FIRST conflict, and neither `Expr` nor `Op` ever
derives the empty string. #166 established that this shape does not trigger the #170
FOLLOW-set bug: the arbno's own internal epsilon is still misflagged, but nothing
inside `Expr` needs `FOLLOW(Expr)` to contain `$`, so the corruption is inert.

Renames from the current (broken) grammar: `Exp`→`Expr`, `AddExp`→`AddOp` (now a
constructor over the *operator*), `NumExp`→removed (`Expr` is now the only concrete
expression shape), field `expList`→`exprList`. `Op`/`AddOp`/`SubOp` and the `MINUS`
token are new.

## Haskell-specific decisions — the reason this is its own issue

Haskell's code-generation model differs structurally from Java/JS/Python, and the
fragment structure must be designed around it from the start (not ported from a
sibling). All of the following were verified against real `plcc-haskell-emit` output
(see Testing):

1. **One module per rule; concrete alternatives are constructors, not files.** The
   emitter produces `Prog.hs`, `Expr.hs` (both lone concretes → their own modules),
   and `Op.hs` (abstract rule → a `data Op = AddOp | SubOp` with the two alternatives
   as *fieldless constructors*). There is no `AddOp.hs`/`SubOp.hs`.

2. **Fragment class names must be module names.** Tagging a fragment with a concrete
   alternative name is a fatal error — reproduced verbatim for the new grammar:

   ```
   plcc-haskell-emit: fragment tagged 'AddOp': AddOp is a concrete alternative of Op.
   In Haskell, concrete alternatives are constructors inside their abstract rule's module.
   Use 'Op' as the fragment class name instead.
   ```

   So Java/JS/Python's per-class `AddOp`/`SubOp` fragments are impossible here. The
   operator logic lives as **pattern-matched clauses in a single `Op` fragment**:
   `apply AddOp l r = l + r` / `apply SubOp l r = l - r`. This is the central
   divergence from the three prior siblings.

3. **`apply` is a standalone top-level function, not a method.** `Op` is a plain
   `data` type with no methods; `apply :: Op -> Int -> Int -> Int` is a module-level
   function defined in the `Op` fragment. `Expr.eval` calls it as `apply o …` (value
   position), where the Java/JS/Python versions wrote `self.op.apply(…)` /
   `this.op.apply(…)` / `op.apply(…)`.

4. **The cross-module calls resolve via whole-module exports/imports** — verified in
   the emitted source:
   - `Op.hs` is `module Op where` (no explicit export list) → exports `apply`.
   - `Expr.hs` has `import Op` (unqualified, whole module, auto-generated because
     `Expr` has field `op :: Op`) → the `apply` *function* is in scope, not merely
     the `Op` type. `eval (Expr l o r) = apply o (read (lexeme l)) (read (lexeme r))`
     compiles.
   - `Prog.hs` has `import Expr` (auto-generated from field `exprList :: [Expr]`) →
     `eval` is in scope for `_run (Prog es) = unlines (map (show . eval) es)`.
   No hand-written `import` fragment is needed for the quick-reference example.

5. **`eval` distributes differently than the original.** The old doc put a single
   `eval :: Exp -> Int` with two clauses (`AddExp`, `NumExp`) in the abstract `Exp`
   module. The new grammar splits it: `eval :: Expr -> Int` (single clause) lives in
   the concrete `Expr` module and delegates the arithmetic to `apply`, which
   pattern-matches the operator in the abstract `Op` module. Every construct the
   page's table documents still appears.

## Changes

### 1. Quick reference example (grammar + Haskell fragments)

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
Haskell

Prog
%%%
_run :: Prog -> String
_run (Prog es) = unlines (map (show . eval) es)
%%%

Expr
%%%
eval :: Expr -> Int
eval (Expr l o r) = apply o (read (lexeme l)) (read (lexeme r))
%%%

Op
%%%
apply :: Op -> Int -> Int -> Int
apply AddOp l r = l + r
apply SubOp l r = l - r
%%%
```

`Expr.eval` reads both captured numbers and delegates the arithmetic to `apply o …`;
the `Op` fragment's two `apply` clauses implement the operators. `Prog._run` is
unchanged in shape from the current doc (same `unlines (map (show . eval) es)`), only
the `Exp`→`Expr` element type behind `es` changes. The doc's claim below the block —
"Running this with `echo "1 + 2" | plcc-rep` prints `3`." — needs no wording change;
it is simply now true. The separate "Running the quick reference example" section
(its `echo "1 + 2"` → `3` block) likewise stays as-is.

### 2. "BNF to Haskell constructs" table

Re-ground every row's example columns in the new grammar (the intro paragraph above
the table — "one module per rule / concrete alternatives are constructors" — is
generic and unchanged):

| Grammar Construct | Example from spec | Haskell Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one module | `<Prog>` in `<Prog> **= <Expr>` | Record type with named fields | `data Prog = Prog { exprList :: [Expr] }` |
| Alternative rule (LHS, with alt name) — all alternatives become constructors in the base nonterminal's module | `<Op:AddOp>` in `<Op:AddOp> ::= PLUS` | Constructor in the base nonterminal's `data` type | `data Op = AddOp \| SubOp` |
| Named non-terminal (RHS) | `<Op:op>` in `<Expr> ::= <NUM:left> <Op:op> <NUM:right>` | Named record field of the nonterminal's type | `op :: Op` in the `Expr` constructor |
| Captured terminal (RHS) | `<NUM:left>` | Named record field of type `Token`; `lexeme` for the string value | `left :: Token` → `lexeme left` |
| Uncaptured terminal (RHS) | `PLUS` in `<Op:AddOp> ::= PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Expr>` | `[Expr]` list field named `exprList` | `exprList :: [Expr]` |

The default-naming paragraph immediately below the table renames its illustrative
nonterminal: `<Exp>` → `exp` becomes `<Expr>` → `expr` (`<NUM>` → `num` is
unaffected — it stays as the generic lowercasing illustration).

### 3. Fragment-kinds constraint paragraph and its error block

The paragraph explaining "Fragment class names must be module names" uses the
quick-reference grammar's names as its examples; re-ground them:

- Prose: "the abstract rule name (`Op`) or a lone concrete name (`Prog`), never a
  concrete alternative name (`AddOp`, `SubOp`)".
- The fatal-error code block is replaced with the verified real output for the new
  grammar (see Haskell-specific decision 2): `fragment tagged 'AddOp': AddOp is a
  concrete alternative of Op. … Use 'Op' as the fragment class name instead.`

### 4. Fragment-kinds "### Example"

This illustrative `import` + `body` example currently references `Exp`/`AddExp`/
`NumExp`. Unlike Python's self-contained `WholeExp` example (which #172 left
untouched), this one is grounded in the quick-reference grammar, so it is re-grounded
— parallel to #171's `MathHelper` re-grounding, and onto the concrete `Expr` module
(the one that carries `eval`) for a minimal, faithful port:

```
Expr:import
%%%
import Data.List (sort)
%%%

Expr
%%%
eval :: Expr -> Int
eval (Expr l o r) = apply o (read (lexeme l)) (read (lexeme r))

sortedEvals :: [Expr] -> [Int]
sortedEvals es = sort (map eval es)
%%%
```

Structurally identical to the original (`sortedEvals :: [X] -> [Int]` = `sort (map
eval es)`); only the type/pattern change to `Expr` and the `eval` body updates.

### 5. Other stale references outside the example and table

Found by grepping the whole file (per the issue's warning):

- **Generated output file tree** (~line 160): `Exp.hs — one .hs per abstract rule` →
  `Op.hs — one .hs per abstract rule (contains all alternatives as constructors)`,
  and add `Expr.hs` as a second lone-concrete file alongside `Prog.hs` (the emitter
  writes `Prog.hs`, `Expr.hs`, and `Op.hs`; `AddOp.hs`/`SubOp.hs` do not exist).
- **Tips — pattern-match tip** (~line 205): "`eval (AddExp l r) = ...` and `eval
  (NumExp t) = ...` both go in the `Exp` fragment" → "`apply AddOp l r = ...` and
  `apply SubOp l r = ...` both go in the `Op` fragment" — the pattern-matched
  multi-clause function in the new grammar is `apply` in the abstract `Op` module.

### 6. Deliberately unchanged

- **`_run` entry-point section example** (~lines 122–123): `_run (Prog es) = unlines
  (map (show . eval) es)`. It binds `Prog`'s single field positionally as `es` and
  maps `eval`; with `data Prog = Prog { exprList :: [Expr] }` this stays correct
  as-is (it names no `Exp`/`AddExp`/`NumExp`).
- **Generic Tips lines**: `lexeme t` (not `t.lexeme`) and `read (lexeme t) :: Int`
  are generic capture illustrations, not quick-reference references.
- **Module-per-rule intro paragraph** and the **Restrictions bullet** ("One module
  per abstract rule…") name no quick-reference class; unchanged.

## Testing

Docs-only change; no automated suite covers doc prose. Verification here is
constrained by the environment: **GHC 9.4+/cabal are not installed**, so the example
cannot be compiled and run end-to-end (`plcc-rep` for a Haskell spec emits → builds
→ runs, and the build stage is unavailable). Verification was therefore done at the
emit level, which is the same `plcc-spec → plcc-model → plcc-haskell-emit` pipeline
the repo's own `tests/bats/e2e/haskell.bats` exercises:

1. `plcc-haskell-emit` on the new grammar + fragments **succeeds** (exit 0) and
   writes `Prog.hs`, `Expr.hs`, `Op.hs`, `Token.hs`, `Main.hs`, `LanguageError.hs`,
   `interpreter.cabal`.
2. The generated modules were inspected and the cross-module references shown to
   resolve: `Op.hs` = `module Op where` (exports `apply`); `Expr.hs` = `import Op`
   (whole-module, brings `apply` into scope) with `data Expr = Expr { left :: Token,
   op :: Op, right :: Token }`; `Prog.hs` = `import Expr` with `data Prog = Prog {
   exprList :: [Expr] }`; `data Op = AddOp | SubOp`. The fragment bodies (`_run`,
   `eval`, `apply`) type-check by inspection (`read (lexeme _)` pinned to `Int` by
   `apply`'s signature; `unlines (map (show . eval) es)` is `[Expr] → String`).
3. The concrete-alternative fragment error was reproduced verbatim by tagging a
   fragment `AddOp` (see Haskell-specific decision 2), confirming the doc's updated
   error block is accurate real output.

**Open verification gap (to close on a GHC-equipped machine):** run
`echo "1 + 2" | plcc-rep` → expect `3` and `echo "5 - 3" | plcc-rep` → expect `2`
against the updated spec, confirming the emitted Haskell compiles and evaluates. The
generated source is straightforward and the types check by inspection, but a real
`cabal build` + run has not been performed in this environment.

## Commit shape

Docs-only, no breaking change. Work lands in the existing `worktree-run-contract-impl`
worktree, on its current branch — no new branch/worktree. Per user direction this
issue skips a separate plan doc (mechanical fourth sibling); a small commit stack
touches only `docs/language-guide/languages/haskell.md` plus this design doc. Final
commit closes #173 via `bin/issues/close.bash 173` (moves the issue to `done/` and
updates the roadmap); any close.bash over-mangling of creation-time paths in a
sibling plan doc is corrected in the same commit, per the #171/#172 precedent.

## Files changed

| File | Change |
| --- | --- |
| `docs/language-guide/languages/haskell.md` | Quick reference grammar + Haskell fragments rewritten (operator-alternation left-factoring, new `MINUS` token; operator logic as pattern-matched clauses in one `Op` fragment, not per-alternative fragments); "BNF to Haskell constructs" table and default-naming paragraph re-grounded; Fragment-kinds constraint paragraph + error block updated to `Op`/`AddOp`/`SubOp` (verified real output); Fragment-kinds "### Example" re-grounded on `Expr`; Generated-output list and the pattern-match Tips line corrected. `_run`-entry-point example and generic Tips lines deliberately unchanged. |
| `dev-docs/specs/2026-07-26-173-haskell-doc-quick-reference-ll1-design.md` | This design doc |
