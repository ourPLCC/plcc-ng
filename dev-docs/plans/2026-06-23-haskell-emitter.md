# Haskell Emitter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Haskell language backend to plcc-ng that emits ADT-based Haskell source from model JSON, compiles it with cabal, and runs it via `cabal run`.

**Architecture:** One Haskell module per grammar rule (abstract class + its concrete alternatives as constructors). `aeson` handles JSON deserialization via generated `FromJSON` instances. Follows the Java three-command pattern: `plcc-haskell-emit`, `plcc-haskell-build`, `plcc-haskell-run`.

**Tech Stack:** Python (emit/build/run commands), GHC + cabal (compilation), aeson + bytestring + containers (Haskell deps)

## Global Constraints

- TDD inner loop: write failing test → `bin/test/units.bash` → implement → `bin/test/units.bash` → commit
- All generated types derive `Show` and `Eq`
- Entry point function: `_run :: StartType -> String`
- Haskell field type mapping: `field['type'] == 'Token'` → `Token`; any other string → that string verbatim; `field['is_list'] == True` → wrap in `[...]`
- cabal project name and executable name: `interpreter`
- Spec section tag: `haskell` (lowercase), matches `s.get('language', '').lower() == 'haskell'`
- Commit prefix: `feat(haskell):` or `test(haskell):`
- All commits to `issue-haskell` branch in `.worktrees/issue-haskell/`

---

## File Map

| File | Created/Modified | Purpose |
|------|-----------------|---------|
| `.devcontainer/devcontainer.json` | Modify | Add GHC + cabal via Haskell devcontainer feature |
| `src/plcc/lang/ext/haskell/__init__.py` | Create | Package marker |
| `src/plcc/lang/ext/haskell/emit.py` | Create | Emitter: reads model JSON, writes Haskell source files |
| `src/plcc/lang/ext/haskell/emit_test.py` | Create | Unit tests for emitter |
| `src/plcc/lang/ext/haskell/build.py` | Create | Runner: invokes `cabal build` in output dir |
| `src/plcc/lang/ext/haskell/build_test.py` | Create | Unit tests for builder |
| `src/plcc/lang/ext/haskell/run.py` | Create | Runner: invokes `cabal run interpreter` in output dir |
| `src/plcc/lang/ext/haskell/run_test.py` | Create | Unit tests for runner |
| `src/plcc/lang/ext/haskell/runtime/Token.hs` | Create | Hand-written runtime: Token type, parseField, parseChildren helpers |
| `src/plcc/lang/ext/haskell/runtime/token_test.py` | Create | Tests for Token.hs via subprocess (requires cabal) |
| `pyproject.toml` | Modify | Add three entry points for emit/build/run |
| `tests/bats/commands/plcc-haskell-emit.bats` | Create | Black-box CLI test for the emit command |
| `tests/bats/e2e/haskell.bats` | Create | End-to-end pipeline test for Haskell |

---

### Task 1: Add Haskell to devcontainer

**Files:**
- Modify: `.devcontainer/devcontainer.json`

- [ ] **Step 1: Add the Haskell devcontainer feature**

In `.devcontainer/devcontainer.json`, add to the `"features"` object:

```json
"ghcr.io/devcontainers/features/haskell:1": {
    "installStack": false,
    "installHLS": false
}
```

The full `features` block should look like:

```json
"features": {
    "ghcr.io/devcontainers/features/python:1": {},
    "ghcr.io/devcontainers/features/java:1": { "version": "17" },
    "ghcr.io/devcontainers-extra/features/pdm:2": {},
    "ghcr.io/anthropics/devcontainer-features/claude-code:1.0": {},
    "ghcr.io/devcontainers/features/haskell:1": {
        "installStack": false,
        "installHLS": false
    }
}
```

- [ ] **Step 2: Rebuild the devcontainer**

VS Code Command Palette → "Dev Containers: Rebuild Container". Wait for it to finish.

- [ ] **Step 3: Verify the toolchain**

```bash
ghc --version
cabal --version
```

Expected:
```
The Glorious Glasgow Haskell Compilation System, version 9.x.x
cabal-install version 3.x.x
```

- [ ] **Step 4: Commit**

```bash
git add .devcontainer/devcontainer.json
git commit -m "feat(haskell): add GHC and cabal to devcontainer"
```

---

### Task 2: Extension skeleton and entry points

**Files:**
- Create: `src/plcc/lang/ext/haskell/__init__.py`
- Create: `src/plcc/lang/ext/haskell/emit.py`
- Create: `src/plcc/lang/ext/haskell/build.py`
- Create: `src/plcc/lang/ext/haskell/run.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `emit(model, output_dir)` function consumed by Tasks 4–9
- Produces: `plcc-haskell-emit`, `plcc-haskell-build`, `plcc-haskell-run` entry points

- [ ] **Step 1: Write the failing test**

Create `src/plcc/lang/ext/haskell/emit_test.py`:

```python
from plcc.lang.ext.haskell.emit import main as run_main
```

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'plcc.lang.ext.haskell'`

- [ ] **Step 2: Create `src/plcc/lang/ext/haskell/__init__.py`**

Empty file — just the package marker.

- [ ] **Step 3: Create `src/plcc/lang/ext/haskell/emit.py`**

```python
"""plcc-haskell-emit
    Emit a Haskell interpreter from model JSON.

Usage:
    plcc-haskell-emit --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
"""

import enum
import json
import shutil
import sys
from pathlib import Path

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-haskell-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')
    model = json.load(sys.stdin)
    emit(model, output_dir)
    verbose.emit(Events.FINISHED, message='done')


def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Create `src/plcc/lang/ext/haskell/build.py`**

```python
"""plcc-haskell-build
    Build a generated Haskell interpreter with cabal.

Usage:
    plcc-haskell-build --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory containing generated Haskell files.
    -h --help       Show this message.
"""

import enum
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-haskell-build", Events, args)
    output_dir = args['--output']
    verbose.emit(Events.STARTED, message=f'building in {output_dir}')
    result = subprocess.run(
        ['cabal', 'build'],
        cwd=output_dir,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    verbose.emit(Events.FINISHED, message=f'exit {result.returncode}')
    sys.exit(result.returncode)
```

- [ ] **Step 5: Create `src/plcc/lang/ext/haskell/run.py`**

```python
"""plcc-haskell-run
    Run a generated Haskell interpreter.

Usage:
    plcc-haskell-run --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory containing generated Haskell files.
    -h --help       Show this message.
"""

import enum
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-haskell-run", Events, args)
    output_dir = args['--output']
    verbose.emit(Events.STARTED, message=f'running in {output_dir}')
    try:
        result = subprocess.run(
            ['cabal', 'run', 'interpreter'],
            cwd=output_dir,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    except KeyboardInterrupt:
        sys.exit(130)
    verbose.emit(Events.FINISHED, message=f'exit {result.returncode}')
    sys.exit(result.returncode)
```

- [ ] **Step 6: Add entry points to `pyproject.toml`**

After the `plcc-javascript-run` line, add:

```toml
plcc-haskell-emit  = "plcc.lang.ext.haskell.emit:main"
plcc-haskell-build = "plcc.lang.ext.haskell.build:main"
plcc-haskell-run   = "plcc.lang.ext.haskell.run:main"
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: `1 passed`

- [ ] **Step 8: Commit**

```bash
git add src/plcc/lang/ext/haskell/ pyproject.toml
git commit -m "feat(haskell): add extension skeleton and entry points"
```

---

### Task 3: Token.hs runtime

**Files:**
- Create: `src/plcc/lang/ext/haskell/runtime/Token.hs`
- Create: `src/plcc/lang/ext/haskell/runtime/__init__.py`
- Create: `src/plcc/lang/ext/haskell/runtime/token_test.py`

**Interfaces:**
- Produces: `Token.hs` — imported by all generated modules; exports `Token`, `parseField`, `parseChildren`

- [ ] **Step 1: Create `src/plcc/lang/ext/haskell/runtime/__init__.py`**

Empty file.

- [ ] **Step 2: Write the failing test**

Create `src/plcc/lang/ext/haskell/runtime/token_test.py`:

```python
import subprocess
import textwrap
from pathlib import Path

import pytest

TOKEN_HS = Path(__file__).parent / 'Token.hs'


def _build_and_run(tmp_path, main_hs):
    """Compile a minimal cabal project containing Token.hs and run it."""
    (tmp_path / 'Token.hs').write_text(TOKEN_HS.read_text())
    (tmp_path / 'Main.hs').write_text(main_hs)
    (tmp_path / 'test-token.cabal').write_text(textwrap.dedent("""\
        cabal-version: 3.0
        name:          test-token
        version:       0.1.0.0
        executable     test-token
          main-is:          Main.hs
          other-modules:    Token
          build-depends:    base, aeson, text
          default-language: Haskell2010
          hs-source-dirs:   .
    """))
    subprocess.run(['cabal', 'build'], cwd=tmp_path, check=True, capture_output=True)
    result = subprocess.run(
        ['cabal', 'run', 'test-token'],
        cwd=tmp_path, capture_output=True, text=True, input=''
    )
    return result.stdout.strip()


def test_token_parses_kind_and_lexeme(tmp_path):
    output = _build_and_run(tmp_path, textwrap.dedent("""\
        module Main where
        import Data.Aeson (decode)
        import qualified Data.ByteString.Lazy.Char8 as BL
        import Token

        main :: IO ()
        main = do
            let Just tok = decode (BL.pack "{\\"name\\":\\"INT\\",\\"lexeme\\":\\"42\\"}") :: Maybe Token
            putStrLn (tokenKind tok)
            putStrLn (lexeme tok)
    """))
    assert output == "INT\n42"


def test_token_show(tmp_path):
    output = _build_and_run(tmp_path, textwrap.dedent("""\
        module Main where
        import Data.Aeson (decode)
        import qualified Data.ByteString.Lazy.Char8 as BL
        import Token

        main :: IO ()
        main = do
            let Just tok = decode (BL.pack "{\\"name\\":\\"INT\\",\\"lexeme\\":\\"42\\"}") :: Maybe Token
            print tok
    """))
    assert 'INT' in output
    assert '42' in output
```

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/runtime/token_test.py`
Expected: FAIL with `FileNotFoundError` (Token.hs doesn't exist yet)

- [ ] **Step 3: Create `src/plcc/lang/ext/haskell/runtime/Token.hs`**

```haskell
module Token where

import Data.Aeson (FromJSON (..), Value (..), withObject, (.:))
import Data.Aeson.Types (Parser)
import Data.Text (unpack)

data Token = Token { tokenKind :: String, lexeme :: String }
    deriving (Show, Eq)

instance FromJSON Token where
    parseJSON = withObject "Token" $ \o ->
        Token <$> o .: "name" <*> o .: "lexeme"

-- | Parse the plcc-ng wire format children array into name-value pairs.
-- children JSON: [["fieldname", value], ...]
parseChildren :: [[Value]] -> [(String, Value)]
parseChildren raw =
    [(unpack k, v) | [String k, v] <- raw]

-- | Look up a named child and parse it.
parseField :: FromJSON a => [(String, Value)] -> String -> Parser a
parseField pairs name =
    case lookup name pairs of
        Nothing -> fail ("missing field: " ++ name)
        Just v  -> parseJSON v
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/runtime/token_test.py`
Expected: Both tests pass. (First run will be slow — cabal fetches aeson on a cold store.)

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/ext/haskell/runtime/
git commit -m "feat(haskell): add Token.hs runtime with parseField helper"
```

---

### Task 4: emit.py — cabal file and Token.hs copy

**Files:**
- Modify: `src/plcc/lang/ext/haskell/emit.py`
- Modify: `src/plcc/lang/ext/haskell/emit_test.py`

**Interfaces:**
- Consumes: `emit(model, output_dir)` from Task 2
- Produces: `interpreter.cabal` in output dir; `Token.hs` copied to output dir

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/haskell/emit_test.py`:

```python
import io
import json

import pytest

from .emit import main as run_main


def _run_emit(monkeypatch, tmp_path, model):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])


def _minimal_model():
    return {
        "start": "prog",
        "classes": [
            {
                "name": "Prog",
                "extends": None,
                "abstract": False,
                "rule_name": "prog",
                "fields": [{"name": "expr", "type": "Expr", "is_list": False}],
            },
            {
                "name": "Expr",
                "extends": None,
                "abstract": True,
                "rule_name": "expr",
                "fields": [],
            },
            {
                "name": "NumExpr",
                "extends": "Expr",
                "abstract": False,
                "rule_name": "expr",
                "fields": [{"name": "num", "type": "Token", "is_list": False}],
            },
        ],
        "semantic_sections": [],
    }


def test_emit_writes_cabal_file(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'interpreter.cabal').exists()


def test_cabal_file_contains_executable(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'interpreter.cabal').read_text()
    assert 'executable interpreter' in text


def test_cabal_file_contains_aeson_dep(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'interpreter.cabal').read_text()
    assert 'aeson' in text


def test_cabal_file_lists_token_module(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'interpreter.cabal').read_text()
    assert 'Token' in text


def test_emit_copies_token_hs(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'Token.hs').exists()


def test_token_hs_contains_token_module(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Token.hs').read_text()
    assert 'module Token' in text
```

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: 6 FAILs (cabal file not written, Token.hs not copied)

- [ ] **Step 2: Implement cabal file writing and Token.hs copy**

Replace the `emit` function and add helpers in `src/plcc/lang/ext/haskell/emit.py`:

```python
def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    modules = _group_modules(model['classes'])
    _write_cabal(modules, output_dir)
    _copy_token(output_dir)


def _group_modules(classes):
    """Return dict mapping module_name -> module_info.

    module_info for an abstract rule:
        {'kind': 'abstract', 'abstract': cls_dict, 'concretes': [cls_dict, ...]}
    module_info for a lone concrete class (no abstract parent):
        {'kind': 'concrete', 'cls': cls_dict}
    """
    modules = {}
    for cls in classes:
        if cls['abstract']:
            modules[cls['name']] = {
                'kind': 'abstract',
                'abstract': cls,
                'concretes': [],
            }
    for cls in classes:
        if cls['abstract']:
            continue
        parent = cls['extends']
        if parent is not None and parent in modules:
            modules[parent]['concretes'].append(cls)
        else:
            modules[cls['name']] = {'kind': 'concrete', 'cls': cls}
    return modules


def _write_cabal(modules, output_dir):
    module_list = ', '.join(['Token'] + sorted(modules))
    content = (
        'cabal-version: 3.0\n'
        'name:          interpreter\n'
        'version:       0.1.0.0\n'
        '\n'
        'executable interpreter\n'
        '  main-is:          Main.hs\n'
        f'  other-modules:    {module_list}\n'
        '  build-depends:    base, aeson, bytestring, containers, text\n'
        '  default-language: Haskell2010\n'
        '  hs-source-dirs:   .\n'
    )
    (output_dir / 'interpreter.cabal').write_text(content)


def _copy_token(output_dir):
    src = Path(__file__).parent / 'runtime' / 'Token.hs'
    shutil.copy(src, output_dir / 'Token.hs')
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: 6 passed (plus the earlier import test = 7 total)

- [ ] **Step 4: Commit**

```bash
git add src/plcc/lang/ext/haskell/emit.py src/plcc/lang/ext/haskell/emit_test.py
git commit -m "feat(haskell): emit cabal file and copy Token.hs"
```

---

### Task 5: emit.py — data type declarations

**Files:**
- Modify: `src/plcc/lang/ext/haskell/emit.py`
- Modify: `src/plcc/lang/ext/haskell/emit_test.py`

**Interfaces:**
- Consumes: `_group_modules(classes)` from Task 4
- Produces: `<RuleName>.hs` files containing `data` declarations

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/haskell/emit_test.py`:

```python
def test_emit_writes_module_for_abstract_rule(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'Expr.hs').exists()


def test_abstract_module_contains_data_declaration(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'data Expr' in text


def test_abstract_module_contains_concrete_constructor(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'NumExpr' in text


def test_concrete_constructor_has_token_field(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'num :: Token' in text


def test_emit_writes_module_for_lone_concrete(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'Prog.hs').exists()


def test_lone_concrete_module_contains_data_declaration(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Prog.hs').read_text()
    assert 'data Prog' in text


def test_lone_concrete_field_uses_class_type(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Prog.hs').read_text()
    assert 'expr :: Expr' in text


def test_all_types_derive_show_and_eq(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    for path in [tmp_path / 'Expr.hs', tmp_path / 'Prog.hs']:
        text = path.read_text()
        assert 'deriving (Show, Eq)' in text


def test_list_field_uses_bracket_type(monkeypatch, tmp_path):
    model = {
        "start": "stmts",
        "classes": [
            {
                "name": "Stmts",
                "extends": None,
                "abstract": False,
                "rule_name": "stmts",
                "fields": [{"name": "items", "type": "Token", "is_list": True}],
            }
        ],
        "semantic_sections": [],
    }
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Stmts.hs').read_text()
    assert 'items :: [Token]' in text
```

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: 9 FAILs (no module files written yet)

- [ ] **Step 2: Implement module file generation (data declarations only)**

Add to `src/plcc/lang/ext/haskell/emit.py` and update `emit()`:

```python
def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    modules = _group_modules(model['classes'])
    _write_cabal(modules, output_dir)
    _copy_token(output_dir)
    section = _find_haskell_section(model)
    fragments_by_class = _group_fragments(section.get('fragments', []) if section else [])
    for module_name, module_info in modules.items():
        _write_module(module_name, module_info, fragments_by_class, output_dir)


def _write_module(module_name, module_info, fragments_by_class, output_dir):
    content = _render_module(module_name, module_info, fragments_by_class)
    (output_dir / f'{module_name}.hs').write_text(content)


def _render_module(module_name, module_info, fragments_by_class):
    frags = fragments_by_class.get(module_name, [])
    top_frags = [f for f in frags if f['kind'] == 'top']
    import_frags = [f for f in frags if f['kind'] == 'import']
    body_frags = [f for f in frags if f['kind'] == 'body']

    lines = []
    for f in top_frags:
        lines.append(f['body'])
    lines.append(f'module {module_name} where')
    lines.append('')
    lines.append('import Data.Aeson (FromJSON (..), Value (..), withObject, (.:))')
    lines.append('import Data.Aeson.Types (Parser)')
    lines.append('import Data.List (sort)')
    lines.append('import Data.Text (unpack)')
    lines.append('import Token')
    for imp in _collect_imports(module_name, module_info):
        lines.append(f'import {imp}')
    for f in import_frags:
        lines.append(f['body'])
    lines.append('')
    lines.extend(_render_data(module_name, module_info))
    lines.append('')
    for f in body_frags:
        lines.append(f['body'])
    return '\n'.join(lines) + '\n'


def _collect_imports(module_name, module_info):
    """Return sorted list of module names to import (excluding Token and self)."""
    concretes = (module_info['concretes'] if module_info['kind'] == 'abstract'
                 else [module_info['cls']])
    imports = set()
    for cls in concretes:
        for field in cls['fields']:
            ft = field['type']
            if ft != 'Token' and ft != module_name:
                imports.add(ft)
    return sorted(imports)


def _render_data(module_name, module_info):
    lines = []
    if module_info['kind'] == 'abstract':
        concretes = module_info['concretes']
        lines.append(f'data {module_name}')
        for i, cls in enumerate(concretes):
            prefix = '    = ' if i == 0 else '    | '
            fields_str = _render_record_fields(cls['fields'])
            if fields_str:
                lines.append(f'{prefix}{cls["name"]} {{ {fields_str} }}')
            else:
                lines.append(f'{prefix}{cls["name"]}')
    else:
        cls = module_info['cls']
        fields_str = _render_record_fields(cls['fields'])
        if fields_str:
            lines.append(f'data {module_name} = {cls["name"]} {{ {fields_str} }}')
        else:
            lines.append(f'data {module_name} = {cls["name"]}')
    lines.append('    deriving (Show, Eq)')
    return lines


def _render_record_fields(fields):
    parts = [f'{f["name"]} :: {_hs_type(f)}' for f in fields]
    return ', '.join(parts)


def _hs_type(field):
    base = field['type']
    return f'[{base}]' if field['is_list'] else base


def _find_haskell_section(model):
    for s in model.get('semantic_sections', []):
        if s.get('language', '').lower() == 'haskell':
            return s
    return None


def _group_fragments(fragments):
    groups = {}
    for frag in fragments:
        groups.setdefault(frag['class_name'], []).append(frag)
    return groups
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/lang/ext/haskell/emit.py src/plcc/lang/ext/haskell/emit_test.py
git commit -m "feat(haskell): emit data type declarations per rule module"
```

---

### Task 6: emit.py — FromJSON instances

**Files:**
- Modify: `src/plcc/lang/ext/haskell/emit.py`
- Modify: `src/plcc/lang/ext/haskell/emit_test.py`

**Interfaces:**
- Consumes: `_render_module` from Task 5 (adds FromJSON block after data declaration)
- Produces: `instance FromJSON <RuleName>` in each generated module

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/haskell/emit_test.py`:

```python
def test_abstract_module_has_from_json_instance(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'instance FromJSON Expr' in text


def test_from_json_matches_on_rule_name(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert '"expr"' in text


def test_from_json_matches_constructor_by_sorted_field_names(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert '["num"]' in text
    assert 'NumExpr' in text


def test_lone_concrete_has_from_json_instance(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Prog.hs').read_text()
    assert 'instance FromJSON Prog' in text


def test_from_json_uses_parse_field(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'parseField' in text


def test_from_json_parses_children_as_pairs(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'parseChildren' in text
```

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: 6 FAILs (FromJSON not yet generated)

- [ ] **Step 2: Implement FromJSON generation**

In `_render_module` in `emit.py`, add `_render_from_json` call between the data declaration and body fragments:

```python
def _render_module(module_name, module_info, fragments_by_class):
    frags = fragments_by_class.get(module_name, [])
    top_frags = [f for f in frags if f['kind'] == 'top']
    import_frags = [f for f in frags if f['kind'] == 'import']
    body_frags = [f for f in frags if f['kind'] == 'body']

    lines = []
    for f in top_frags:
        lines.append(f['body'])
    lines.append(f'module {module_name} where')
    lines.append('')
    lines.append('import Data.Aeson (FromJSON (..), Value (..), withObject, (.:))')
    lines.append('import Data.Aeson.Types (Parser)')
    lines.append('import Data.List (sort)')
    lines.append('import Data.Text (unpack)')
    lines.append('import Token')
    for imp in _collect_imports(module_name, module_info):
        lines.append(f'import {imp}')
    for f in import_frags:
        lines.append(f['body'])
    lines.append('')
    lines.extend(_render_data(module_name, module_info))
    lines.append('')
    lines.extend(_render_from_json(module_name, module_info))
    lines.append('')
    for f in body_frags:
        lines.append(f['body'])
    return '\n'.join(lines) + '\n'
```

Add the `_render_from_json` function:

```python
def _render_from_json(module_name, module_info):
    if module_info['kind'] == 'abstract':
        rule_name = module_info['abstract']['rule_name']
        concretes = module_info['concretes']
    else:
        rule_name = module_info['cls']['rule_name']
        concretes = [module_info['cls']]

    lines = [
        f'instance FromJSON {module_name} where',
        f'    parseJSON = withObject "{module_name}" $ \\o -> do',
        f'        rule     <- o .: "rule"',
        f'        rawChildren <- o .: "children"',
        f'        let children = parseChildren rawChildren',
        f'            fns      = sort (map fst children)',
        f'        case (rule :: String) of',
        f'            "{rule_name}" -> case fns of',
    ]
    for cls in concretes:
        field_names = sorted(f['name'] for f in cls['fields'])
        fns_literal = '[' + ', '.join(f'"{n}"' for n in field_names) + ']'
        if cls['fields']:
            first = cls['fields'][0]['name']
            rest = cls['fields'][1:]
            expr = f'{cls["name"]} <$> parseField children "{first}"'
            for f in rest:
                expr += f'\n                              <*> parseField children "{f["name"]}"'
        else:
            expr = f'return {cls["name"]}'
        lines.append(f'                {fns_literal} ->')
        lines.append(f'                    {expr}')
    lines.append(f'                fns -> fail ("unknown variant of {rule_name}: " ++ show fns)')
    lines.append(f'            r -> fail ("unexpected rule: " ++ r)')
    return lines
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/lang/ext/haskell/emit.py src/plcc/lang/ext/haskell/emit_test.py
git commit -m "feat(haskell): emit FromJSON instances for rule modules"
```

---

### Task 7: emit.py — fragments and `file` override

**Files:**
- Modify: `src/plcc/lang/ext/haskell/emit.py`
- Modify: `src/plcc/lang/ext/haskell/emit_test.py`

**Interfaces:**
- Consumes: `_group_fragments`, `_find_haskell_section` from Task 5
- Produces: `top`, `import`, `body` fragments placed correctly; `file` fragments overwrite entire module

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/haskell/emit_test.py`:

```python
def _model_with_fragments(fragment_list):
    model = _minimal_model()
    model['semantic_sections'] = [{'language': 'haskell', 'fragments': fragment_list}]
    return model


def test_top_fragment_appears_before_module_declaration(monkeypatch, tmp_path):
    model = _model_with_fragments([
        {'class_name': 'Expr', 'kind': 'top', 'body': '{-# LANGUAGE OverloadedStrings #-}'}
    ])
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Expr.hs').read_text()
    top_pos = text.index('{-# LANGUAGE')
    module_pos = text.index('module Expr')
    assert top_pos < module_pos


def test_import_fragment_appears_after_generated_imports(monkeypatch, tmp_path):
    model = _model_with_fragments([
        {'class_name': 'Expr', 'kind': 'import', 'body': 'import Data.Map (Map)'}
    ])
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Expr.hs').read_text()
    assert 'import Data.Map (Map)' in text
    token_pos = text.index('import Token')
    map_pos = text.index('import Data.Map (Map)')
    assert token_pos < map_pos


def test_body_fragment_appears_after_from_json(monkeypatch, tmp_path):
    model = _model_with_fragments([
        {'class_name': 'Expr', 'kind': 'body',
         'body': '_run :: Expr -> String\n_run (NumExpr t) = lexeme t'}
    ])
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Expr.hs').read_text()
    assert '_run :: Expr -> String' in text
    from_json_pos = text.index('instance FromJSON Expr')
    body_pos = text.index('_run :: Expr -> String')
    assert from_json_pos < body_pos


def test_file_fragment_replaces_entire_module(monkeypatch, tmp_path):
    model = _model_with_fragments([
        {'class_name': 'Expr', 'kind': 'file', 'body': '-- custom Expr module\nmodule Expr where\n'}
    ])
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Expr.hs').read_text()
    assert '-- custom Expr module' in text
    assert 'instance FromJSON Expr' not in text
```

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: The `top`, `import`, and `body` fragment tests already pass (placed in `_render_module`); only `file` override fails.

- [ ] **Step 2: Implement `file` fragment override**

In `emit.py`, update `emit()` and `_write_module()` to apply `file` fragments after all regular modules are written:

```python
def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    modules = _group_modules(model['classes'])
    _write_cabal(modules, output_dir)
    _copy_token(output_dir)
    section = _find_haskell_section(model)
    all_frags = section.get('fragments', []) if section else []
    fragments_by_class = _group_fragments(all_frags)
    for module_name, module_info in modules.items():
        _write_module(module_name, module_info, fragments_by_class, output_dir)
    for frag in all_frags:
        if frag['kind'] == 'file':
            (output_dir / f'{frag["class_name"]}.hs').write_text(frag['body'])
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/lang/ext/haskell/emit.py src/plcc/lang/ext/haskell/emit_test.py
git commit -m "feat(haskell): handle top/import/body/file fragments in emitter"
```

---

### Task 8: emit.py — default `_run` for start rule

**Files:**
- Modify: `src/plcc/lang/ext/haskell/emit.py`
- Modify: `src/plcc/lang/ext/haskell/emit_test.py`

**Interfaces:**
- Consumes: `model['start']`, body fragments for the start rule module
- Produces: `_run :: StartType -> String\n_run = show` appended to start module when no `_run` in body fragments

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/haskell/emit_test.py`:

```python
def test_default_run_generated_when_start_has_no_body_fragment(monkeypatch, tmp_path):
    # _minimal_model() start is 'prog' → start module is 'Prog'
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Prog.hs').read_text()
    assert '_run :: Prog -> String' in text
    assert '_run = show' in text


def test_default_run_not_generated_when_user_provides_it(monkeypatch, tmp_path):
    model = _model_with_fragments([
        {'class_name': 'Prog', 'kind': 'body',
         'body': '_run :: Prog -> String\n_run (Prog e) = show e'}
    ])
    _run_emit(monkeypatch, tmp_path, model)
    text = (tmp_path / 'Prog.hs').read_text()
    # User's _run is present; default '_run = show' must not be added
    assert text.count('_run') >= 1
    assert '_run = show' not in text


def test_default_run_not_added_to_non_start_modules(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Expr.hs').read_text()
    assert '_run = show' not in text
```

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: 3 FAILs (default `_run` not generated yet)

- [ ] **Step 2: Implement default `_run` generation**

Update `emit()` and `_write_module()` in `emit.py`:

```python
def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    modules = _group_modules(model['classes'])
    _write_cabal(modules, output_dir)
    _copy_token(output_dir)
    section = _find_haskell_section(model)
    all_frags = section.get('fragments', []) if section else []
    fragments_by_class = _group_fragments(all_frags)
    start_module = model['start'][0].upper() + model['start'][1:]
    for module_name, module_info in modules.items():
        is_start = (module_name == start_module)
        _write_module(module_name, module_info, fragments_by_class, output_dir, is_start)
    for frag in all_frags:
        if frag['kind'] == 'file':
            (output_dir / f'{frag["class_name"]}.hs').write_text(frag['body'])


def _write_module(module_name, module_info, fragments_by_class, output_dir, is_start=False):
    frags = fragments_by_class.get(module_name, [])
    # Check for file override — skip rendering if file fragment exists
    content = _render_module(module_name, module_info, fragments_by_class)
    if is_start:
        body_frags = [f for f in frags if f['kind'] == 'body']
        user_has_run = any('_run' in f['body'] for f in body_frags)
        if not user_has_run:
            content = content.rstrip('\n') + f'\n\n_run :: {module_name} -> String\n_run = show\n'
    (output_dir / f'{module_name}.hs').write_text(content)
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/lang/ext/haskell/emit.py src/plcc/lang/ext/haskell/emit_test.py
git commit -m "feat(haskell): generate default _run for start rule when not provided"
```

---

### Task 9: emit.py — Main.hs generation

**Files:**
- Modify: `src/plcc/lang/ext/haskell/emit.py`
- Modify: `src/plcc/lang/ext/haskell/emit_test.py`

**Interfaces:**
- Consumes: `model['start']`, `modules` dict from Task 4
- Produces: `Main.hs` in output dir

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/haskell/emit_test.py`:

```python
def test_emit_writes_main_hs(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    assert (tmp_path / 'Main.hs').exists()


def test_main_hs_imports_start_module(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Main.hs').read_text()
    assert 'import Prog' in text


def test_main_hs_calls_run_on_start_type(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Main.hs').read_text()
    assert '_run' in text
    assert 'Prog' in text


def test_main_hs_outputs_json_result_line(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Main.hs').read_text()
    assert '"result"' in text or 'result' in text


def test_main_hs_outputs_json_error_line(monkeypatch, tmp_path):
    _run_emit(monkeypatch, tmp_path, _minimal_model())
    text = (tmp_path / 'Main.hs').read_text()
    assert '"error"' in text or 'error' in text
```

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: 5 FAILs (Main.hs not written yet)

- [ ] **Step 2: Implement Main.hs generation**

Add `_write_main` and call it from `emit()`:

```python
def emit(model, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    modules = _group_modules(model['classes'])
    _write_cabal(modules, output_dir)
    _copy_token(output_dir)
    section = _find_haskell_section(model)
    all_frags = section.get('fragments', []) if section else []
    fragments_by_class = _group_fragments(all_frags)
    start_module = model['start'][0].upper() + model['start'][1:]
    for module_name, module_info in modules.items():
        is_start = (module_name == start_module)
        _write_module(module_name, module_info, fragments_by_class, output_dir, is_start)
    for frag in all_frags:
        if frag['kind'] == 'file':
            (output_dir / f'{frag["class_name"]}.hs').write_text(frag['body'])
    _write_main(start_module, modules, output_dir)


def _write_main(start_module, modules, output_dir):
    import_lines = '\n'.join(f'import {name}' for name in sorted(modules))
    content = (
        'module Main where\n'
        '\n'
        'import Data.Aeson (eitherDecode, encode, object, (.=))\n'
        'import qualified Data.ByteString.Lazy.Char8 as BL\n'
        'import System.IO (hSetBuffering, stdout, BufferMode (..))\n'
        f'{import_lines}\n'
        '\n'
        'main :: IO ()\n'
        'main = do\n'
        '    hSetBuffering stdout LineBuffering\n'
        '    contents <- getContents\n'
        '    mapM_ handle (filter (not . null) (lines contents))\n'
        '  where\n'
        '    handle line = case eitherDecode (BL.pack line) of\n'
        '        Left err ->\n'
        '            BL.putStrLn $ encode $ object\n'
        '                [ "kind" .= ("error" :: String)\n'
        '                , "message" .= err\n'
        '                ]\n'
        '        Right tree ->\n'
        '            BL.putStrLn $ encode $ object\n'
        '                [ "kind" .= ("result" :: String)\n'
        f'                , "value" .= _run (tree :: {start_module})\n'
        '                ]\n'
    )
    (output_dir / 'Main.hs').write_text(content)
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py`
Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/lang/ext/haskell/emit.py src/plcc/lang/ext/haskell/emit_test.py
git commit -m "feat(haskell): emit Main.hs entry point"
```

---

### Task 10: build_test.py and run_test.py

**Files:**
- Create: `src/plcc/lang/ext/haskell/build_test.py`
- Create: `src/plcc/lang/ext/haskell/run_test.py`

**Interfaces:**
- Consumes: `build.main` from Task 2, `run.main` from Task 2

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/lang/ext/haskell/build_test.py`:

```python
import subprocess

import pytest

from .build import main as build_main


def test_build_invokes_cabal_build(monkeypatch, tmp_path):
    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class R:
            returncode = 0
        return R()
    monkeypatch.setattr(subprocess, 'run', fake_run)
    try:
        build_main([f'--output={tmp_path}'])
    except SystemExit:
        pass
    assert calls[0] == ['cabal', 'build']


def test_build_exits_with_cabal_return_code(monkeypatch, tmp_path):
    class FakeResult:
        returncode = 2
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: FakeResult())
    exit_code = None
    try:
        build_main([f'--output={tmp_path}'])
    except SystemExit as e:
        exit_code = e.code
    assert exit_code == 2


def test_build_uses_output_dir_as_cwd(monkeypatch, tmp_path):
    cwds = []
    def fake_run(cmd, cwd=None, **kwargs):
        cwds.append(cwd)
        class R:
            returncode = 0
        return R()
    monkeypatch.setattr(subprocess, 'run', fake_run)
    try:
        build_main([f'--output={tmp_path}'])
    except SystemExit:
        pass
    assert cwds[0] == str(tmp_path)
```

Create `src/plcc/lang/ext/haskell/run_test.py`:

```python
import subprocess

import pytest

from .run import main as run_main


def test_run_invokes_cabal_run_interpreter(monkeypatch, tmp_path):
    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class R:
            returncode = 0
        return R()
    monkeypatch.setattr(subprocess, 'run', fake_run)
    try:
        run_main([f'--output={tmp_path}'])
    except SystemExit:
        pass
    assert calls[0] == ['cabal', 'run', 'interpreter']


def test_run_exits_with_process_return_code(monkeypatch, tmp_path):
    class FakeResult:
        returncode = 42
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: FakeResult())
    exit_code = None
    try:
        run_main([f'--output={tmp_path}'])
    except SystemExit as e:
        exit_code = e.code
    assert exit_code == 42


def test_run_exits_130_on_keyboard_interrupt(monkeypatch, tmp_path):
    def raise_ki(*a, **kw):
        raise KeyboardInterrupt()
    monkeypatch.setattr(subprocess, 'run', raise_ki)
    exit_code = None
    try:
        run_main([f'--output={tmp_path}'])
    except SystemExit as e:
        exit_code = e.code
    except KeyboardInterrupt:
        pytest.fail("KeyboardInterrupt should be converted to sys.exit(130)")
    assert exit_code == 130
```

Run: `bin/test/units.bash src/plcc/lang/ext/haskell/build_test.py src/plcc/lang/ext/haskell/run_test.py`
Expected: All 6 tests pass (build.py and run.py were already written in Task 2 with the correct behavior).

- [ ] **Step 2: Commit**

```bash
git add src/plcc/lang/ext/haskell/build_test.py src/plcc/lang/ext/haskell/run_test.py
git commit -m "test(haskell): add unit tests for build.py and run.py"
```

---

### Task 11: BATS command and e2e tests

**Files:**
- Create: `tests/bats/commands/plcc-haskell-emit.bats`
- Create: `tests/bats/e2e/haskell.bats`

**Interfaces:**
- Consumes: all installed entry points from Tasks 2 and 6; a complete plcc spec with `%haskell` section

- [ ] **Step 1: Write `tests/bats/commands/plcc-haskell-emit.bats`**

```bash
#!/usr/bin/env bats

@test "plcc-haskell-emit: no args exits nonzero" {
    run plcc-haskell-emit
    [ "$status" -ne 0 ]
}

@test "plcc-haskell-emit: --help exits 0" {
    run plcc-haskell-emit --help
    [ "$status" -eq 0 ]
}

@test "plcc-haskell-emit: emits interpreter.cabal given minimal model" {
    local out
    out=$(mktemp -d)
    echo '{"start":"prog","classes":[{"name":"Prog","extends":null,"abstract":false,"rule_name":"prog","fields":[]}],"semantic_sections":[]}' \
        | plcc-haskell-emit --output="$out"
    [ -f "$out/interpreter.cabal" ]
    rm -rf "$out"
}

@test "plcc-haskell-emit: emits Token.hs given minimal model" {
    local out
    out=$(mktemp -d)
    echo '{"start":"prog","classes":[{"name":"Prog","extends":null,"abstract":false,"rule_name":"prog","fields":[]}],"semantic_sections":[]}' \
        | plcc-haskell-emit --output="$out"
    [ -f "$out/Token.hs" ]
    rm -rf "$out"
}
```

- [ ] **Step 2: Run the command tests**

Run: `bin/test/commands.bash`
Expected: All haskell emit tests pass.

- [ ] **Step 3: Write `tests/bats/e2e/haskell.bats`**

This test exercises the full pipeline: spec → model → emit → build → run.

```bash
#!/usr/bin/env bats

setup() {
    SPEC_DIR=$(mktemp -d)
    OUT_DIR=$(mktemp -d)
    cat > "$SPEC_DIR/arith.plcc" << 'EOF'
%lexical
INT /[0-9]+/
PLUS /\+/

%syntactic
<prog>     ::= expr:Expr
<expr>Expr ::= left:Expr PLUS right:Term
             | Term
<term>Term ::= num:INT

%haskell
Expr
%%%
body
_run :: Prog -> String
_run (Prog e) = evalExpr e

evalExpr :: Expr -> String
evalExpr (ExprLeft l _ r) = show (read (evalExpr l) + read (evalTerm r) :: Int)
evalExpr (ExprRight t)    = evalTerm t

evalTerm :: Term -> String
evalTerm (Term t) = lexeme t
%%%
EOF
}

teardown() {
    rm -rf "$SPEC_DIR" "$OUT_DIR"
}

@test "haskell pipeline: full emit-build-run roundtrip" {
    plcc-spec < "$SPEC_DIR/arith.plcc" \
        | plcc-model \
        | plcc-haskell-emit --output="$OUT_DIR"
    plcc-haskell-build --output="$OUT_DIR"
    result=$(plcc-spec < "$SPEC_DIR/arith.plcc" \
        | plcc-scan \
        | plcc-parse \
        | plcc-trees \
        | plcc-model \
        | plcc-haskell-run --output="$OUT_DIR" \
        <<< '1 + 2')
    # result should be JSON {"kind":"result","value":"3"}
    echo "$result" | grep -q '"value":"3"'
}
```

> **Note:** The exact PLCC spec syntax and pipeline invocation should match the patterns in existing e2e tests under `tests/bats/e2e/`. Adjust rule names and the spec if needed to match the actual grammar format used by this project.

- [ ] **Step 4: Run the e2e test**

Run: `bin/test/e2e.bash`
Expected: haskell test passes. If it fails, check the generated Haskell compiles and the output JSON format matches what plcc-lang-run expects.

- [ ] **Step 5: Run the full test suite**

Run: `bin/test/functional.bash`
Expected: All tiers pass.

- [ ] **Step 6: Commit**

```bash
git add tests/bats/commands/plcc-haskell-emit.bats tests/bats/e2e/haskell.bats
git commit -m "test(haskell): add BATS command and e2e tests"
```

---

## Self-Review

**Spec coverage:**

| Spec requirement | Task |
|-----------------|------|
| Devcontainer: GHC + cabal feature | Task 1 |
| Extension location `src/plcc/lang/ext/haskell/` | Task 2 |
| Entry points: emit, build, run | Task 2 |
| Token.hs runtime with parseField/parseChildren | Task 3 |
| interpreter.cabal generated with aeson dep | Task 4 |
| Token.hs copied to output | Task 4 |
| One module per rule (abstract + concretes) | Task 5 |
| data declarations with correct constructors | Task 5 |
| All types derive Show and Eq | Task 5 |
| Field types: Token → Token, class → class, is_list → `[...]` | Task 5 |
| FromJSON instance per module | Task 6 |
| Field matching uses sorted field names | Task 6 |
| top/import/body fragments placed correctly | Task 7 |
| file fragment replaces entire module | Task 7 |
| Default `_run = show` for start rule when not provided | Task 8 |
| Main.hs reads JSON lines, calls `_run`, outputs JSON result/error | Task 9 |
| build.py runs `cabal build` | Task 10 |
| run.py runs `cabal run interpreter`, exits 130 on KeyboardInterrupt | Task 10 |
| BATS command and e2e tests | Task 11 |

All spec requirements covered.
