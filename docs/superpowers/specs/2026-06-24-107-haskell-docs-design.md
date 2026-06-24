# Design: Haskell Language Extension Documentation (Issue 107)

**Date:** 2026-06-24
**Issue:** 107

## Goal

Add a student-facing documentation page for the Haskell language extension,
following the same 12-section template established by the JavaScript, Java, and
Python pages. The page must explain Haskell's unusual one-module-per-rule model
clearly enough that a student who knows Haskell but not plcc-ng can write a
working semantic section.

## Key structural difference from other languages

Every other language (Java, Python, JavaScript) generates **one file per class**
— including concrete alternatives. Haskell generates **one module per rule**:

- An **abstract rule** (one with alternatives) → one `.hs` file containing a
  `data` type with all concrete alternatives as constructors.
  Example: `<Exp:AddExp>` and `<Exp:NumExp>` → `Exp.hs` with
  `data Exp = AddExp { left :: Exp, right :: Exp } | NumExp { num :: Token }`.
- A **lone concrete rule** (no abstract parent) → one `.hs` file.
  Example: `<Prog> **= <Exp>` → `Prog.hs` with `data Prog = Prog { expList :: [Exp] }`.

Consequence: **fragment class names must be module names** (abstract rules or
lone concretes), never concrete alternative names. Since issue 105 was fixed,
using a concrete alternative name (e.g. `AddExp`) is a fatal error with a
message directing the user to the abstract rule name.

## Language tag

`Haskell` (capital H) — consistent with `Java` and `Python`.

## Canonical example

Same expression evaluator grammar used across all language pages:

```text
token NUM   '\d+'
token PLUS  '\+'
skip  SPACE '\s+'
%
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
%
Haskell

Prog
%%%
_run :: Prog -> String
_run (Prog es) = unlines (map (show . eval) es)
%%%

Exp
%%%
eval :: Exp -> Int
eval (AddExp l r) = eval l + eval r
eval (NumExp t)   = read (lexeme t)
%%%
```

Style confirmed against `tests/bats/e2e/haskell.bats`:
- Positional pattern matching (`_run (Prog es)`, not record syntax)
- `lexeme fieldName` function application (not dot notation)
- Concrete alternatives (`AddExp`, `NumExp`) are matched as constructors
  inside the abstract rule's fragment (`Exp`) — they do not have their own fragment

## BNF to Haskell constructs table (4-column format)

| Grammar Construct | Example from spec | Haskell Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one module | `<Prog>` in `<Prog> **= <Exp>` | Record type with named fields | `data Prog = Prog { expList :: [Exp] }` |
| Alternative rule (LHS, with alt name) — all alternatives become constructors of one type in the base nonterminal's module | `<Exp:AddExp>` in `<Exp:AddExp> ::= ...` | Constructor in the base nonterminal's `data` type | `data Exp = AddExp { left :: Exp, right :: Exp } \| NumExp { num :: Token }` |
| Named non-terminal (RHS) | `<Exp:left>` | Named record field of the nonterminal's type | `left :: Exp` in the `AddExp` constructor |
| Captured terminal (RHS) | `<NUM>` | Named record field of type `Token`; `lexeme` for the string value | `num :: Token` → `lexeme num` |
| Uncaptured terminal (RHS) | `PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Exp>` | `[Exp]` list field named `expList` | `expList :: [Exp]` |

Note below table: without explicit `:name` on a RHS symbol, the field name is the
symbol name lowercased (`<Exp>` → `exp`, `<NUM>` → `num`).

## Sections

### 1. Prerequisites

GHC and cabal. Recommend `ghcup` for installation. Minimum versions:
GHC 9.4+ and cabal 3.0+ (the generated cabal file uses `cabal-version: 3.0`
and `Haskell2010`; GHC 9.4 is the oldest series with active security support).

Verify:
```bash
ghc --version
cabal --version
```

### 2. Enabling in a spec

Language tag `Haskell`.

### 3. Quick reference example

The canonical example above. Running with `echo "1 + 2" | plcc-rep` prints `3`.

### 4. BNF to Haskell constructs

4-column table as above.

### 5. Fragment kinds

| Kind | Where injected | Typical use |
| --- | --- | --- |
| `top` | Before the `module` line (language pragmas) | `{-# LANGUAGE ... #-}` extensions |
| `import` | After auto-generated imports | Additional `import` statements |
| `body` | Module body, after the `FromJSON` instance | Top-level function definitions |
| `file` | Replaces the entire file | Standalone helper modules |

No `init` (no constructor injection — Haskell is functional) or `class`
(no class declaration line to annotate).

`body` is the default when no kind is given.

Critical rule: **fragment class names must be module names** — the abstract
rule name (`Exp`) or a lone concrete name (`Prog`), never a concrete
alternative name (`AddExp`, `NumExp`). Using a concrete alternative name
produces a fatal error with a message naming the correct module to use.

Include a fragment kinds example showing `top` (pragma) + `import` + `body`
together on one class.

### 6. `_run` entry point

Unlike Java/Python/JavaScript where `_run` is a method, in Haskell it is a
**top-level function**:

```haskell
_run :: StartModule -> String
```

It is injected into the start module's `.hs` file. If not defined by the user,
the default `_run = show` is injected. The return value is sent back to
`plcc-rep` as the result string.

### 7. Referencing other generated modules

Other generated modules are not auto-imported into every module. To use a
sibling module, add an `import` fragment:

```text
MyModule:import
%%%
import OtherModule
%%%
```

Note that the generated `Main.hs` imports all modules, but each `.hs` file
only auto-imports the modules it references based on its fields' types.

### 8. Generated output

`plcc-haskell-emit` writes to `--output=DIR`. All files are overwritten on
every emit run.

```
DIR/
  interpreter.cabal   — cabal project file; lists all modules as dependencies
  Token.hs            — runtime Token type with lexeme field
  Main.hs             — entry point; deserializes parse tree JSON, calls _run
  Prog.hs             — one .hs per lone concrete rule
  Exp.hs              — one .hs per abstract rule (contains all alternatives)
```

Run `plcc-haskell-build` to compile with cabal. Run `plcc-haskell-run` to
execute. Do not edit generated files directly.

### 9. Running the quick reference example

Same pattern as other language pages: save spec, `echo "1 + 2" | plcc-rep`,
expected output `3`.

### 10. Commands

| Command | What it does |
| --- | --- |
| `plcc-haskell-emit` | Writes `.hs` source files and `interpreter.cabal` to output directory |
| `plcc-haskell-build` | Compiles with `cabal build`; requires GHC and cabal on `PATH` |
| `plcc-haskell-run` | Runs with `cabal run interpreter`; requires cabal on `PATH` |

Unlike Python and JavaScript, a build step is required before running.

### 11. Restrictions

- Requires GHC and cabal on `PATH`.
- Fragment class names must be module names (abstract rules or lone concretes).
  Using a concrete alternative name is a fatal error.
- Generated files are overwritten on every emit run — do not edit directly.
- No `init` or `class` fragment hooks.
- One module per abstract rule: all concrete alternatives share the abstract
  rule's module.

### 12. Tips

- `lexeme fieldName` (not `fieldName.lexeme`) — `lexeme` is a record field
  accessor function applied to a `Token`.
- Use `hPutStrLn stderr "debug"` (after `import System.IO`) for debug output
  so it does not corrupt the stdout protocol.
- Pattern match on constructors inside the abstract rule's fragment:
  `eval (AddExp l r) = ...` and `eval (NumExp t) = ...` both go in the `Exp`
  fragment, not in `AddExp` or `NumExp` fragments.
- `_run` must return a `String`. Use `show` to convert numeric results.
- The `top` fragment is useful for enabling language extensions:
  `{-# LANGUAGE TupleSections #-}` etc.
- `read (lexeme t) :: Int` converts a token's string value to a number.

## Files to create

- `docs/language-guide/languages/haskell.md` — the main deliverable
- `docs/cli/commands/plcc-haskell-emit.md`
- `docs/cli/commands/plcc-haskell-build.md`
- `docs/cli/commands/plcc-haskell-run.md`

## Files to modify

- `docs/cli/guide/language-extensions.md` — add `## plcc-haskell` section
- `mkdocs.yml` — add Haskell to Languages nav and CLI commands list
