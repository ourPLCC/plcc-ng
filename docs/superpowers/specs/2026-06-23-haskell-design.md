# Haskell Emitter Design

**Date:** 2026-06-23

## Overview

Add a Haskell language backend to plcc-ng, following the same extension pattern as the existing `java`, `python`, and `javascript` backends. Generated code uses algebraic data types (ADTs) and is compiled with `cabal build`.

Haskell was chosen as a target because Haskell programmers have strong idiomatic expectations that plcc-ng should meet. The generated code should look like code a Haskell programmer would write, not a translation of the OOP model.

## Design Decisions

### ADTs over type classes or records

Each grammar rule maps to a Haskell `data` type with one constructor per concrete alternative. This is idiomatic Haskell — pattern matching is the natural dispatch mechanism for grammar alternatives. Type classes and record-with-function-fields approaches were rejected as non-idiomatic.

### One module per rule

Each abstract class (grammar rule) becomes one `.hs` file. All concrete alternatives for that rule appear as constructors in the same module. This matches Haskell programmer expectations: function equations for a rule live together in one file, not scattered across per-constructor files. Lone concrete classes (no abstract parent) get their own module with a single-constructor data type.

### Cabal with aeson

GHC is used directly for compilation, but via `cabal build` rather than bare `ghc`. The emitter generates an `interpreter.cabal` file in the output directory. This approach was chosen because:

- JSON deserialization requires `aeson`; no suitable JSON library ships with `base`
- Getting `aeson` requires cabal anyway (via GHCup), so using cabal properly is simpler than global `--lib` installs
- The installation story is just: install GHCup (which provides both GHC and cabal)
- A hand-rolled JSON parser was rejected — it creates ongoing maintenance burden

### Fragment kinds

Matches the other backends minus `init` (which is a constructor-body hook with no Haskell equivalent):

| Kind     | Placement in generated file                                      |
|----------|------------------------------------------------------------------|
| `top`    | Before imports (e.g. language pragmas, type aliases)             |
| `import` | After generated imports, before the data declaration             |
| `body`   | After the `FromJSON` instance (top-level function definitions)   |
| `file`   | Replaces the entire generated module file                        |

Body fragments on abstract classes contain complete top-level Haskell functions that pattern-match on all constructors. This is idiomatic: the user writes `_run (AddExp l r) = ...` and `_run (NumExp t) = ...` together in the `Exp` module's body fragment.

### Entry point

The entry point function is `_run :: StartType -> String`, consistent with the other backends. If the start rule's module has no `_run` function in its body fragments, the emitter generates a default:

```haskell
_run :: StartType -> String
_run = show
```

This requires all generated types to derive `Show`, which the emitter does unconditionally.

## Extension Location

```text
src/plcc/lang/ext/haskell/
  __init__.py
  emit.py
  emit_test.py
  build.py
  build_test.py
  run.py
  run_test.py
  runtime/
    Token.hs
    token_test.py
```

No Jinja2 templates. The generated files are simple enough to construct with string formatting in `emit.py`.

## Entry Points

Three entries added to `pyproject.toml` `[project.scripts]`:

```toml
plcc-haskell-emit  = "plcc.lang.ext.haskell.emit:main"
plcc-haskell-build = "plcc.lang.ext.haskell.build:main"
plcc-haskell-run   = "plcc.lang.ext.haskell.run:main"
```

## Spec Section Tag

Users tag semantic sections with `haskell` (lowercase), consistent with other backends:

```text
%haskell
Exp
%%%
body
_run :: Exp -> String
_run (AddExp l r) = _run l ++ " + " ++ _run r
_run (NumExp t)   = lexeme t
%%%
```

## Generated Output Structure

```text
<output>/
  interpreter.cabal     ← generated; declares dependencies
  Main.hs               ← generated entry point
  Token.hs              ← copied from runtime/
  <RuleName>.hs         ← one per abstract rule (and lone concrete classes)
```

## Generated Rule Module (`<RuleName>.hs`)

For a rule `Exp` with concrete alternatives `AddExp { left :: Exp, right :: Exp }` and `NumExp { value :: Token }`:

```haskell
module Exp where

-- top fragments

import Data.Aeson
import qualified Data.Map.Strict as Map
import Token
-- import fragments

data Exp
    = AddExp { left :: Exp, right :: Exp }
    | NumExp { value :: Token }
    deriving (Show, Eq)

instance FromJSON Exp where
    parseJSON = withObject "Exp" $ \o -> do
        rule     <- o .: "rule"
        children <- o .: "children"   -- parsed as [(String, Value)]
        let fieldNames = sort (map fst children)
        case (rule :: String) of
            "Exp" -> case fieldNames of
                ["left", "right"] ->
                    AddExp <$> parseField children "left"
                           <*> parseField children "right"
                ["value"] ->
                    NumExp <$> parseField children "value"
                _ -> fail "unknown Exp variant"
            r -> fail $ "unexpected rule: " ++ r

-- body fragments
```

`children` is the JSON array of `[name, value]` pairs from the plcc-ng wire format. Field names are sorted before matching, mirroring the registry lookup algorithm used in the other backends. `parseField` is a generated helper — `parseField children name = ...` that finds the named entry in the pairs list and recursively calls `parseJSON` on its value.

Abstract classes (rules with no concrete fields of their own) follow the same structure but have no single-constructor shortcut.

## `Token.hs` (runtime, hand-written)

```haskell
module Token where

import Data.Aeson

data Token = Token { tokenKind :: String, lexeme :: String }
    deriving (Show, Eq)

instance FromJSON Token where
    parseJSON = withObject "Token" $ \o ->
        Token <$> o .: "name" <*> o .: "lexeme"
```

## `Main.hs` (generated)

```haskell
module Main where

import Data.Aeson
import qualified Data.ByteString.Lazy.Char8 as BL
import System.IO
import Exp     -- start rule module
-- imports for all other rule modules

main :: IO ()
main = do
    hSetBuffering stdout LineBuffering
    contents <- getContents
    mapM_ handle (filter (not . null) (lines contents))
  where
    handle line = case eitherDecode (BL.pack line) of
        Left err   ->
            BL.putStrLn $ encode $ object
                [ "kind"    .= ("error" :: String)
                , "message" .= err
                ]
        Right tree ->
            BL.putStrLn $ encode $ object
                [ "kind"  .= ("result" :: String)
                , "value" .= _run (tree :: Exp)
                ]
```

## `interpreter.cabal` (generated)

```cabal
cabal-version: 3.0
name:          interpreter
version:       0.1.0.0

executable interpreter
  main-is:          Main.hs
  other-modules:    Token, Exp, Prog
  build-depends:    base, aeson, bytestring, containers
  default-language: Haskell2010
  hs-source-dirs:   .
```

The `other-modules` list is generated from all rule modules. The `base` version bound is set to the GHC version's bundled base.

## `emit.py`

Mirrors `javascript/emit.py` in structure:

- Reads model JSON from stdin
- Creates output directory
- Copies `Token.hs` from the runtime directory
- Generates one `<RuleName>.hs` for each abstract class and each lone concrete class
- Generates `Main.hs`
- Generates `interpreter.cabal`
- Applies `file` fragments (overwrite entire module file)

## `build.py`

Runs `cabal build` in the output directory, passing stdout/stderr through. Exits with cabal's return code.

First build fetches and compiles `aeson` and its transitive dependencies from Hackage. This can take several minutes on a cold cabal store. Subsequent builds are fast due to cabal's global package store cache.

## `run.py`

Runs `cabal run interpreter` in the output directory, passing stdin/stdout/stderr through. Uses `cabal run` rather than locating the binary directly to avoid platform-specific binary path resolution. Handles `KeyboardInterrupt` with exit code 130.

Since `plcc-lang-build` always runs before `plcc-lang-run` in the pipeline, the binary is already built when `run.py` is called; `cabal run` will not trigger a rebuild.

## Devcontainer

The existing `.devcontainer/devcontainer.json` has no Haskell toolchain. The Haskell feature must be added so that `token_test.py`, the BATS command tests, and the e2e tests can run inside the container:

```json
"ghcr.io/devcontainers/features/haskell:1": {
    "ghcupDownloadUrls": "",
    "installStack": false,
    "installHLS": false
}
```

This installs GHCup, GHC, and cabal. Stack and HLS are disabled to keep the image lean. Adding this feature is a prerequisite for any test that invokes `ghc`, `cabal`, or runs the compiled interpreter.

Updating the devcontainer should be its own step in the implementation plan, done before writing tests that exercise the Haskell toolchain.

## Installation Prerequisites

Users need GHCup, which installs both GHC and cabal:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://get-ghcup.haskell.org | sh
```

No manual `aeson` installation is required — `cabal build` fetches it automatically on first use.

## Testing

### `emit_test.py`

Pytest unit tests for the emitter:

- Correct `.hs` files generated for abstract and lone-concrete rules
- `data` declaration has correct constructors and field names
- All generated types derive `Show` and `Eq`
- `FromJSON` instance generated for each rule module
- Default `_run` generated when start rule has no body fragment defining it
- No default `_run` generated when the user provides one in body fragments
- Fragment kinds placed in correct positions (`top`, `import`, `body`)
- `file` fragment replaces the entire rule module
- `interpreter.cabal` written with correct `other-modules` list and dependencies
- `Token.hs` copied to output directory

### `build_test.py`

Pytest unit tests for the builder:

- Invokes `cabal build` in the output directory
- Passes stdout/stderr through
- Exits with cabal's return code

### `run_test.py`

Pytest unit tests for the runner:

- Invokes `cabal run interpreter` in the output directory
- Passes stdin/stdout/stderr through
- Exits with the process's return code
- Exits 130 on `KeyboardInterrupt`

### `runtime/token_test.py`

Pytest tests that compile and run a small Haskell program exercising `Token.hs` via `subprocess.run`. Requires GHC and cabal on `PATH`.

Tests cover:
- `Token` stores `tokenKind` and `lexeme`
- `show` produces a readable representation
- `FromJSON` parses a token JSON object correctly
