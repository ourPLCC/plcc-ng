# Design: Move Haskell `LanguageError` Into a Runtime Module

**Date:** 2026-07-03
**Issue:** 131
**Status:** Approved

## Problem

`LanguageError` is defined inline in generated `Main.hs` (`src/plcc/lang/ext/haskell/emit.py:74-75`):

```haskell
newtype LanguageError = LanguageError String deriving Show
instance Exception LanguageError
```

Because it's declared inside `Main.hs` itself, no user-authored module (`Prog.hs`, `Exp.hs`, etc.) can import it. The other three languages (Python, Java, JavaScript) provide `LanguageError` via an importable `runtime/` module.

## Scope

Haskell emitter only (`src/plcc/lang/ext/haskell/`). Also finishes Haskell's part of issue 132 ("`LanguageError` in scope by default"), which was explicitly deferred pending this issue — see `dev-docs/issues/done/132-language-error-in-scope-by-default.md`.

## Approach: Mirror the existing `Token.hs` pattern

Haskell already has a working precedent for exactly this: `runtime/Token.hs` is copied into the output root and unconditionally imported into every generated module (`emit.py:189`, `import Token`). `LanguageError` gets the identical treatment — same file-copy idiom, same unconditional import — so it is importable everywhere with no fragment required, closing the gap issue 132 left open for Haskell.

This was chosen over requiring an explicit user `import` fragment (matching the pre-132 behavior of the other languages) because the auto-import machinery already exists for `Token` and costs nothing extra to extend.

## Changes

### New file: `src/plcc/lang/ext/haskell/runtime/LanguageError.hs`

```haskell
module LanguageError where

import Control.Exception (Exception)

newtype LanguageError = LanguageError String deriving Show

instance Exception LanguageError
```

### `src/plcc/lang/ext/haskell/emit.py`

- Replace `_copy_token(output_dir)` with `_copy_runtime_files(output_dir)`, which copies both `Token.hs` and `LanguageError.hs` from `runtime/` into the output root (one loop instead of two near-duplicate functions).
- `_write_main`: remove the inline `newtype LanguageError ...` / `instance Exception LanguageError` lines. Add a hardcoded `import LanguageError` to `Main.hs`'s import block (alongside `Control.Exception`, `Data.Aeson`, etc.) since `Main.hs`'s `catch` handler still pattern-matches on `LanguageError`.
- `_write_cabal`: `module_list` becomes `', '.join(['Token', 'LanguageError'] + sorted(modules))`.
- `_render_module`: add `lines.append('import LanguageError')` next to the existing `lines.append('import Token')` (`emit.py:189`), so every generated user module gets it automatically. Also add `lines.append('import Control.Exception (throw)')` — `LanguageError` is only useful if user code can also call `throw`, and `throw` is a plain function from `Control.Exception` (part of `base`, already a build-depends), not a keyword, so it needs the same auto-import treatment. Usage becomes `throw (LanguageError "message")`, directly analogous to Python's `raise LanguageError(...)` and Java's `throw new LanguageError(...)`.

## What Does Not Change

- `Token.hs` content or its role as the copy/import idiom being generalized
- Python, Java, JavaScript emitters
- cabal `build-depends` (`base` already provides `Control.Exception`)

## Testing

- `runtime/language_error_test.py` (new, mirrors `runtime/token_test.py`'s `_build_and_run` pattern): a minimal two-module cabal project where one module throws `LanguageError` and `Main` catches it, proving it compiles and is catchable across module boundaries — not just present as a string. Skipped without `cabal`/Hackage cache, same skip condition as the Token test.
- `emit_test.py`:
  - Update `test_write_main_contains_language_error` to assert `import LanguageError` appears in `Main.hs` (replacing the old inline-`newtype` assertion).
  - Assert `LanguageError.hs` is copied into the emitted output directory.
  - Assert a rendered module (`_render_module` output) contains `import LanguageError` and `import Control.Exception (throw)`.
  - Assert the cabal `other-modules` list includes `LanguageError`.

No bats/e2e test is added — none of the other three languages have a `LanguageError` bats/e2e test either; unit-level coverage plus the existing `haskell_roundtrip.bats` (unaffected) is the established bar.

## Documentation

`docs/language-guide/languages/haskell.md`:

- Rewrite the `## LanguageError` section (lines 131-137): drop the "not currently accessible" caveat, add a `throw (LanguageError "message")` usage example (both `LanguageError` and `throw` are in scope without an import fragment), and note that Haskell has no subclassing — unlike the other three languages' "named error type via subclass" convention, `LanguageError "msg"` (with a distinguishing message) is the only form available.
- Add `LanguageError.hs` to the generated-output file listing (~lines 150-161).
