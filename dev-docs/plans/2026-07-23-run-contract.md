# `_run()` Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `_run()` return a string, period, across Python, JavaScript, Java, and Haskell — with a runtime-enforced `specification_error` on violation — and document the contract everywhere a spec author or language-extension author would need it.

**Architecture:** Each language's runtime driver (`main.py.jinja`, `main.js.jinja`, `Main.java.jinja`) stops converting/coercing `_run()`'s return value and instead validates it is already a string, raising through the existing `specification_error` exception path if not. Each language's default `_Start._run()` changes from printing directly to returning. Java's `_run()` signature changes from `void` to `String`. Haskell needs no code change — it already satisfies the contract by compiler enforcement. Docs and the migration guide are updated to state the contract explicitly, including three `BREAKING CHANGE:` commits (Python, JavaScript, Java).

**Tech Stack:** Python (pytest, jinja2), JavaScript (Node.js), Java (JDK 21+, javac/reflection), Haskell (GHC/cabal, docs only), bats (CLI-level tests).

## Global Constraints

- Design of record: `dev-docs/specs/2026-07-23-issues-162-165-run-contract-design.md`. If anything here seems to contradict it, the spec wins — stop and reconcile before continuing.
- Java JDK 21+, Node.js 18+, Python 3.12+, GHC 9.4+/cabal 3.0+ — existing floors, unaffected by this work.
- Keep `bin/test/units.bash` green after every task — it is the fast pytest tier and the TDD inner loop for this repo.
- Tasks 1–3 are breaking changes. Each gets its own commit with `!` after the type **and** a `BREAKING CHANGE:` footer stating what broke and how to fix it, per `dev-docs/release-sop.md`. Do not squash them together — `python-semantic-release` needs one footer per language's actual break for a legible changelog.
- Never use `git commit --no-verify` or otherwise bypass hooks. If a hook fails, fix the underlying issue and recommit.
- Follow existing test-tier conventions from `CONTRIBUTING.md`: unit tests co-located as `<module>_test.py` next to the code (pytest, no subprocesses except where the existing suite already uses them for these `main.py`/`main.js` drivers); CLI-boundary behavior in `tests/bats/{commands,integration,e2e}/`.

---

### Task 1: Python — `_run()` returns a string, validated

**Files:**
- Modify: `src/plcc/lang/ext/python/emit.py:27-34` (default `_Start._run()`)
- Modify: `src/plcc/lang/ext/python/templates/main.py.jinja:21-29` (result handling)
- Modify: `src/plcc/lang/ext/python/emit_test.py` (fixture + new tests)
- Modify: `tests/fixtures/arith.plcc`, `tests/fixtures/trivial-python.plcc`, `tests/fixtures/trivial-arbno.plcc`

**Interfaces:**
- Produces: `main.py`'s result record is now `{"kind": "result", "value": <the exact string _run() returned>}` — no `repr()`/`str()` conversion applied. A non-`str` return raises `TypeError` inside the driver, caught by the existing generic handler, producing `{"kind": "specification_error", "type": "TypeError", "message": "_run() must return a string, got <type>"}`.

- [ ] **Step 1: Write the failing unit tests**

Open `src/plcc/lang/ext/python/emit_test.py`. Change the `_arith_model()` fixture's `Program` fragment (currently returns an `int`) to return a `str`, since that's what the new contract requires:

```python
def _arith_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None, "rule_name": "program",
             "fields": [{"name": "expr", "type": "Expr"}]},
            {"name": "Expr", "abstract": False, "extends": None, "rule_name": "Expr",
             "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
            {"name": "ExprRest", "abstract": True, "extends": None, "rule_name": "ExprRest",
             "fields": []},
            {"name": "AddRest", "abstract": False, "extends": "ExprRest", "rule_name": "ExprRest",
             "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
            {"name": "NilRest", "abstract": False, "extends": "ExprRest", "rule_name": "ExprRest",
             "fields": []},
            {"name": "Term", "abstract": False, "extends": None, "rule_name": "Term",
             "fields": [{"name": "num", "type": "Token"}]},
        ],
        "semantic_sections": [
            {
                "language": "Python",
                "fragments": [
                    {"class_name": "Program", "kind": "body", "body": "def _run(self):\n    return str(self.expr.eval())"},
                    {"class_name": "AddRest", "kind": "body", "body": "def eval(self, acc):\n    return self.rest.eval(acc + self.term.eval())"},
                    {"class_name": "NilRest", "kind": "body", "body": "def eval(self, acc):\n    return acc"},
                    {"class_name": "Term", "kind": "body", "body": "def eval(self):\n    return int(self.num.lexeme)"},
                    {"class_name": "Expr", "kind": "body", "body": "def eval(self):\n    return self.rest.eval(self.term.eval())"},
                ]
            }
        ]
    }
```

Then add three new tests at the end of the file:

```python
def test_default_run_returns_instead_of_printing(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    start_py = (tmp_path / '_Start.py').read_text()
    assert 'return str(self)' in start_py
    assert 'print(' not in start_py


def test_emit_generated_main_result_value_is_unquoted_string(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    tree_json = json.dumps({
        "kind": "tree",
        "rule": "program",
        "children": [
            ["expr", {
                "kind": "tree", "rule": "Expr", "children": [
                    ["term", {"kind": "tree", "rule": "Term", "children": [
                        ["num", {"kind": "token", "name": "NUM", "lexeme": "3"}]
                    ]}],
                    ["rest", {"kind": "tree", "rule": "ExprRest", "children": []}]
                ]
            }]
        ]
    })
    result = subprocess.run(
        [sys.executable, str(tmp_path / 'main.py')],
        input=tree_json + '\n',
        capture_output=True,
        text=True,
    )
    records = [json.loads(l) for l in result.stdout.splitlines() if l]
    result_records = [r for r in records if r.get('kind') == 'result']
    assert result_records, f"No result record found in: {result.stdout}"
    assert result_records[0]['value'] == '3'


def test_emit_generated_main_non_string_return_is_specification_error(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['fragments'][0] = {
        "class_name": "Program", "kind": "body",
        "body": "def _run(self):\n    return self.expr.eval()"
    }
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    tree_json = json.dumps({
        "kind": "tree",
        "rule": "program",
        "children": [
            ["expr", {
                "kind": "tree", "rule": "Expr", "children": [
                    ["term", {"kind": "tree", "rule": "Term", "children": [
                        ["num", {"kind": "token", "name": "NUM", "lexeme": "3"}]
                    ]}],
                    ["rest", {"kind": "tree", "rule": "ExprRest", "children": []}]
                ]
            }]
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
    assert 'must return a string' in spec_error_records[0]['message']
    assert result.returncode != 0
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `bin/test/units.bash src/plcc/lang/ext/python/emit_test.py -v`
Expected: `test_default_run_returns_instead_of_printing` FAILs (`_Start.py` still has `print(str(self))`); `test_emit_generated_main_result_value_is_unquoted_string` FAILs (`result_records[0]['value']` is `"'3'"`, not `'3'`, because of `repr()`); `test_emit_generated_main_non_string_return_is_specification_error` FAILs (no `specification_error` — today an `int` return is silently `repr()`'d and printed as a `result`, not rejected).

- [ ] **Step 3: Fix the default `_Start._run()`**

In `src/plcc/lang/ext/python/emit.py`, change:

```python
_START_PY = """\
import runtime.base as _plcc


class _Start(_plcc.Node):
    def _run(self):
        print(str(self))
"""
```

to:

```python
_START_PY = """\
import runtime.base as _plcc


class _Start(_plcc.Node):
    def _run(self):
        return str(self)
"""
```

- [ ] **Step 4: Fix the driver's result handling**

In `src/plcc/lang/ext/python/templates/main.py.jinja`, change:

```python
        try:
            tree = registry.deserialize(json.loads(line))
            result = tree.{{ entry_point }}()
            print(json.dumps({"kind": "result", "value": repr(result) if result is not None else None}), flush=True)
        except LanguageError as e:
```

to:

```python
        try:
            tree = registry.deserialize(json.loads(line))
            result = tree.{{ entry_point }}()
            if not isinstance(result, str):
                raise TypeError(f"{{ entry_point }}() must return a string, got {type(result).__name__}")
            print(json.dumps({"kind": "result", "value": result}), flush=True)
        except LanguageError as e:
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/python/emit_test.py -v`
Expected: all tests PASS, including the three new ones and every pre-existing test in the file (in particular `test_emit_generated_main_language_error_returns_error_record` and `test_emit_generated_main_other_exception_returns_specification_error`, which override `_run()` with error-raising bodies and are unaffected by this change).

- [ ] **Step 6: Fix the shared fixture files**

`tests/fixtures/arith.plcc` — change:
```
Program
%%%
def _run(self):
    return self.expr.eval()
%%%
```
to:
```
Program
%%%
def _run(self):
    return str(self.expr.eval())
%%%
```

`tests/fixtures/trivial-python.plcc` — change:
```
Program
%%%
def _run(self):
    return int(self.num.lexeme)
%%%
```
to:
```
Program
%%%
def _run(self):
    return str(int(self.num.lexeme))
%%%
```

`tests/fixtures/trivial-arbno.plcc` — change:
```
Program
%%%
def _run(self):
    return [e.eval() for e in self.rands.exprList]
%%%
```
to:
```
Program
%%%
def _run(self):
    return str([e.eval() for e in self.rands.exprList])
%%%
```

- [ ] **Step 7: Run the bats tiers that exercise these fixtures**

Run: `bin/test/commands.bash` (covers `tests/bats/commands/plcc-rep.bats`, which asserts `plcc-rep --spec=trivial-python.plcc` on input `42` prints `42` as the last line — unchanged, since `str(int("42"))` is still `"42"`)
Run: `bin/test/e2e.bash` (covers `tests/bats/e2e/plcc-rep.bats`'s arith.plcc batch/json tests and the three trivial-arbno.plcc tests expecting `[1, 2, 3]`, `[]`, `[42]` — unchanged, since `str([1, 2, 3])` is still `"[1, 2, 3]"`)
Run: `bin/test/integration.bash` (covers `tests/bats/integration/python-emit.bats`, which asserts the arith.plcc JSON output contains `"value"` and `'3'` — unchanged)
Expected: all PASS. If anything fails, read the exact diff between old and new fixture text again — the fix is always "wrap the existing return expression in `str(...)`", nothing else changes.

- [ ] **Step 8: Commit**

```bash
git add src/plcc/lang/ext/python/emit.py \
        src/plcc/lang/ext/python/templates/main.py.jinja \
        src/plcc/lang/ext/python/emit_test.py \
        tests/fixtures/arith.plcc \
        tests/fixtures/trivial-python.plcc \
        tests/fixtures/trivial-arbno.plcc
git commit -m "$(cat <<'EOF'
fix(python)!: _run() must return a str, or it's a specification error

The runtime no longer coerces _run()'s return value with repr()/str() —
it uses the returned string as-is, and validates it is actually a str
before doing so. This also fixes _run() returning a quoted string
(issue #162), which was a symptom of the same repr()-based coercion.
The default _Start._run() now returns str(self) instead of printing it.

BREAKING CHANGE: _run() (or a custom entry point) that returns a
non-str value — an int, a list, any object relied on for its __str__ —
now fails with a specification_error instead of silently working.
Convert the return value explicitly, e.g. `return str(x)` instead of
`return x`. Specs whose _run() already returns a str, or that never
define _run() at all, are unaffected.
EOF
)"
```

---

### Task 2: JavaScript — `_run()` returns a string, validated

**Files:**
- Modify: `src/plcc/lang/ext/javascript/emit.py:27-37` (default `_Start._run()`)
- Modify: `src/plcc/lang/ext/javascript/templates/main.js.jinja:20-35` (result handling)
- Modify: `src/plcc/lang/ext/javascript/emit_test.py` (fixture + new tests)

**Interfaces:**
- Produces: `main.js`'s result record is now `{"kind": "result", "value": <the exact string _run() returned>}` — no `String()` conversion applied. A non-`string` return throws inside the driver, caught by the existing catch block, producing `{"kind": "specification_error", "type": "Error", "message": "_run() must return a string, got <typeof>"}`.

- [ ] **Step 1: Write the failing unit tests**

Open `src/plcc/lang/ext/javascript/emit_test.py`. Change `_arith_model()`'s `Program` fragment (currently returns a `number`) to return a `string`:

```python
def _arith_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None,
             "rule_name": "program",
             "fields": [{"name": "expr", "type": "Expr"}]},
            {"name": "Expr", "abstract": False, "extends": None,
             "rule_name": "Expr",
             "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
            {"name": "ExprRest", "abstract": True, "extends": None,
             "rule_name": "ExprRest", "fields": []},
            {"name": "AddRest", "abstract": False, "extends": "ExprRest",
             "rule_name": "ExprRest",
             "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
            {"name": "NilRest", "abstract": False, "extends": "ExprRest",
             "rule_name": "ExprRest", "fields": []},
            {"name": "Term", "abstract": False, "extends": None,
             "rule_name": "Term",
             "fields": [{"name": "num", "type": "Token"}]},
        ],
        "semantic_sections": [
            {
                "language": "javascript",
                "fragments": [
                    {"class_name": "Program", "kind": "body",
                     "body": "_run() {\n    return String(this.expr.eval());\n}"},
                    {"class_name": "AddRest", "kind": "body",
                     "body": "eval(acc) {\n    return this.rest.eval(acc + this.term.eval());\n}"},
                    {"class_name": "NilRest", "kind": "body",
                     "body": "eval(acc) {\n    return acc;\n}"},
                    {"class_name": "Term", "kind": "body",
                     "body": "eval() {\n    return parseInt(this.num.lexeme);\n}"},
                    {"class_name": "Expr", "kind": "body",
                     "body": "eval() {\n    return this.rest.eval(this.term.eval());\n}"},
                ]
            }
        ]
    }
```

Then add three new tests at the end of the file:

```python
def test_default_run_returns_instead_of_printing(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    start_js = (tmp_path / '_Start.js').read_text()
    assert 'return String(this);' in start_js
    assert 'console.log' not in start_js


def test_emit_generated_main_result_value_is_unquoted_string(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    tree_json = json.dumps({
        "kind": "tree",
        "rule": "program",
        "children": [
            ["expr", {
                "kind": "tree", "rule": "Expr", "children": [
                    ["term", {"kind": "tree", "rule": "Term", "children": [
                        ["num", {"kind": "token", "name": "NUM", "lexeme": "3"}]
                    ]}],
                    ["rest", {"kind": "tree", "rule": "ExprRest", "children": []}]
                ]
            }]
        ]
    })
    result = subprocess.run(
        ['node', str(tmp_path / 'main.js')],
        input=tree_json + '\n',
        capture_output=True,
        text=True,
    )
    records = [json.loads(l) for l in result.stdout.splitlines() if l]
    result_records = [r for r in records if r.get('kind') == 'result']
    assert result_records, f"No result record found in: {result.stdout}"
    assert result_records[0]['value'] == '3'


def test_emit_generated_main_non_string_return_is_specification_error(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['fragments'][0] = {
        "class_name": "Program", "kind": "body",
        "body": "_run() {\n    return this.expr.eval();\n}"
    }
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    tree_json = json.dumps({
        "kind": "tree",
        "rule": "program",
        "children": [
            ["expr", {
                "kind": "tree", "rule": "Expr", "children": [
                    ["term", {"kind": "tree", "rule": "Term", "children": [
                        ["num", {"kind": "token", "name": "NUM", "lexeme": "3"}]
                    ]}],
                    ["rest", {"kind": "tree", "rule": "ExprRest", "children": []}]
                ]
            }]
        ]
    })
    result = subprocess.run(
        ['node', str(tmp_path / 'main.js')],
        input=tree_json + '\n',
        capture_output=True,
        text=True,
    )
    records = [json.loads(l) for l in result.stdout.splitlines() if l]
    spec_error_records = [r for r in records if r.get('kind') == 'specification_error']
    assert spec_error_records, f"No specification_error record found in: {result.stdout}"
    assert 'must return a string' in spec_error_records[0]['message']
    assert result.returncode != 0
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `bin/test/units.bash src/plcc/lang/ext/javascript/emit_test.py -v`
Expected: `test_default_run_returns_instead_of_printing` FAILs; `test_emit_generated_main_result_value_is_unquoted_string` FAILs or errors (the model's `_run()` now returns a string via `String(this.expr.eval())`, so this one may actually pass already — but `test_emit_generated_main_non_string_return_is_specification_error` FAILs, since today a `number` return is silently coerced via `String(result)` and printed as a `result`, not rejected).

- [ ] **Step 3: Fix the default `_Start._run()`**

In `src/plcc/lang/ext/javascript/emit.py`, change:

```python
_START_JS = """\
const { Node } = require('./runtime/base');

class _Start extends Node {
    _run() {
        console.log(String(this));
    }
}

module.exports = { _Start };
"""
```

to:

```python
_START_JS = """\
const { Node } = require('./runtime/base');

class _Start extends Node {
    _run() {
        return String(this);
    }
}

module.exports = { _Start };
"""
```

- [ ] **Step 4: Fix the driver's result handling**

In `src/plcc/lang/ext/javascript/templates/main.js.jinja`, change:

```js
    try {
        const tree = deserialize(JSON.parse(line), registry);
        const result = tree.{{ entry_point }}();
        console.log(JSON.stringify({ kind: 'result', value: result != null ? String(result) : null }));
    } catch (e) {
```

to:

```js
    try {
        const tree = deserialize(JSON.parse(line), registry);
        const result = tree.{{ entry_point }}();
        if (typeof result !== 'string') {
            throw new Error(`{{ entry_point }}() must return a string, got ${typeof result}`);
        }
        console.log(JSON.stringify({ kind: 'result', value: result }));
    } catch (e) {
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/javascript/emit_test.py -v`
Expected: all tests PASS, including the three new ones and every pre-existing test in the file.

- [ ] **Step 6: Run the broader tiers touching the JS driver**

Run: `bin/test/e2e.bash`
Expected: PASS (no `.plcc` fixture in `tests/fixtures/` targets JavaScript, so nothing else needs updating for this language).

- [ ] **Step 7: Commit**

```bash
git add src/plcc/lang/ext/javascript/emit.py \
        src/plcc/lang/ext/javascript/templates/main.js.jinja \
        src/plcc/lang/ext/javascript/emit_test.py
git commit -m "$(cat <<'EOF'
fix(javascript)!: _run() must return a string, or it's a specification error

The runtime no longer coerces _run()'s return value with String() — it
uses the returned string as-is, and validates it is actually a string
before doing so. The default _Start._run() now returns String(this)
instead of printing it.

BREAKING CHANGE: _run() (or a custom entry point) that returns a
non-string value — a number, an array, any object relied on for its
toString() — now fails with a specification_error instead of silently
working. Convert the return value explicitly, e.g. `return String(x)`
instead of `return x`. Specs whose _run() already returns a string, or
that never define _run() at all, are unaffected.
EOF
)"
```

---

### Task 3: Java — `_run()` signature changes from `void` to `String`

**Files:**
- Modify: `src/plcc/lang/ext/java/emit.py:27-33` (default `_Start._run()`)
- Modify: `src/plcc/lang/ext/java/templates/Main.java.jinja:24-32` (result handling)
- Modify: `src/plcc/lang/ext/java/emit_test.py` (fixture + updated + new tests)
- Modify: `tests/fixtures/trivial-java.plcc`
- Modify: `tests/bats/integration/java-emit.bats:42-45` (rename)

**Interfaces:**
- Produces: `Main.java`'s result record is now `{"kind": "result", "value": <the String _run() returned>}`. `_run()` returning `null` (the only way a `String`-declared method can violate the contract in Java) raises `IllegalStateException`, caught by the existing generic `catch (Exception e)`, producing `{"kind": "specification_error", "type": "IllegalStateException", "message": "_run() must return a string, got null"}`.

- [ ] **Step 1: Write the failing unit tests**

Open `src/plcc/lang/ext/java/emit_test.py`. Change `_trivial_model()`'s `Program` fragment (currently a `void`+`println` body) to return a `String`:

```python
def _trivial_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None, "rule_name": "program",
             "fields": [{"name": "expr", "type": "Expr", "is_list": False}]},
            {"name": "Expr", "abstract": True, "extends": None, "rule_name": "expr",
             "fields": []},
            {"name": "NumExpr", "abstract": False, "extends": "Expr", "rule_name": "expr",
             "fields": [{"name": "num", "type": "runtime.Token", "is_list": False}]},
        ],
        "semantic_sections": [
            {
                "language": "Java",
                "fragments": [
                    {"class_name": "Program", "kind": "body",
                     "body": "    public String _run() {\n        return expr.toString();\n    }"},
                ]
            }
        ]
    }
```

Update `test_start_java_uses_underscore_run` and the two tests asserting the old body text:

```python
def test_start_java_uses_underscore_run(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    start_java = (tmp_path / '_Start.java').read_text()
    assert 'public String _run()' in start_java
    assert '$run' not in start_java


def test_start_java_run_returns_instead_of_printing(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    start_java = (tmp_path / '_Start.java').read_text()
    assert 'return this.toString();' in start_java
    assert 'System.out.println' not in start_java
```

(Add `test_start_java_run_returns_instead_of_printing` as a new test right after `test_start_java_uses_underscore_run`.)

```python
def test_body_fragment_pasted_into_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_trivial_model())))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'return expr.toString();' in program_java
```

```python
def test_body_fragment_pasted_into_class_when_language_is_lowercase(tmp_path, monkeypatch):
    model = _trivial_model()
    model['semantic_sections'][0]['language'] = 'java'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    program_java = (tmp_path / 'Program.java').read_text()
    assert 'return expr.toString();' in program_java
```

Add one new test at the end of the file, asserting `Main.java` now validates the result is non-null:

```python
def test_main_java_validates_non_null_result(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    main_java = (tmp_path / 'Main.java').read_text()
    assert 'if (result == null)' in main_java
    assert 'must return a string' in main_java
```

- [ ] **Step 2: Run tests to verify the new/changed ones fail**

Run: `bin/test/units.bash src/plcc/lang/ext/java/emit_test.py -v`
Expected: `test_start_java_uses_underscore_run` FAILs (still `public void _run()`); `test_start_java_run_returns_instead_of_printing` FAILs; `test_body_fragment_pasted_into_class` and its lowercase variant FAIL (fixture text no longer matches old assertion, which was already changed in Step 1 — confirm they fail against unmodified `emit.py`/templates, not because the fixture itself is wrong); `test_main_java_validates_non_null_result` FAILs (no null check exists yet).

- [ ] **Step 3: Fix the default `_Start._run()`**

In `src/plcc/lang/ext/java/emit.py`, change:

```python
_START_JAVA = """\
public abstract class _Start extends runtime.Node {
    public void _run() {
        System.out.println(this.toString());
    }
}
"""
```

to:

```python
_START_JAVA = """\
public abstract class _Start extends runtime.Node {
    public String _run() {
        return this.toString();
    }
}
"""
```

- [ ] **Step 4: Fix the driver's result handling**

In `src/plcc/lang/ext/java/templates/Main.java.jinja`, change:

```java
                {{ start_class }} root = ({{ start_class }}) deserializer.deserialize(new JSONObject(line));
                java.lang.reflect.Method m = {{ start_class }}.class.getMethod("{{ entry_point }}");
                Object result = m.invoke(root);
                JSONObject record = new JSONObject();
                record.put("kind", "result");
                record.put("value", result != null ? result.toString() : JSONObject.NULL);
                System.out.println(record.toString());
                System.out.flush();
```

to:

```java
                {{ start_class }} root = ({{ start_class }}) deserializer.deserialize(new JSONObject(line));
                java.lang.reflect.Method m = {{ start_class }}.class.getMethod("{{ entry_point }}");
                Object result = m.invoke(root);
                if (result == null) {
                    throw new IllegalStateException("{{ entry_point }}() must return a string, got null");
                }
                JSONObject record = new JSONObject();
                record.put("kind", "result");
                record.put("value", result.toString());
                System.out.println(record.toString());
                System.out.flush();
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/java/emit_test.py -v`
Expected: all tests PASS.

- [ ] **Step 6: Fix the shared fixture file**

`tests/fixtures/trivial-java.plcc` — change:
```
Program
%%%
    public void _run() {
        System.out.println(num.toString());
    }
%%%
```
to:
```
Program
%%%
    public String _run() {
        return num.toString();
    }
%%%
```

- [ ] **Step 7: Rename the bats test that documents the old `void` behavior**

In `tests/bats/integration/java-emit.bats`, change:

```bash
@test "run outputs token lexeme from void _run()" {
    TREE='{"kind":"tree","rule":"Program","children":[["num",{"kind":"token","name":"NUM","lexeme":"99"}]]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [[ "$output" == *"99"* ]]
}
```

to:

```bash
@test "run outputs token lexeme from default _run()" {
    TREE='{"kind":"tree","rule":"Program","children":[["num",{"kind":"token","name":"NUM","lexeme":"99"}]]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [[ "$output" == *"99"* ]]
}
```

- [ ] **Step 8: Add a bats test proving `null` triggers `specification_error`**

In the same file, add a new test after "run outputs JSON result record":

```bash
@test "run reports specification_error when _run() returns null" {
    NULL_DIR="$(mktemp -d)"
    trap "rm -rf '${NULL_DIR}'" EXIT
    cat > "${NULL_DIR}/spec.plcc" << 'EOF'
token NUM '\d+'
skip SPACE '\s+'
%
<Program> ::= <NUM:num>
%
Java
Program
%%%
    public String _run() {
        return null;
    }
%%%
EOF
    plcc-spec "${NULL_DIR}/spec.plcc" | plcc-model | plcc-java-emit --output="${NULL_DIR}/out"
    plcc-java-build --output="${NULL_DIR}/out"
    TREE='{"kind":"tree","rule":"Program","children":[["num",{"kind":"token","name":"NUM","lexeme":"99"}]]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${NULL_DIR}/out'"
    [[ "$output" == *'"specification_error"'* ]]
    [[ "$output" == *'must return a string'* ]]
    [ "$status" -ne 0 ]
}
```

- [ ] **Step 9: Run the Java bats tiers**

Run: `bats tests/bats/integration/java-emit.bats` (skips cleanly if `javac` is unavailable, per the file's own `setup()` guard)
Expected: all PASS, including the renamed and new tests.
Run: `bin/test/integration.bash` and `bin/test/commands.bash` for full-tier confirmation.

- [ ] **Step 10: Commit**

```bash
git add src/plcc/lang/ext/java/emit.py \
        src/plcc/lang/ext/java/templates/Main.java.jinja \
        src/plcc/lang/ext/java/emit_test.py \
        tests/fixtures/trivial-java.plcc \
        tests/bats/integration/java-emit.bats
git commit -m "$(cat <<'EOF'
fix(java)!: _run() must return a String instead of void

_run() now returns a String that the runtime marshals into plcc-rep's
JSON result envelope, matching the return-and-convert contract already
used by Python, JavaScript, and Haskell. The previous void/print-inside-
_run() model silently bypassed the envelope and broke
`plcc-rep --format json`.

BREAKING CHANGE: Java's `_run()` signature changed from `public void
_run()` to `public String _run()`. Any spec that overrides `_run()` (or
a custom entry point) must change it to return a String instead of
printing directly — e.g. replace `System.out.println(x);` with
`return x.toString();`. Specs that never defined `_run()` are
unaffected; the default implementation was updated to match.
EOF
)"
```

---

### Task 4: Haskell — documentation consistency pass (no code change)

**Files:**
- Modify: `docs/language-guide/languages/haskell.md:115-129`

**Interfaces:**
- None — Haskell's `_run :: StartModule -> String` already satisfies the contract at compile time; the default `_run = show` already returns rather than prints. This task only aligns wording with the other three languages' rewritten sections (Task 5) so a reader comparing all four guides sees one consistent story.

- [ ] **Step 1: Update the wording**

In `docs/language-guide/languages/haskell.md`, change:

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
```

to:

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

The function signature must be `_run :: StartModule -> String`. `_run()` must return a string — same contract as every other language target — and the compiler enforces it: there is no way to write a Haskell `_run` that does anything else. The runtime sends the returned string to `plcc-rep` as the result, unmodified.

If you do not define `_run`, the default `_run = show` is injected, which returns the `Show` instance of the root node (not printed directly — `show` returns a `String`, matching the contract).
```

- [ ] **Step 2: Verify by reading the rendered section**

Run: `grep -n "must return a string" docs/language-guide/languages/haskell.md`
Expected: one match, in the paragraph just edited.

- [ ] **Step 3: Commit**

```bash
git add docs/language-guide/languages/haskell.md
git commit -m "$(cat <<'EOF'
docs(haskell): state the _run() contract explicitly for consistency

No behavior change — Haskell's _run :: StartModule -> String already
satisfies the same "returns a string" contract Python, JavaScript, and
Java now state explicitly (issues #162, #165). This aligns the wording
so a reader comparing all four language guides sees one consistent
story instead of Haskell's being implicit.
EOF
)"
```

---

### Task 5: Language guide and quick-start documentation updates

**Files:**
- Modify: `docs/language-guide/languages/python.md:105-116`
- Modify: `docs/language-guide/languages/javascript.md:118-130`
- Modify: `docs/language-guide/languages/java.md:43-50, 119-128`
- Modify: `docs/quick-start.md:66-76`

**Interfaces:**
- None — prose only. Every example shown must actually work as written (verify with the runtime code from Tasks 1–3), and every claim about the default must match the code as it now stands.

- [ ] **Step 1: Update `python.md`**

Change:

```
```python
Prog
%%%
def _run(self):
    # compute and return a value, or return None to produce no output
    return '\n'.join(str(exp.eval()) for exp in self.expList)
%%%
```

The return value is converted to a string and printed by `plcc-rep`. Return `None` to suppress output.

The default `_Start._run()` prints `str(self)`. Override it to replace the default behavior.
```

to:

```
```python
Prog
%%%
def _run(self):
    return '\n'.join(str(exp.eval()) for exp in self.expList)
%%%
```

`_run()` must return a `str`. The runtime sends that string to `plcc-rep` as-is — it is not converted or coerced. Returning anything else (an `int`, a `list`, `None`, ...) raises a `specification_error`; convert explicitly (`str(x)`) if needed.

Do not print or write to stdout from inside `_run()` — that bypasses `plcc-rep`'s JSON result envelope. Plain-text mode will still show what you printed, but `plcc-rep --verbose-format=json` will not.

The default `_Start._run()` returns `str(self)`. Override it to replace the default behavior.
```

- [ ] **Step 2: Update `javascript.md`**

Change:

```
```javascript
Prog
%%%
_run() {
    // Compute and return a value, or return undefined to produce no output.
    return this.expList.map(exp => String(exp.eval())).join('\n');
}
%%%
```

The return value is converted to a string and printed by `plcc-rep`. Return `undefined` (or nothing) to suppress output for that input.

The default `_Start._run()` prints `String(this)` to stdout. Override it to replace the default behavior entirely.
```

to:

```
```javascript
Prog
%%%
_run() {
    return this.expList.map(exp => String(exp.eval())).join('\n');
}
%%%
```

`_run()` must return a `string`. The runtime sends that string to `plcc-rep` as-is — it is not converted or coerced. Returning anything else (a `number`, an `array`, `undefined`, ...) raises a `specification_error`; convert explicitly (`String(x)`) if needed.

Do not print or write to stdout from inside `_run()` — that bypasses `plcc-rep`'s JSON result envelope. Plain-text mode will still show what you printed, but `plcc-rep --verbose-format=json` will not.

The default `_Start._run()` returns `String(this)`. Override it to replace the default behavior entirely.
```

- [ ] **Step 3: Update `java.md`'s quick reference example**

Change:

```
Prog
%%%
public void _run() {
    for (Exp exp : expList) {
        System.out.println(exp.eval());
    }
}
%%%
```
```

to:

```
Prog
%%%
public String _run() {
    java.util.List<String> lines = new java.util.ArrayList<>();
    for (Exp exp : expList) {
        lines.add(String.valueOf(exp.eval()));
    }
    return String.join("\n", lines);
}
%%%
```
```

(This preserves "Running this with `echo "1 + 2" | plcc-rep` prints `3`" immediately below it — a single-element `expList` produces `"3"` with no trailing newline, same as the Python/JS examples' `\n.join`-style output.)

- [ ] **Step 4: Update `java.md`'s `_run` entry point section**

Change:

```
```java
Prog
%%%
public void _run() {
    // your implementation
}
%%%
```

The default `_Start._run()` prints `String(this)` using `System.out.println`. Override it to replace the default behavior. Return type is `void`.
```

to:

```
```java
Prog
%%%
public String _run() {
    // your implementation
}
%%%
```

`_run()` must return a `String`. The runtime sends that string to `plcc-rep` as-is — it is not converted or coerced. Returning `null` raises a `specification_error`.

Do not print or write to stdout from inside `_run()` — that bypasses `plcc-rep`'s JSON result envelope. Plain-text mode will still show what you printed, but `plcc-rep --verbose-format=json` will not.

The default `_Start._run()` returns `this.toString()`. Override it to replace the default behavior.
```

- [ ] **Step 5: Update `docs/quick-start.md`'s Java example**

Change:

```
    Program
    %%%
    public void _run() {
        int sum = 0;
        for (NUM num : numList) {
            sum += Integer.parseInt(num.lexeme);
        }
        System.out.println(sum);
    }
    %%%
    ```
```

to:

```
    Program
    %%%
    public String _run() {
        int sum = 0;
        for (NUM num : numList) {
            sum += Integer.parseInt(num.lexeme);
        }
        return String.valueOf(sum);
    }
    %%%
    ```
```

- [ ] **Step 6: Verify the examples actually work**

Run each doc's example spec through the real pipeline to prove the rewritten code compiles/runs and produces the documented output:

```bash
mkdir -p /tmp/run-contract-doc-check && cd /tmp/run-contract-doc-check

cat > java-quickstart.plcc << 'EOF'
skip  WHITESPACE '\s+'
token NUM '\d+'
%
<Program> **= <NUM:num>
%
Java

Program
%%%
public String _run() {
    int sum = 0;
    for (NUM num : numList) {
        sum += Integer.parseInt(num.lexeme);
    }
    return String.valueOf(sum);
}
%%%
EOF
echo "42 36 2" | plcc-rep --spec=java-quickstart.plcc
# Expected output: 80

cat > java-guide.plcc << 'EOF'
token NUM   '\d+'
token PLUS  '\+'
skip  SPACE '\s+'
%
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
%
Java

Exp
%%%
public abstract int eval();
%%%

Prog
%%%
public String _run() {
    java.util.List<String> lines = new java.util.ArrayList<>();
    for (Exp exp : expList) {
        lines.add(String.valueOf(exp.eval()));
    }
    return String.join("\n", lines);
}
%%%

AddExp
%%%
public int eval() {
    return left.eval() + right.eval();
}
%%%

NumExp
%%%
public int eval() {
    return Integer.parseInt(num.lexeme);
}
%%%
EOF
echo "1 + 2" | plcc-rep --spec=java-guide.plcc
# Expected output: 3

cd - && rm -rf /tmp/run-contract-doc-check
```

Expected: both print exactly the documented output, with no extra blank line.

- [ ] **Step 7: Commit**

```bash
git add docs/language-guide/languages/python.md \
        docs/language-guide/languages/javascript.md \
        docs/language-guide/languages/java.md \
        docs/quick-start.md
git commit -m "$(cat <<'EOF'
docs: state the _run() return-a-string contract explicitly

Python, JavaScript, and Java's language guides described the return
value as merely "converted to a string" and, for Java, showed a void
method that prints directly — both now superseded by issues #162/#165.
State the actual contract plainly: _run() must return a string, the
runtime does not convert or print for you, and a non-string return (or,
for Java, null) is a specification_error. Update every code example and
the quick-start Java example to match the new String-returning
signature.
EOF
)"
```

---

### Task 6: Language-extension protocol doc + migration guide

**Files:**
- Modify: `docs/cli/guide/language-extensions.md` (append new section)
- Modify: `docs/migration.md:7-31, 141-149`

**Interfaces:**
- None — prose only.

- [ ] **Step 1: Add the `_run()` protocol section to `language-extensions.md`**

Append to the end of `docs/cli/guide/language-extensions.md` (after the `plcc-haskell` section):

```

## The `_run()` protocol

Every language extension's `main`/entry-point driver must implement the same
contract for the root node's entry point method (`_run()` by default, or a
custom name from `entry_point`):

- It **returns a string**. The driver marshals it into a
  `{"kind": "result", "value": "<string>"}` JSON record on stdout for
  `plcc-rep` to read and print — it does not print or convert the value
  itself.
- If it returns anything other than a string (or, for statically-typed
  languages, if the call otherwise fails to produce one — e.g. Java's
  reflection returning `null`), the driver raises a `specification_error`.
  It must never let a wrong-typed value flow into the `value` field
  silently.
- The entry-point implementation itself must never write to stdout. Doing
  so bypasses the JSON envelope entirely; plain-text `plcc-rep` sessions
  will still show it (by accident, since unparseable lines are echoed
  as-is), but `plcc-rep --verbose-format=json` will not.

This is what lets `plcc-rep --verbose-format=json` show a real, structured
record for every result, regardless of which language emitted the
interpreter. A new language extension must follow it to interoperate
correctly with `plcc-rep`.
```

- [ ] **Step 2: Update `migration.md`'s "Breaking behavior changes" section**

After the existing `plcc-scan` output-format bullet and before `## Migration checklist`, add:

```

**The `_run()` entry point must return a string.** This applies whether
you're migrating an old `$run()` or have already ported to `_run()`. Java's
`_run()` changed from `void` (print inside the method) to `String` (return
the text) — a spec with `public void _run() { System.out.println(...); }`
will fail to compile and must become
`public String _run() { return ...; }`. Python and JavaScript's `_run()`
must now return an actual `str`/`string` — a `_run()` that returns a
non-string value (an `int`, a `list`, a bare number, ...) now fails with a
`specification_error` instead of silently working; convert explicitly
(`str(x)` / `String(x)`) if needed. No language's `_run()` may print or
write to stdout directly — only plain-text `plcc-rep` sessions tolerated
that before, and only by accident.
```

- [ ] **Step 3: Update `migration.md` §9**

Change:

```
### 9. Rename the entry point method

The method the start symbol's class uses as its execution entry point was renamed.

| PLCC | PLCC-ng |
|---|---|
| `$run()` | `_run()` |

Update this in the semantic section of your spec file.
```

to:

```
### 9. Rename the entry point method

The method the start symbol's class uses as its execution entry point was
renamed — and its contract changed, not just its name.

| PLCC | PLCC-ng |
|---|---|
| `$run()` | `_run()` |

`$run()` was `void`; it printed its output directly. `_run()` must
**return** a string — the runtime prints it for you. See "Breaking
behavior changes" above for what this means for each language.

Update this in the semantic section of your spec file.
```

- [ ] **Step 4: Verify by grep**

Run: `grep -n "must return a string\|_run() entry point must return" docs/migration.md docs/cli/guide/language-extensions.md`
Expected: matches in both files, in the sections just added.

- [ ] **Step 5: Commit**

```bash
git add docs/cli/guide/language-extensions.md docs/migration.md
git commit -m "$(cat <<'EOF'
docs: document the _run() protocol obligation and its migration impact

Adds the _run() contract to language-extensions.md as an explicit
obligation on any language extension (existing or future) — the
natural home for it, since it's the closest thing this repo has to a
language-extension contract doc. Updates migration.md's breaking-
changes section and its $run()-to-_run() rename entry (§9) to state
that the contract changed, not just the name — closing the gap
identified in issue #165.
EOF
)"
```

---

### Task 7: Cross-cutting integration test — default `_run()` under `--verbose-format=json`

**Files:**
- Modify: `tests/bats/e2e/plcc-rep.bats` (append new test)

**Interfaces:**
- None — this is the regression guard for the core bug in issue #165: before Tasks 1–3, a spec relying on the default `_run()` produced a no-op `{"kind": "result", "value": null}` record under `--verbose-format=json` while silently working in plain-text mode. This test proves both modes now agree.

- [ ] **Step 1: Write the failing test**

Append to `tests/bats/e2e/plcc-rep.bats`:

```bash
@test "plcc-rep --verbose-format=json shows a real value for the default _run()" {
    cat > spec.plcc << 'EOF'
token NUM '\d+'
skip WS '\s+'
%
<Program> ::= <NUM:num>
%
Python
EOF
    text_output=$(echo '42' | plcc-rep --spec=spec.plcc)
    run --separate-stderr bash -c "echo '42' | plcc-rep --verbose-format=json --spec=spec.plcc"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"result"'* ]]
    [[ "$output" != *'"value": null'* ]]
    [[ "$output" == *"${text_output}"* ]]
}
```

- [ ] **Step 2: Run the test against the pre-Task-1 driver to confirm it would have failed**

This step is a sanity check on the test's design, not something to actually execute against reverted code — reason about it instead: before Task 1's fix, the spec above has no `_run()` override, so the default `_Start._run()` printed `str(self)` directly and returned `None`. Plain-text mode would show the printed line (`text_output` non-empty); JSON mode would show `{"kind": "result", "value": null}` — so `[[ "$output" != *'"value": null'* ]]` would FAIL and `[[ "$output" == *"${text_output}"* ]]` would also FAIL, since `text_output` (the raw printed address-like string) never appears inside the JSON-mode output at all. This confirms the test actually exercises the bug.

- [ ] **Step 3: Run the test against the current (post-Task-1) code**

Run: `bats tests/bats/e2e/plcc-rep.bats`
Expected: PASS — with Task 1 already landed, the default `_Start._run()` returns `str(self)`, so both plain-text and JSON modes now derive from the same returned string.

- [ ] **Step 4: Run the full e2e tier**

Run: `bin/test/e2e.bash`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/bats/e2e/plcc-rep.bats
git commit -m "$(cat <<'EOF'
test(rep): prove --verbose-format=json shows real output for default _run()

Closes the coverage gap identified while designing issues #162/#165:
no existing test proved that a spec relying on the default _run()
produces a real (non-null) JSON result record. Before the Task 1 fix,
this scenario silently produced {"kind": "result", "value": null} under
--verbose-format=json while plain-text mode showed real (if useless)
output — the two modes disagreeing was the whole bug.
EOF
)"
```

---

## Final Verification

- [ ] Run `bin/test/functional.bash` (units + commands + integration + e2e) and confirm everything is green.
- [ ] Run `bin/issues/check.bash` to confirm the issue/roadmap bookkeeping is still consistent (this plan doesn't close #162/#165 itself — do that with `bin/issues/close.bash 162` and `bin/issues/close.bash 165` in the branch's final commit, per `dev-docs/issue-conventions.md`, once this work is merged).
