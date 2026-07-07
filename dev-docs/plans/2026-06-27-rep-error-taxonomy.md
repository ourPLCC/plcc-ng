# plcc-rep Error Taxonomy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the error taxonomy defined in the spec so that `plcc-rep` distinguishes Language Behavior (continue), Specification Errors (exit with message), and plcc-ng Errors (exit with report prompt).

**Architecture:** Each language runtime gains a `LanguageError` base exception and emits a startup `{"kind": "ready"}` handshake on stdout. The runtime template catches `LanguageError` → `{"kind": "error"}` (REPL continues) and all other exceptions → `{"kind": "specification_error"}` (REPL exits). `plcc-rep` reads the ready handshake before the REPL loop (treating EOF as a Specification Error) and handles the new `specification_error` record kind.

**Tech Stack:** Python (pytest, Jinja2 templates), JavaScript (Node.js), Java, Haskell (via `_write_main` in `emit.py`)

## Global Constraints

- All tests run via `bin/test/units.bash` (pytest). Run after every task.
- TDD: failing test first, then minimal implementation.
- Do not modify tests not related to the task at hand.
- Commit after each task passes.
- Follow existing code style in each file.
- `[skip ci]` is not needed for code commits on this branch.

---

## File Map

| File | Change |
| --- | --- |
| `src/plcc/lang/ext/python/runtime/base.py` | Add `LanguageError` class |
| `src/plcc/lang/ext/python/runtime/base_test.py` | Tests for `LanguageError` |
| `src/plcc/lang/ext/python/templates/main.py.jinja` | Ready signal, `LanguageError` vs `specification_error` |
| `src/plcc/lang/ext/python/emit_test.py` | Integration tests for new template behavior |
| `src/plcc/lang/ext/javascript/runtime/base.js` | Add `LanguageError` class |
| `src/plcc/lang/ext/javascript/runtime/base_test.py` | Tests for `LanguageError` (Node subprocess) |
| `src/plcc/lang/ext/javascript/templates/main.js.jinja` | Ready signal, `LanguageError` vs `specification_error` |
| `src/plcc/lang/ext/java/runtime/LanguageError.java` | New: `LanguageError` unchecked exception |
| `src/plcc/lang/ext/java/templates/Main.java.jinja` | Ready signal, `LanguageError` vs `specification_error` |
| `src/plcc/lang/ext/haskell/emit.py` | Update `_write_main`: ready signal, `LanguageError`, `specification_error` |
| `src/plcc/lang/ext/haskell/emit_test.py` | Tests for updated `_write_main` output |
| `src/plcc/cmd/_test_helpers.py` | Add `_ready_record()`, `_specification_error_record()` |
| `src/plcc/cmd/rep.py` | `_wait_for_ready`, `specification_error` handling, `error` rendering |
| `src/plcc/cmd/rep_test.py` | Tests for all new `plcc-rep` behaviors |

---

### Task 1: Python `LanguageError`

**Files:**
- Modify: `src/plcc/lang/ext/python/runtime/base.py`
- Modify: `src/plcc/lang/ext/python/runtime/base_test.py`

**Interfaces:**
- Produces: `LanguageError(Exception)` importable from `runtime.base` as `_plcc.LanguageError`

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/python/runtime/base_test.py`:

```python
from .base import LanguageError


def test_language_error_is_exception():
    assert issubclass(LanguageError, Exception)


def test_language_error_can_be_raised_and_caught():
    with pytest.raises(LanguageError, match="type mismatch"):
        raise LanguageError("type mismatch")


def test_language_error_subclass_is_caught_as_language_error():
    class TypeError(LanguageError):
        pass
    with pytest.raises(LanguageError):
        raise TypeError("bad type")
```

Also add `import pytest` at the top of the file.

- [ ] **Step 2: Run to verify failure**

```bash
bin/test/units.bash src/plcc/lang/ext/python/runtime/base_test.py -v
```

Expected: FAIL — `cannot import name 'LanguageError'`

- [ ] **Step 3: Implement `LanguageError` in `base.py`**

Add to the end of `src/plcc/lang/ext/python/runtime/base.py`:

```python
class LanguageError(Exception):
    pass
```

- [ ] **Step 4: Run to verify pass**

```bash
bin/test/units.bash src/plcc/lang/ext/python/runtime/base_test.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/ext/python/runtime/base.py src/plcc/lang/ext/python/runtime/base_test.py
git commit -m "feat(python): add LanguageError to Python runtime base"
```

---

### Task 2: Python template — ready signal + `specification_error`

**Files:**
- Modify: `src/plcc/lang/ext/python/templates/main.py.jinja`
- Modify: `src/plcc/lang/ext/python/emit_test.py`

**Interfaces:**
- Consumes: `LanguageError` from `runtime.base` (Task 1)
- Produces: `{"kind": "ready"}` as first stdout line; `{"kind": "error"}` for `LanguageError`; `{"kind": "specification_error"}` for other exceptions

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/python/emit_test.py` (import `json` is already present):

```python
def test_emit_generated_main_emits_ready_on_startup(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    result = subprocess.run(
        [sys.executable, str(tmp_path / 'main.py')],
        input='',
        capture_output=True,
        text=True,
    )
    first_line = result.stdout.splitlines()[0] if result.stdout else ''
    assert json.loads(first_line) == {"kind": "ready"}


def test_emit_generated_main_language_error_returns_error_record(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['fragments'].append({
        "class_name": "Program", "kind": "body",
        "body": "def _run(self):\n    from runtime.base import LanguageError\n    raise LanguageError('type mismatch')"
    })
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    tree_json = json.dumps({
        "rule": "program",
        "children": [
            {"rule": "Expr", "children": [
                {"rule": "Term", "children": [{"kind": "token", "name": "NUM", "lexeme": "1"}]},
                {"rule": "ExprRest", "alt": "NilRest", "children": []}
            ]}
        ]
    })
    result = subprocess.run(
        [sys.executable, str(tmp_path / 'main.py')],
        input=tree_json + '\n',
        capture_output=True,
        text=True,
    )
    records = [json.loads(l) for l in result.stdout.splitlines() if l]
    error_records = [r for r in records if r.get('kind') == 'error']
    assert error_records, f"No error record found in: {result.stdout}"
    assert error_records[0]['message'] == 'type mismatch'


def test_emit_generated_main_other_exception_returns_specification_error(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['fragments'].append({
        "class_name": "Program", "kind": "body",
        "body": "def _run(self):\n    raise ValueError('stack underflow')"
    })
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    tree_json = json.dumps({
        "rule": "program",
        "children": [
            {"rule": "Expr", "children": [
                {"rule": "Term", "children": [{"kind": "token", "name": "NUM", "lexeme": "1"}]},
                {"rule": "ExprRest", "alt": "NilRest", "children": []}
            ]}
        ]
    })
    result = subprocess.run(
        [sys.executable, str(tmp_path / 'main.py')],
        input=tree_json + '\n',
        capture_output=True,
        text=True,
    )
    records = [json.loads(l) for l in result.stdout.splitlines() if l]
    spec_error_records = [r for r in records if r.get('kind') == 'specification_error']
    assert spec_error_records, f"No specification_error record found in: {result.stdout}"
    assert 'stack underflow' in spec_error_records[0]['message']
```

- [ ] **Step 2: Run to verify failure**

```bash
bin/test/units.bash src/plcc/lang/ext/python/emit_test.py::test_emit_generated_main_emits_ready_on_startup src/plcc/lang/ext/python/emit_test.py::test_emit_generated_main_language_error_returns_error_record src/plcc/lang/ext/python/emit_test.py::test_emit_generated_main_other_exception_returns_specification_error -v
```

Expected: all FAIL

- [ ] **Step 3: Update `main.py.jinja`**

Replace the entire contents of `src/plcc/lang/ext/python/templates/main.py.jinja` with:

```python
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime.base import LanguageError
from runtime.registry import Registry
{% for cls in classes %}from {{ cls.name }} import {{ cls.name }}
{% endfor %}
registry = Registry()
registry.register({% for cls in classes if not cls.abstract %}{{ cls.name }}{% if not loop.last %}, {% endif %}{% endfor %})

print(json.dumps({"kind": "ready"}), flush=True)

try:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            tree = registry.deserialize(json.loads(line))
            result = tree.{{ entry_point }}()
            print(json.dumps({"kind": "result", "value": repr(result) if result is not None else None}), flush=True)
        except LanguageError as e:
            print(json.dumps({"kind": "error", "type": type(e).__name__, "message": str(e)}), flush=True)
        except Exception as e:
            print(json.dumps({"kind": "specification_error", "type": type(e).__name__, "message": str(e)}), flush=True)
except KeyboardInterrupt:
    print("User interrupted execution by ^C.", flush=True)
    sys.exit(130)
```

- [ ] **Step 4: Run to verify pass**

```bash
bin/test/units.bash src/plcc/lang/ext/python/emit_test.py -v
```

Expected: all tests PASS (including existing ones)

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/ext/python/templates/main.py.jinja src/plcc/lang/ext/python/emit_test.py
git commit -m "feat(python): emit ready signal and specification_error in main template"
```

---

### Task 3: JavaScript `LanguageError` + template

**Files:**
- Modify: `src/plcc/lang/ext/javascript/runtime/base.js`
- Modify: `src/plcc/lang/ext/javascript/runtime/base_test.py`
- Modify: `src/plcc/lang/ext/javascript/templates/main.js.jinja`

**Interfaces:**
- Produces: `LanguageError` class in `runtime/base.js`, exported as `{ LanguageError }`; ready signal and `specification_error` in `main.js.jinja`

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/javascript/runtime/base_test.py`:

```python
def test_language_error_is_a_class():
    r = _node("const { LanguageError } = require('./base'); console.log(typeof LanguageError);")
    assert r.returncode == 0
    assert r.stdout.strip() == 'function'


def test_language_error_instance_is_error():
    r = _node("const { LanguageError } = require('./base'); const e = new LanguageError('oops'); console.log(e instanceof Error);")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true'


def test_language_error_subclass_is_language_error():
    r = _node("""
const { LanguageError } = require('./base');
class TypeError extends LanguageError {}
const e = new TypeError('bad');
console.log(e instanceof LanguageError);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true'
```

- [ ] **Step 2: Run to verify failure**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/runtime/base_test.py -v
```

Expected: FAIL — `LanguageError` not exported

- [ ] **Step 3: Add `LanguageError` to `base.js`**

Replace `src/plcc/lang/ext/javascript/runtime/base.js` with:

```javascript
class Node {}

class Token {
    constructor(kind, lexeme) {
        this.kind = kind;
        this.lexeme = lexeme;
    }

    toString() {
        return this.lexeme;
    }
}

class LanguageError extends Error {
    constructor(message) {
        super(message);
        this.name = 'LanguageError';
    }
}

module.exports = { Node, Token, LanguageError };
```

- [ ] **Step 4: Run to verify pass**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/runtime/base_test.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Update `main.js.jinja`**

Replace the entire contents of `src/plcc/lang/ext/javascript/templates/main.js.jinja` with:

```javascript
{% set concrete = classes | selectattr('abstract', 'equalto', false) | list %}
const { Registry } = require('./runtime/registry');
const { deserialize } = require('./runtime/deserialize');
const { LanguageError } = require('./runtime/base');
{% for cls in concrete %}const { {{ cls.name }} } = require('./{{ cls.name }}');
{% endfor %}
const registry = new Registry();
registry.register({% for cls in concrete %}{{ cls.name }}{% if not loop.last %}, {% endif %}{% endfor %});

process.on('SIGINT', () => {
    process.stdout.write('User interrupted execution by ^C.\n');
    process.exit(130);
});

console.log(JSON.stringify({ kind: 'ready' }));

const readline = require('readline');
const rl = readline.createInterface({ input: process.stdin });

rl.on('line', (line) => {
    line = line.trim();
    if (!line) return;
    try {
        const tree = deserialize(JSON.parse(line), registry);
        const result = tree.{{ entry_point }}();
        console.log(JSON.stringify({ kind: 'result', value: result != null ? String(result) : null }));
    } catch (e) {
        if (e instanceof LanguageError) {
            console.log(JSON.stringify({ kind: 'error', type: e.constructor.name, message: e.message ?? '' }));
        } else {
            console.log(JSON.stringify({ kind: 'specification_error', type: e.constructor.name, message: e.message ?? '' }));
        }
    }
});
```

- [ ] **Step 6: Run all JS tests**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/ -v
```

Expected: all tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/plcc/lang/ext/javascript/runtime/base.js src/plcc/lang/ext/javascript/runtime/base_test.py src/plcc/lang/ext/javascript/templates/main.js.jinja
git commit -m "feat(javascript): add LanguageError, ready signal, and specification_error"
```

---

### Task 4: Java `LanguageError` + template

**Files:**
- Create: `src/plcc/lang/ext/java/runtime/LanguageError.java`
- Modify: `src/plcc/lang/ext/java/templates/Main.java.jinja`
- Modify: `src/plcc/lang/ext/java/emit_test.py`

**Interfaces:**
- Produces: `runtime.LanguageError extends RuntimeException`; ready signal and `specification_error` in `Main.java.jinja`

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/java/emit_test.py`:

```python
def test_emit_main_java_catches_language_error_separately(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert 'LanguageError' in main_java
    assert 'specification_error' in main_java


def test_emit_main_java_contains_ready_signal(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert '"ready"' in main_java


def test_emit_copies_language_error_java(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'runtime' / 'LanguageError.java').exists()
```

- [ ] **Step 2: Run to verify failure**

```bash
bin/test/units.bash src/plcc/lang/ext/java/emit_test.py::test_emit_main_java_catches_language_error_separately src/plcc/lang/ext/java/emit_test.py::test_emit_main_java_contains_ready_signal src/plcc/lang/ext/java/emit_test.py::test_emit_copies_language_error_java -v
```

Expected: FAIL

- [ ] **Step 3: Create `LanguageError.java`**

Create `src/plcc/lang/ext/java/runtime/LanguageError.java`:

```java
package runtime;

public class LanguageError extends RuntimeException {
    public LanguageError(String message) {
        super(message);
    }
}
```

- [ ] **Step 4: Update `Main.java.jinja`**

Replace `src/plcc/lang/ext/java/templates/Main.java.jinja` with:

```java
import java.io.BufferedReader;
import java.io.InputStreamReader;
import org.json.JSONObject;
import runtime.Deserializer;
import runtime.LanguageError;
import runtime.Registry;

public class Main {
    public static void main(String[] args) throws Exception {
        Registry registry = new Registry();
        registry.register({% for cls in concrete_classes %}{{ cls.name }}.class{% if not loop.last %}, {% endif %}{% endfor %});
        Deserializer deserializer = new Deserializer(registry);

        JSONObject readyRecord = new JSONObject();
        readyRecord.put("kind", "ready");
        System.out.println(readyRecord.toString());
        System.out.flush();

        BufferedReader reader = new BufferedReader(new InputStreamReader(System.in));
        String line;
        while ((line = reader.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) continue;
            try {
                {{ start_class }} root = ({{ start_class }}) deserializer.deserialize(new JSONObject(line));
                java.lang.reflect.Method m = {{ start_class }}.class.getMethod("{{ entry_point }}");
                Object result = m.invoke(root);
                JSONObject record = new JSONObject();
                record.put("kind", "result");
                record.put("value", result != null ? result.toString() : JSONObject.NULL);
                System.out.println(record.toString());
                System.out.flush();
            } catch (java.lang.reflect.InvocationTargetException ite) {
                Throwable cause = ite.getCause() != null ? ite.getCause() : ite;
                JSONObject record = new JSONObject();
                if (cause instanceof LanguageError) {
                    record.put("kind", "error");
                } else {
                    record.put("kind", "specification_error");
                }
                record.put("type", cause.getClass().getSimpleName());
                record.put("message", cause.getMessage() != null ? cause.getMessage() : "");
                System.out.println(record.toString());
                System.out.flush();
            } catch (Exception e) {
                JSONObject record = new JSONObject();
                record.put("kind", "specification_error");
                record.put("type", e.getClass().getSimpleName());
                record.put("message", e.getMessage() != null ? e.getMessage() : "");
                System.out.println(record.toString());
                System.out.flush();
            }
        }
    }
}
```

Note: `java.lang.reflect.Method.invoke` wraps exceptions in `InvocationTargetException`, so the cause must be unwrapped to check for `LanguageError`.

- [ ] **Step 5: Verify `emit.py` copies Java runtime files**

Check `src/plcc/lang/ext/java/emit.py` to confirm it copies all `.java` files from the `runtime/` directory. If it uses a glob like `*.java`, `LanguageError.java` is automatically included. If it copies specific files, add `LanguageError.java` to the list.

```bash
grep -n "runtime\|copy\|java" src/plcc/lang/ext/java/emit.py | head -20
```

If the copy is file-specific, add `LanguageError.java` to the list. If glob-based, no change needed.

- [ ] **Step 6: Run to verify pass**

```bash
bin/test/units.bash src/plcc/lang/ext/java/emit_test.py -v
```

Expected: all tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/plcc/lang/ext/java/runtime/LanguageError.java src/plcc/lang/ext/java/templates/Main.java.jinja src/plcc/lang/ext/java/emit_test.py
git commit -m "feat(java): add LanguageError, ready signal, and specification_error"
```

---

### Task 5: Haskell `LanguageError` + `specification_error` + ready signal

**Files:**
- Modify: `src/plcc/lang/ext/haskell/emit.py` (function `_write_main`)
- Modify: `src/plcc/lang/ext/haskell/emit_test.py`

**Interfaces:**
- Produces: `_write_main` generates `Main.hs` with `LanguageError` data type, ready signal, and `specification_error` for non-`LanguageError` exceptions

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/haskell/emit_test.py`:

```python
def test_write_main_contains_language_error(tmp_path):
    from .emit import _write_main
    _write_main("Program", {}, tmp_path)
    main_hs = (tmp_path / 'Main.hs').read_text()
    assert 'LanguageError' in main_hs


def test_write_main_contains_ready_signal(tmp_path):
    from .emit import _write_main
    _write_main("Program", {}, tmp_path)
    main_hs = (tmp_path / 'Main.hs').read_text()
    assert '"ready"' in main_hs


def test_write_main_contains_specification_error(tmp_path):
    from .emit import _write_main
    _write_main("Program", {}, tmp_path)
    main_hs = (tmp_path / 'Main.hs').read_text()
    assert 'specification_error' in main_hs
```

- [ ] **Step 2: Run to verify failure**

```bash
bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py::test_write_main_contains_language_error src/plcc/lang/ext/haskell/emit_test.py::test_write_main_contains_ready_signal src/plcc/lang/ext/haskell/emit_test.py::test_write_main_contains_specification_error -v
```

Expected: FAIL

- [ ] **Step 3: Update `_write_main` in `emit.py`**

Replace the `_write_main` function in `src/plcc/lang/ext/haskell/emit.py`:

```python
def _write_main(start_module, modules, output_dir):
    import_lines = '\n'.join(f'import {name}' for name in sorted(modules))
    content = (
        '{-# LANGUAGE OverloadedStrings #-}\n'
        '{-# LANGUAGE DeriveAnyClass #-}\n'
        'module Main where\n'
        '\n'
        'import Control.Exception (Exception, SomeException, catch, evaluate, throwIO)\n'
        'import Data.Aeson (eitherDecode, encode, object, (.=))\n'
        'import qualified Data.ByteString.Lazy.Char8 as BL\n'
        'import Data.Typeable (Typeable)\n'
        'import System.IO (hSetBuffering, stdout, BufferMode (..))\n'
        f'{import_lines}\n'
        '\n'
        'newtype LanguageError = LanguageError String deriving (Show, Typeable)\n'
        'instance Exception LanguageError\n'
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
        '                    , "value" .= show v\n'
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

- [ ] **Step 4: Run to verify pass**

```bash
bin/test/units.bash src/plcc/lang/ext/haskell/emit_test.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/ext/haskell/emit.py src/plcc/lang/ext/haskell/emit_test.py
git commit -m "feat(haskell): add LanguageError, ready signal, and specification_error"
```

---

### Task 6: `plcc-rep` — startup handshake, `specification_error`, error rendering

**Files:**
- Modify: `src/plcc/cmd/_test_helpers.py`
- Modify: `src/plcc/cmd/rep.py`
- Modify: `src/plcc/cmd/rep_test.py`

**Interfaces:**
- Consumes: `{"kind": "ready"}` from interpreter on startup; `{"kind": "specification_error", "type": ..., "message": ...}` during session
- Produces: correct exit with messages for each error category

- [ ] **Step 1: Add test helpers**

Add to `src/plcc/cmd/_test_helpers.py`:

```python
def _ready_record():
    return json.dumps({"kind": "ready"}).encode() + b"\n"


def _specification_error_record(msg="stack underflow", type_="ValueError"):
    return json.dumps({"kind": "specification_error", "type": type_, "message": msg}).encode() + b"\n"
```

- [ ] **Step 2: Write the failing tests**

Add to `src/plcc/cmd/rep_test.py`:

```python
from plcc.cmd._test_helpers import _ready_record, _specification_error_record


def test_render_record_error_prints_only_message(capsys):
    record = {"kind": "error", "type": "TypeError", "message": "bad value"}
    _rep_module._render_record(record, "text")
    out, _ = capsys.readouterr()
    assert "bad value" in out
    assert "TypeError" not in out


def test_render_record_specification_error_prints_spec_error_message(capsys):
    record = {"kind": "specification_error", "type": "ValueError", "message": "stack underflow"}
    with pytest.raises(SystemExit) as exc_info:
        _rep_module._render_record(record, "text")
    assert exc_info.value.code != 0
    out, err = capsys.readouterr()
    combined = out + err
    assert "Specification error" in combined
    assert "stack underflow" in combined
    assert "Fix the errors" in combined


def test_render_record_unknown_kind_prints_plccng_error(capsys):
    record = {"kind": "unexpected_kind", "type": "X", "message": "oops"}
    with pytest.raises(SystemExit) as exc_info:
        _rep_module._render_record(record, "text")
    assert exc_info.value.code != 0
    out, err = capsys.readouterr()
    combined = out + err
    assert "plcc-ng error" in combined
    assert "report" in combined.lower()


def _make_interpreter_with_ready(response=b'{"kind":"result","value":"42"}\n'):
    interp = SimpleNamespace()
    interp.stdin = io.BytesIO()
    interp.stdout = io.BytesIO(_ready_record() + response)
    interp.poll = lambda: None
    return interp


def test_wait_for_ready_succeeds_when_interpreter_sends_ready(monkeypatch):
    interp = _make_interpreter_with_ready()
    # Should not raise
    _rep_module._wait_for_ready(interp)


def test_wait_for_ready_exits_with_spec_error_when_interpreter_sends_eof(capsys):
    interp = SimpleNamespace()
    interp.stdin = io.BytesIO()
    interp.stdout = io.BytesIO(b"")  # EOF immediately
    with pytest.raises(SystemExit) as exc_info:
        _rep_module._wait_for_ready(interp)
    assert exc_info.value.code != 0
    out, err = capsys.readouterr()
    combined = out + err
    assert "Specification error" in combined
    assert "Fix the errors" in combined
```

- [ ] **Step 3: Run to verify failure**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py::test_render_record_error_prints_only_message src/plcc/cmd/rep_test.py::test_render_record_specification_error_prints_spec_error_message src/plcc/cmd/rep_test.py::test_render_record_unknown_kind_prints_plccng_error src/plcc/cmd/rep_test.py::test_wait_for_ready_succeeds_when_interpreter_sends_ready src/plcc/cmd/rep_test.py::test_wait_for_ready_exits_with_spec_error_when_interpreter_sends_eof -v
```

Expected: FAIL

- [ ] **Step 4: Update `rep.py`**

**4a.** Replace `_render_record` in `src/plcc/cmd/rep.py`:

```python
def _render_record(record, verbose_format):
    if verbose_format == 'json':
        print(json.dumps(record))
        return
    kind = record.get('kind')
    if kind == 'result':
        value = record.get('value')
        if value is not None:
            print(value)
    elif kind == 'error':
        print(record.get('message', ''))
    elif kind == 'specification_error':
        msg = record.get('message', '')
        type_ = record.get('type', '')
        label = f"Specification error: {type_}: {msg}" if type_ else f"Specification error: {msg}"
        print_user_error(label)
        print_user_error("Fix the errors in your specification and re-run.")
        sys.exit(1)
    else:
        print_user_error(f"plcc-ng error: unexpected record kind '{kind}': {record}")
        print_user_error("Please report this at https://github.com/ourPLCC/plcc-ng/issues.")
        sys.exit(1)
```

**4b.** Add `_wait_for_ready` to `rep.py` (before `main`):

```python
def _wait_for_ready(interpreter):
    raw = interpreter.stdout.readline()
    if not raw:
        print_user_error("Specification error: interpreter failed to start.")
        print_user_error("Fix the errors in your specification and re-run.")
        sys.exit(1)
    try:
        record = json.loads(raw.decode('utf-8', errors='replace'))
        if record.get('kind') == 'ready':
            return
    except (json.JSONDecodeError, AttributeError):
        pass
    print_user_error(f"plcc-ng error: unexpected startup output from interpreter: {raw!r}")
    print_user_error("Please report this at https://github.com/ourPLCC/plcc-ng/issues.")
    sys.exit(1)
```

**4c.** Call `_wait_for_ready` in `main()` immediately after `subprocess.Popen`. The existing code in `main()` has:

```python
interpreter = subprocess.Popen(
    ['plcc-lang-run', f'--target={language}', f'--output={output_dir}'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=None,
)

try:
    handler = RepHandler(...)
```

Insert `_wait_for_ready(interpreter)` between the `Popen` call and the `try` block:

```python
interpreter = subprocess.Popen(
    ['plcc-lang-run', f'--target={language}', f'--output={output_dir}'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=None,
)

_wait_for_ready(interpreter)

try:
    handler = RepHandler(...)
```

- [ ] **Step 5: Update the existing test that changed behaviour**

`test_render_record_interpreter_error_writes_to_stdout` in `rep_test.py` currently checks that `"TypeError"` appears in output. With the new rendering, only `message` is printed — not `type`. Update it:

```python
def test_render_record_interpreter_error_writes_to_stdout(capsys):
    record = {"kind": "error", "type": "TypeError", "message": "bad value"}
    _rep_module._render_record(record, "text")
    out, err = capsys.readouterr()
    assert "bad value" in out
    assert err == ""
```

Also update the `RepHandler` fixture in `rep_test.py` to use an interpreter that sends the ready record first. Find the `_make_interpreter` helper and update it:

```python
def _make_interpreter(response=b'{"kind":"result","value":"42"}\n'):
    interp = SimpleNamespace()
    interp.stdin = io.BytesIO()
    interp.stdout = io.BytesIO(_ready_record() + response)
    interp.poll = lambda: None
    return interp
```

Also update `_make_dead_interpreter` to emit no ready record (EOF):

```python
def _make_dead_interpreter(returncode):
    interp = SimpleNamespace()
    interp.stdin = io.BytesIO()
    interp.stdout = io.BytesIO(b"")
    interp.poll = lambda: returncode
    return interp
```

**Important:** The `RepHandler` fixture uses `_make_interpreter()`. Because `_wait_for_ready` is called in `main()` (not in `RepHandler`), the handler tests do not call `_wait_for_ready`. However, the `_make_interpreter` helper is used for `_read_response` tests, where the interpreter's stdout is read directly. The ready record must be consumed before the handler tries to read the first result. Since `RepHandler.feed()` calls `_read_response` which reads one record at a time from `interpreter.stdout`, the ready record will be the first thing read.

Check: do existing handler tests use `h.feed()` to trigger `_read_response`? Yes. Those tests start with a fresh `BytesIO` where the first bytes are the response records. Since `_wait_for_ready` is NOT called by `RepHandler`, those tests are unaffected.

But: `_make_interpreter` builds the interpreter stub that `handler` fixture uses. Since `_wait_for_ready` is only in `main()`, not in `RepHandler`, the handler tests do NOT go through `_wait_for_ready`. The `_make_interpreter` helper does NOT need to prepend the ready record for handler tests.

Only the `main()` integration tests (`test_rep_main_*`) go through `_wait_for_ready`. Those tests stub out `subprocess.Popen` with `_MagicMock(stdin=_MagicMock(), wait=_MagicMock())`, which does not have a real `stdout`. You need to update `_setup_rep_main` (and the individual main tests) to mock `Popen` with a stub that provides a `stdout` returning the ready record.

Update `_setup_rep_main`:

```python
def _setup_rep_main(monkeypatch, tmp_path):
    import json as _j
    monkeypatch.chdir(tmp_path)
    (tmp_path / "grammar.plcc").write_text("")
    build = tmp_path / "build"
    build.mkdir()
    (build / ".spec").write_text(str(tmp_path / "grammar.plcc"))
    spec = {"semantics": {"language": "Python"}}
    (build / "spec.json").write_text(_j.dumps(spec))
    (build / "ll1.json").write_text("{}")
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: _MagicMock(returncode=0, stderr=b""),
    )
    fake_interp = _MagicMock()
    fake_interp.stdin = _MagicMock()
    fake_interp.stdout = io.BytesIO(_ready_record())
    fake_interp.wait = _MagicMock()
    monkeypatch.setattr("subprocess.Popen", lambda *a, **kw: fake_interp)
    monkeypatch.setattr(_rep_module, "SourceRunner",
                        lambda **kw: type("R", (), {"run": lambda self, s, h: True})())
    monkeypatch.setattr("plcc.cmd.rep.get_version", lambda: "1.2.3")
```

Also update `test_rep_main_default_prints_no_banner_to_stdout` which uses its own `Popen` stub — it currently only checks that make fails (returncode=1), which exits before `Popen` is called, so no change needed there.

Also update `test_main_constructs_runner_without_submit_mode` to give its `Popen` stub a stdout with the ready record:

```python
fake_interp = _MagicMock()
fake_interp.stdin = _MagicMock()
fake_interp.stdout = io.BytesIO(_ready_record())
fake_interp.wait = _MagicMock()
monkeypatch.setattr("subprocess.Popen", lambda *a, **kw: fake_interp)
```

- [ ] **Step 6: Run all rep tests**

```bash
bin/test/units.bash src/plcc/cmd/rep_test.py -v
```

Expected: all tests PASS

- [ ] **Step 7: Run the full unit suite**

```bash
bin/test/units.bash
```

Expected: all tests PASS (1147+ passed)

- [ ] **Step 8: Commit**

```bash
git add src/plcc/cmd/_test_helpers.py src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py
git commit -m "feat(rep): startup handshake, specification_error handling, clean error rendering"
```

---

## Self-Review

**Spec coverage:**
- Language Behavior / Syntax rejection: unchanged (existing pipeline `print_parse_error` path) ✓
- Language Behavior / Semantic rejection (`LanguageError`): Tasks 1–5 add `LanguageError` + template catch; Task 6 renders `{"kind": "error"}` as just `message` ✓
- Specification Error at startup (Python syntax): Task 6 `_wait_for_ready` catches EOF before REPL loop ✓
- Specification Error at runtime: Tasks 1–5 emit `specification_error` record; Task 6 handles it in `_render_record` ✓
- plcc-ng Error: Task 6 handles unknown record kinds ✓
- `plcc-make` failure: already handled by existing non-zero exit check ✓

**Placeholder scan:** No TBDs or TODOs. All steps include concrete code.

**Type consistency:**
- `_wait_for_ready(interpreter)` defined and called in Task 6 consistently.
- `_ready_record()` / `_specification_error_record()` defined in helpers and used in tests.
- `LanguageError` named consistently across all tasks (Python, JS, Java, Haskell).
- `{"kind": "specification_error"}` spelled consistently everywhere.
