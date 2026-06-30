# Haskell

## Prerequisites

GHC 9.4 or later and cabal 3.0 or later. Install both using [ghcup](https://www.haskell.org/ghcup/).

Verify your installation:

```bash
ghc --version
cabal --version
```

## Enabling in a spec

Add a bare `%` separator after the syntactic section, then write `Haskell` on the first non-blank line:

```text
%
Haskell
```

## Quick reference example

This example exercises every grammar construct. Later sections reference it by name.

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

Running this with `echo "1 + 2" | plcc-rep` prints `3`.

## BNF to Haskell constructs

Unlike Java, Python, and JavaScript — where each class gets its own file —
Haskell generates **one module per rule**. An abstract rule (one with
alternatives) produces a single `.hs` file whose `data` type contains all
concrete alternatives as constructors. Concrete alternatives are constructors,
not separate files.

| Grammar Construct | Example from spec | Haskell Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one module | `<Prog>` in `<Prog> **= <Exp>` | Record type with named fields | `data Prog = Prog { expList :: [Exp] }` |
| Alternative rule (LHS, with alt name) — all alternatives become constructors in the base nonterminal's module | `<Exp:AddExp>` in `<Exp:AddExp> ::= ...` | Constructor in the base nonterminal's `data` type | `data Exp = AddExp { left :: Exp, right :: Exp } \| NumExp { num :: Token }` |
| Named non-terminal (RHS) | `<Exp:left>` | Named record field of the nonterminal's type | `left :: Exp` in the `AddExp` constructor |
| Captured terminal (RHS) | `<NUM>` | Named record field of type `Token`; `lexeme` for the string value | `num :: Token` → `lexeme num` |
| Uncaptured terminal (RHS) | `PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Exp>` | `[Exp]` list field named `expList` | `expList :: [Exp]` |

Without explicit `:name` on a RHS symbol, the field name is the symbol name lowercased (e.g., `<Exp>` → `exp`, `<NUM>` → `num`). Use explicit names when two RHS symbols would produce the same field name.

## Fragment kinds

Fragments inject code at specific locations in the generated `.hs` file. Use `ModuleName:kind` to name the target module and location.

| Kind | Where injected | Typical use |
| --- | --- | --- |
| `top` | Before the `module` line | Language pragmas (`{-# LANGUAGE ... #-}`) |
| `import` | After auto-generated imports | Additional `import` statements |
| `body` | Module body, after the `FromJSON` instance | Top-level function definitions |
| `file` | Replaces the entire file | Standalone helper modules |

`body` is the default when no kind is given (plain `ModuleName` with no colon).

Haskell has no `init` or `class` hook — there is no constructor body to inject into, and no class declaration line.

**Fragment class names must be module names** — the abstract rule name (`Exp`) or a lone concrete name (`Prog`), never a concrete alternative name (`AddExp`, `NumExp`). Using a concrete alternative name produces a fatal error:

```text
plcc-haskell-emit: fragment tagged 'AddExp': AddExp is a concrete alternative of Exp.
In Haskell, concrete alternatives are constructors inside their abstract rule's module.
Use 'Exp' as the fragment class name instead.
```

### Example

```text
Exp:import
%%%
import Data.List (sort)
%%%

Exp
%%%
eval :: Exp -> Int
eval (AddExp l r) = eval l + eval r
eval (NumExp t)   = read (lexeme t)

sortedEvals :: [Exp] -> [Int]
sortedEvals es = sort (map eval es)
%%%
```

## `_run` entry point

Unlike Java, Python, and JavaScript where `_run` is a method, in Haskell `_run` is a **top-level function** defined in the start module:

```text
Prog
%%%
_run :: Prog -> String
_run (Prog es) = unlines (map (show . eval) es)
%%%
```

The function signature must be `_run :: StartModule -> String`. The return value is sent to `plcc-rep` as the result string.

If you do not define `_run`, the default `_run = show` is injected, which prints the `Show` instance of the root node.

## `LanguageError`

`LanguageError` is the intended mechanism for signaling a deliberate error in the defined language from Haskell semantics code. When thrown, `plcc-rep` prints the message and gives a fresh prompt; the session continues.

`LanguageError` is currently not accessible from user-authored module files — it is defined in the generated `Main.hs`, which user modules cannot import. Support for throwing `LanguageError` from semantics code is tracked in issues 131 and 132.

In the meantime, note that Haskell's built-in `error "message"` throws `ErrorCall`, which is treated as a **specification error** (not a language error) — `plcc-rep` will exit.

## Referencing other generated modules

Each generated `.hs` file auto-imports only the modules its record fields reference. To use a sibling module that is not auto-imported, add an `import` fragment:

```text
MyModule:import
%%%
import OtherModule
%%%
```

## Generated output

`plcc-haskell-emit` writes the following to `--output=DIR`. **All files are overwritten on every emit run.**

```
DIR/
  interpreter.cabal   — cabal project file; lists all modules
  Token.hs            — runtime Token type with lexeme field
  Main.hs             — entry point; deserializes parse tree JSON, calls _run
  Prog.hs             — one .hs per lone concrete rule
  Exp.hs              — one .hs per abstract rule (contains all alternatives as constructors)
```

Do not edit these files directly. Put all custom code in the spec's semantic section.

Run `plcc-haskell-build` to compile before running.

## Running the quick reference example

Save the spec above as `spec.plcc`. In the same directory:

```bash
echo "1 + 2" | plcc-rep
```

Expected output:

```text
3
```

`plcc-rep` auto-discovers `spec.plcc`, emits the interpreter to a temporary directory, builds it with cabal, and runs it.

## Commands

| Command | What it does |
| --- | --- |
| [`plcc-haskell-emit`](../../cli/commands/plcc-haskell-emit.md) | Writes `.hs` source files and `interpreter.cabal` to the output directory |
| [`plcc-haskell-build`](../../cli/commands/plcc-haskell-build.md) | Compiles with `cabal build`; requires GHC 9.4+ and cabal 3.0+ on `PATH` |
| [`plcc-haskell-run`](../../cli/commands/plcc-haskell-run.md) | Runs `cabal run interpreter`; requires cabal 3.0+ on `PATH` |

Unlike Python and JavaScript, a build step is required before running.

## Restrictions

- Requires GHC 9.4 or later and cabal 3.0 or later on `PATH`.
- Fragment class names must be module names (abstract rules or lone concretes) — using a concrete alternative name is a fatal error.
- No `init` or `class` fragment hooks.
- Generated files are overwritten on every emit run — do not edit them directly.
- One module per abstract rule: all concrete alternatives share the abstract rule's `.hs` file.

## Tips

- `lexeme fieldName` — `lexeme` is a record accessor function on `Token`. Write `lexeme t`, not `t.lexeme`.
- Pattern match on all constructors inside the abstract rule's `body` fragment: `eval (AddExp l r) = ...` and `eval (NumExp t) = ...` both go in the `Exp` fragment.
- Use `hPutStrLn stderr "debug"` (after `import System.IO`) for debug output so it does not interfere with the output protocol.
- `_run` must return a `String`. Use `show` to convert numeric or other results.
- The `top` fragment is useful for language extensions: `{-# LANGUAGE TupleSections #-}`.
- `read (lexeme t) :: Int` converts a token's string value to a number.
