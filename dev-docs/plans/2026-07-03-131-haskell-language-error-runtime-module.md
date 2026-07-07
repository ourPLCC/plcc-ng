# Haskell `LanguageError` Runtime Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `LanguageError` importable from Haskell user semantics modules by moving it out of the inline `Main.hs` template into a `runtime/LanguageError.hs` module, auto-imported into every generated module — mirroring the existing `Token.hs` pattern.

**Architecture:** Add `runtime/LanguageError.hs` alongside the existing `runtime/Token.hs`. Extend the Haskell emitter (`src/plcc/lang/ext/haskell/emit.py`) to copy it into every emitted project's output root, list it in the generated `.cabal` file's `other-modules`, and unconditionally `import LanguageError` (plus `Control.Exception (throw)`, since `throw` is a function, not a keyword) into every generated module — the same treatment `Token` already gets. `Main.hs` switches from defining `LanguageError` inline to importing it.

**Tech Stack:** Python 3 (emitter), Haskell (GHC 9.4+, cabal 3.0+), pytest, `aeson`/`base` packages.

## Global Constraints

- GHC 9.4+ and cabal 3.0+ (existing project requirement — see `docs/language-guide/languages/haskell.md` Prerequisites).
- `interpreter.cabal`'s `build-depends` stays `base, aeson, bytestring, text` — no new dependency; `Control.Exception` and the `Exception` typeclass are part of `base`.
- Follow `Token.hs`'s existing idiom: runtime files are copied flat into the output root (`output_dir/LanguageError.hs`), **not** into an `output_dir/runtime/` subdirectory (unlike Python/Java/JS, which copy the whole `runtime/` tree).
- No new bats/e2e *behavioral* test file is added for `LanguageError` — none of the other three languages have one either; unit-level coverage is the established bar for that. However, per project convention (emitter output changes get bats coverage), the *existing* bats assertions that check individual emitted files must be extended with a `LanguageError.hs` existence check, alongside their existing `Token.hs` check: `tests/bats/commands/plcc-haskell-emit.bats` and `tests/bats/e2e/haskell.bats`. `tests/bats/e2e/haskell_roundtrip.bats` must still pass unmodified.
- Generated output files are always fully overwritten on every emit run — do not special-case `LanguageError.hs`.

---

### Task 1: Add `runtime/LanguageError.hs` and copy it into emitted output

**Files:**
- Create: `src/plcc/lang/ext/haskell/runtime/LanguageError.hs`
- Modify: `src/plcc/lang/ext/haskell/emit.py:43-47,159-161` (the `emit()` function and `_copy_token`)
- Test: `src/plcc/lang/ext/haskell/emit_test.py`, `tests/bats/commands/plcc-haskell-emit.bats`, `tests/bats/e2e/haskell.bats`

**Interfaces:**
- Produces: `runtime/LanguageError.hs` containing `newtype LanguageError = LanguageError String deriving Show` and `instance Exception LanguageError`. `_copy_runtime_files(output_dir)` replaces `_copy_token(output_dir)` and copies both `Token.hs` and `LanguageError.hs` into `output_dir`.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/haskell/emit_test.py`, directly after `test_token_hs_contains_token_module` (currently ending at line 75):

```python
def test_emit_copies_language_error_hs(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'LanguageError.hs').exists()


def test_language_error_hs_contains_module(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'LanguageError.hs').read_text()
    assert 'module LanguageError' in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py -k language_error_hs`
Expected: FAIL — `FileNotFoundError` or assertion failure, since `LanguageError.hs` is never written.

- [ ] **Step 3: Create the runtime module**

Create `src/plcc/lang/ext/haskell/runtime/LanguageError.hs`:

```haskell
module LanguageError where

import Control.Exception (Exception)

newtype LanguageError = LanguageError String deriving Show

instance Exception LanguageError
```

- [ ] **Step 4: Wire the copy into the emitter**

In `src/plcc/lang/ext/haskell/emit.py`, replace the `_copy_token` function (lines 159-161):

```python
def _copy_token(output_dir):
    src = Path(__file__).parent / 'runtime' / 'Token.hs'
    shutil.copy(src, output_dir / 'Token.hs')
```

with:

```python
def _copy_runtime_files(output_dir):
    for name in ('Token.hs', 'LanguageError.hs'):
        src = Path(__file__).parent / 'runtime' / name
        shutil.copy(src, output_dir / name)
```

Then update the call site in `emit()` (line 47):

```python
    _copy_token(output_dir)
```

becomes:

```python
    _copy_runtime_files(output_dir)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py -v`
Expected: PASS — all tests in the file, including the two new ones and the pre-existing `test_emit_copies_token_hs` / `test_token_hs_contains_token_module` (must still pass unchanged).

- [ ] **Step 5b: Extend the bats command and e2e tests to cover the new emitted file**

Per project convention, emitter output changes get bats coverage alongside the pytest unit tests. Add a `LanguageError.hs` existence check next to the existing `Token.hs` check in both files.

In `tests/bats/commands/plcc-haskell-emit.bats`, add directly after the `"plcc-haskell-emit: emits Token.hs given minimal model"` test (lines 26-33):

```bash
@test "plcc-haskell-emit: emits LanguageError.hs given minimal model" {
    local out
    out=$(mktemp -d)
    echo '{"start":"prog","classes":[{"name":"Prog","extends":null,"abstract":false,"rule_name":"prog","fields":[]}],"semantic_sections":[]}' \
        | plcc-haskell-emit --output="$out"
    [ -f "$out/LanguageError.hs" ]
    rm -rf "$out"
}
```

In `tests/bats/e2e/haskell.bats`, in the `"haskell pipeline: spec to model to emit produces expected files"` test, add a line next to the existing `[ -f "$OUT_DIR/Token.hs" ]` assertion:

```bash
    [ -f "$OUT_DIR/interpreter.cabal" ]
    [ -f "$OUT_DIR/Token.hs" ]
    [ -f "$OUT_DIR/LanguageError.hs" ]
    [ -f "$OUT_DIR/Main.hs" ]
    [ -f "$OUT_DIR/Program.hs" ]
```

Run: `bin/test/commands.bash` and `bin/test/e2e.bash` (or, if `bats` is not directly runnable in this environment, run `bin/install/bats.bash` first).
Expected: PASS — both new assertions pass alongside all pre-existing bats assertions in these two files.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/haskell/runtime/LanguageError.hs src/plcc/lang/ext/haskell/emit.py src/plcc/lang/ext/haskell/emit_test.py tests/bats/commands/plcc-haskell-emit.bats tests/bats/e2e/haskell.bats
git commit -m "feat(haskell): add runtime/LanguageError.hs and copy it into emitted output"
```

---

### Task 2: Move `LanguageError`'s definition out of inline `Main.hs`, import it instead

**Files:**
- Modify: `src/plcc/lang/ext/haskell/emit.py:62-112` (`_write_main`), `:142-156` (`_write_cabal`)
- Test: `src/plcc/lang/ext/haskell/emit_test.py`

**Interfaces:**
- Consumes: `runtime/LanguageError.hs` module produced in Task 1 (must already be copied into `output_dir` by the time `Main.hs` is written — `emit()` already calls `_copy_runtime_files` before `_write_main`, so ordering is correct).
- Produces: `Main.hs` that `import LanguageError` instead of defining it inline; `interpreter.cabal`'s `other-modules` list includes `LanguageError`.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/haskell/emit_test.py`, directly after `test_write_main_contains_language_error` (currently at lines 305-309):

```python
def test_write_main_imports_language_error_module(tmp_path):
    from .emit import _write_main
    _write_main("Program", {}, tmp_path)
    main_hs = (tmp_path / 'Main.hs').read_text()
    assert 'import LanguageError' in main_hs


def test_write_main_does_not_define_language_error_inline(tmp_path):
    from .emit import _write_main
    _write_main("Program", {}, tmp_path)
    main_hs = (tmp_path / 'Main.hs').read_text()
    assert 'newtype LanguageError' not in main_hs
```

Add to `src/plcc/lang/ext/haskell/emit_test.py`, directly after `test_cabal_file_lists_token_module` (currently at lines 61-64):

```python
def test_cabal_file_lists_language_error_module(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'interpreter.cabal').read_text()
    assert 'LanguageError' in text.split('other-modules:')[1].splitlines()[0]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py -k "imports_language_error_module or does_not_define_language_error_inline or cabal_file_lists_language_error_module"`
Expected: FAIL — `test_write_main_imports_language_error_module` and `test_cabal_file_lists_language_error_module` fail (no import / not in `other-modules` yet); `test_write_main_does_not_define_language_error_inline` fails (inline `newtype` is still there).

- [ ] **Step 3: Update `_write_main`**

In `src/plcc/lang/ext/haskell/emit.py`, replace the `_write_main` function (lines 62-112) with:

```python
def _write_main(start_module, modules, output_dir):
    import_lines = '\n'.join(f'import {name}' for name in sorted(modules))
    content = (
        '{-# LANGUAGE OverloadedStrings, ScopedTypeVariables #-}\n'
        'module Main where\n'
        '\n'
        'import Control.Exception (SomeException, catch, evaluate)\n'
        'import Data.Aeson (eitherDecode, encode, object, (.=))\n'
        'import qualified Data.ByteString.Lazy.Char8 as BL\n'
        'import System.IO (hSetBuffering, stdout, BufferMode (..))\n'
        'import LanguageError\n'
        f'{import_lines}\n'
        '\n'
        'main :: IO ()\n'
        'main = do\n'
        '    hSetBuffering stdout LineBuffering\n'
        '    BL.putStrLn $ encode $ object ["kind" .= ("ready" :: String)]\n'
        '    contents <- getContents\n'
        '    mapM_ handle (filter (not . null) (lines contents))\n'
        '  where\n'
        '    handle line = case eitherDecode (BL.pack line) of\n'
        '        Left err ->\n'
        '            BL.putStrLn $ encode $ object\n'
        '                [ "kind" .= ("specification_error" :: String)\n'
        '                , "type" .= ("ParseError" :: String)\n'
        '                , "message" .= err\n'
        '                ]\n'
        '        Right tree -> do\n'
        f'            let val = _run (tree :: {start_module})\n'
        '            result <- (evaluate val >>= \\v ->\n'
        '                return (encode $ object\n'
        '                    [ "kind" .= ("result" :: String)\n'
        '                    , "value" .= v\n'
        '                    ]))\n'
        '                `catch` (\\(LanguageError msg) ->\n'
        '                    return (encode $ object\n'
        '                        [ "kind" .= ("error" :: String)\n'
        '                        , "type" .= ("LanguageError" :: String)\n'
        '                        , "message" .= msg\n'
        '                        ]))\n'
        '                `catch` (\\(e :: SomeException) ->\n'
        '                    return (encode $ object\n'
        '                        [ "kind" .= ("specification_error" :: String)\n'
        '                        , "type" .= show e\n'
        '                        , "message" .= show e\n'
        '                        ]))\n'
        '            BL.putStrLn result\n'
    )
    (output_dir / 'Main.hs').write_text(content)
```

Note the two changes from the original: `Control.Exception (Exception, SomeException, catch, evaluate)` drops `Exception` (only needed for the `instance Exception LanguageError` declaration, which moved to `LanguageError.hs`), and a new `import LanguageError` line replaces the deleted `newtype LanguageError = LanguageError String deriving Show` / `instance Exception LanguageError` lines.

- [ ] **Step 4: Update `_write_cabal`**

In `src/plcc/lang/ext/haskell/emit.py`, change line 143:

```python
    module_list = ', '.join(['Token'] + sorted(modules))
```

to:

```python
    module_list = ', '.join(['Token', 'LanguageError'] + sorted(modules))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py -v`
Expected: PASS — all tests, including `test_write_main_contains_language_error` (still true: the `catch` handler still pattern-matches `\(LanguageError msg) -> ...`), the three new tests, and every pre-existing test in the file.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/haskell/emit.py src/plcc/lang/ext/haskell/emit_test.py
git commit -m "feat(haskell): import LanguageError from runtime module instead of defining it inline in Main.hs"
```

---

### Task 3: Auto-import `LanguageError` and `throw` into every generated user module

**Files:**
- Modify: `src/plcc/lang/ext/haskell/emit.py:175-201` (`_render_module`)
- Test: `src/plcc/lang/ext/haskell/emit_test.py`

**Interfaces:**
- Produces: every generated `.hs` module (e.g. `Prog.hs`, `Expr.hs`) unconditionally contains `import LanguageError` and `import Control.Exception (throw)`, so user semantics code can write `throw (LanguageError "message")` without any `:import` fragment.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/haskell/emit_test.py`, directly after `test_concrete_constructor_has_token_field` (currently at lines 95-98):

```python
def test_generated_module_imports_language_error(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'import LanguageError' in text


def test_generated_module_imports_throw(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'import Control.Exception (throw)' in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py -k "generated_module_imports"`
Expected: FAIL — neither import line is present in `Expr.hs` yet.

- [ ] **Step 3: Update `_render_module`**

In `src/plcc/lang/ext/haskell/emit.py`, in `_render_module` (around line 187-189), change:

```python
    lines.append('import Data.Aeson (FromJSON (..), Value (..), withObject, (.:))')
    lines.append('import Data.List (sort)')
    lines.append('import Token')
```

to:

```python
    lines.append('import Data.Aeson (FromJSON (..), Value (..), withObject, (.:))')
    lines.append('import Data.List (sort)')
    lines.append('import Token')
    lines.append('import LanguageError')
    lines.append('import Control.Exception (throw)')
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py -v`
Expected: PASS — all tests in the file.

- [ ] **Step 5: Run the full unit suite**

Run: `bin/test/units.bash`
Expected: PASS — no regressions anywhere else in the codebase (this change only touches the Haskell emitter).

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/haskell/emit.py src/plcc/lang/ext/haskell/emit_test.py
git commit -m "feat(haskell): auto-import LanguageError and throw into every generated module"
```

---

### Task 4: Cross-module build+run test proving `LanguageError` is genuinely usable

**Files:**
- Create: `src/plcc/lang/ext/haskell/runtime/language_error_test.py`

**Interfaces:**
- Consumes: `src/plcc/lang/ext/haskell/runtime/LanguageError.hs` (from Task 1) — this test copies that literal file into a throwaway cabal project, so it will catch any regression in Task 1-3's changes to that file's content or the `throw`/`import LanguageError` usage pattern documented in Task 3.

This test mirrors `runtime/token_test.py`'s `_build_and_run` pattern exactly, but with two modules (`Lib.hs` + `Main.hs`) to prove `LanguageError` is importable and catchable *across* module boundaries — not just present as a string in a template, which is all the Task 1-3 unit tests check.

- [ ] **Step 1: Write the test file**

Create `src/plcc/lang/ext/haskell/runtime/language_error_test.py`:

```python
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

LANGUAGE_ERROR_HS = Path(__file__).parent / 'LanguageError.hs'

def _hackage_available():
    if not shutil.which('cabal'):
        return False
    for base in [Path.home() / '.cabal', Path.home() / '.local' / 'state' / 'cabal']:
        if (base / 'packages' / 'hackage.haskell.org').exists():
            return True
    return False

_skip_no_hackage = pytest.mark.skipif(
    not _hackage_available(),
    reason="requires cabal with hackage package list (run 'cabal update')",
)


def _build_and_run(tmp_path, lib_hs, main_hs):
    """Compile a minimal cabal project containing LanguageError.hs plus a
    second module, and run it."""
    (tmp_path / 'LanguageError.hs').write_text(LANGUAGE_ERROR_HS.read_text())
    (tmp_path / 'Lib.hs').write_text(lib_hs)
    (tmp_path / 'Main.hs').write_text(main_hs)
    (tmp_path / 'test-language-error.cabal').write_text(textwrap.dedent("""\
        cabal-version: 3.0
        name:          test-language-error
        version:       0.1.0.0
        executable     test-language-error
          main-is:          Main.hs
          other-modules:    LanguageError, Lib
          build-depends:    base
          default-language: Haskell2010
          hs-source-dirs:   .
    """))
    subprocess.run(['cabal', 'build'], cwd=tmp_path, check=True, capture_output=True)
    result = subprocess.run(
        ['cabal', 'run', 'test-language-error'],
        cwd=tmp_path, capture_output=True, text=True, input=''
    )
    return result.stdout.strip()


@_skip_no_hackage
def test_language_error_thrown_in_one_module_caught_in_another(tmp_path):
    output = _build_and_run(
        tmp_path,
        lib_hs=textwrap.dedent("""\
            module Lib where
            import Control.Exception (throw)
            import LanguageError

            explode :: Int
            explode = throw (LanguageError "boom")
        """),
        main_hs=textwrap.dedent("""\
            module Main where
            import Control.Exception (catch, evaluate)
            import LanguageError
            import Lib (explode)

            main :: IO ()
            main = (evaluate explode >> return ())
                `catch` (\\(LanguageError msg) -> putStrLn msg)
        """),
    )
    assert output == "boom"
```

- [ ] **Step 2: Run the test**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/runtime/language_error_test.py -v`
Expected: PASS if `cabal` with a Hackage package index is available locally (same precondition as `runtime/token_test.py`); otherwise SKIPPED with reason `"requires cabal with hackage package list (run 'cabal update')"`. Either outcome is acceptable — do not treat a skip as a failure.

- [ ] **Step 3: Commit**

```bash
git add src/plcc/lang/ext/haskell/runtime/language_error_test.py
git commit -m "test(haskell): verify LanguageError is throwable/catchable across module boundaries"
```

---

### Task 5: Update the Haskell language-guide doc

**Files:**
- Modify: `docs/language-guide/languages/haskell.md:131-137` (the `## LanguageError` section), `:150-161` (the "Generated output" file listing)

**Interfaces:**
- Consumes: the final behavior from Tasks 1-3 — `LanguageError` and `throw` are both in scope in every generated module without an import fragment.

- [ ] **Step 1: Rewrite the `## LanguageError` section**

In `docs/language-guide/languages/haskell.md`, replace lines 131-137:

```markdown
## `LanguageError`

`LanguageError` is the intended mechanism for signaling a deliberate error in the defined language from Haskell semantics code. When thrown, `plcc-rep` prints the message and gives a fresh prompt; the session continues.

`LanguageError` is currently not accessible from user-authored module files — it is defined in the generated `Main.hs`, which user modules cannot import. Support for throwing `LanguageError` from semantics code is tracked in issues 131 and 132.

In the meantime, note that Haskell's built-in `error "message"` throws `ErrorCall`, which is treated as a **specification error** (not a language error) — `plcc-rep` will exit.
```

with:

`````markdown
## `LanguageError`

Throw `LanguageError` to signal a deliberate error in the defined language — a type mismatch, division by zero, or any condition your language treats as an error. `plcc-rep` prints the message and gives a fresh prompt; the session continues.

`LanguageError` and `throw` are both available in every generated module without any import:

```haskell
eval :: Exp -> Int
eval (DivExp l r)
    | evalR == 0 = throw (LanguageError "division by zero")
    | otherwise  = evalL `div` evalR
  where
    evalL = eval l
    evalR = eval r
```

Unlike Python, Java, and JavaScript, Haskell has no subclassing, so there is no equivalent to defining named error types — `LanguageError "message"` (distinguished by its message string) is the only form.

Haskell's built-in `error "message"` throws `ErrorCall`, which is treated as a **specification error** (not a language error) — `plcc-rep` will exit.
`````

- [ ] **Step 2: Update the "Generated output" file listing**

In `docs/language-guide/languages/haskell.md`, in the "Generated output" section, replace:

```
DIR/
  interpreter.cabal   — cabal project file; lists all modules
  Token.hs            — runtime Token type with lexeme field
  Main.hs             — entry point; deserializes parse tree JSON, calls _run
  Prog.hs             — one .hs per lone concrete rule
  Exp.hs              — one .hs per abstract rule (contains all alternatives as constructors)
```

with:

```
DIR/
  interpreter.cabal   — cabal project file; lists all modules
  Token.hs            — runtime Token type with lexeme field
  LanguageError.hs    — runtime LanguageError type for signaling language errors
  Main.hs             — entry point; deserializes parse tree JSON, calls _run
  Prog.hs             — one .hs per lone concrete rule
  Exp.hs              — one .hs per abstract rule (contains all alternatives as constructors)
```

- [ ] **Step 3: Proofread the rendered page**

Run: `grep -n "LanguageError\|issues 131 and 132" docs/language-guide/languages/haskell.md`
Expected: no remaining reference to "not currently accessible" or "issues 131 and 132"; `LanguageError.hs` appears in the file listing.

- [ ] **Step 4: Commit**

```bash
git add docs/language-guide/languages/haskell.md
git commit -m "docs(haskell): document LanguageError now that it's importable from user code"
```

---

### Task 6: Full verification sweep

**Files:** none (verification only)

- [ ] **Step 1: Run the full unit suite**

Run: `bin/test/units.bash`
Expected: PASS, same total count as baseline plus the 9 new tests added across Tasks 1-3 (2 + 3 + 2 in emit_test.py = 7, plus `language_error_test.py`'s 1 test — 8 new, either passing or cleanly skipped for the cabal-dependent one).

- [ ] **Step 2: Run the Haskell roundtrip e2e test**

Run: `bin/test/e2e_haskell_roundtrip.bash`
Expected: PASS (or SKIP if `cabal` is unavailable in this environment) — confirms the emitter still produces a working end-to-end interpreter after the `Main.hs` and `_render_module` changes in Tasks 2-3.

- [ ] **Step 3: Run the full functional suite**

Run: `bin/test/functional.bash`
Expected: PASS — confirms no regressions in commands, integration, or e2e tiers outside Haskell.

No commit for this task — it's verification only. If any step fails, return to the relevant task above and fix it before considering the plan complete.
