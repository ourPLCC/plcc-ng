# JavaScript Emitter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a JavaScript (Node.js/CommonJS) language backend to plcc-ng, mirroring the structure of the existing `python` and `java` extensions.

**Architecture:** A new extension at `src/plcc/lang/ext/javascript/` containing a Python emitter (`emit.py`) that reads model JSON from stdin and writes CommonJS `.js` files using Jinja2 templates, a runner (`run.py`) that invokes `node main.js`, and a runtime library (`runtime/`) that is copied into the output directory. Tests at every layer: Python pytest tests for the emitter and runner, and pytest+subprocess tests for the JavaScript runtime modules.

**Tech Stack:** Python (emitter/runner/tests), Jinja2 (templates), Node.js/CommonJS (generated code and runtime), pytest + subprocess (runtime testing).

## Global Constraints

- All generated JavaScript uses CommonJS (`require`/`module.exports`) — no ESM, no `package.json` in the output dir
- Spec section tag: `javascript` (case-insensitive match)
- CLI entry points: `plcc-javascript-emit`, `plcc-javascript-run` — no `plcc-javascript-build`
- Fragment kinds supported: `top`, `import`, `init`, `body`, `file` — no `class` (JS has no interfaces or multiple inheritance)
- Abstract classes: no `_RULE_NAME`, `_FIELDS`, or constructor in generated output
- Start class with no explicit `extends` gets `extends _Start`; `_Start.js` always written to output
- Runtime test files (`*_test.py`) are excluded when copying the runtime dir
- Entry point method: `_run`
- Follow `src/plcc/lang/ext/python/emit_test.py` as the testing style reference

---

## File Map

**New files — extension:**
- `src/plcc/lang/ext/javascript/__init__.py` — empty package marker
- `src/plcc/lang/ext/javascript/emit.py` — reads model JSON, writes `.js` files via Jinja2
- `src/plcc/lang/ext/javascript/emit_test.py` — pytest tests for the emitter
- `src/plcc/lang/ext/javascript/run.py` — invokes `node main.js`
- `src/plcc/lang/ext/javascript/run_test.py` — pytest tests for the runner

**New files — templates:**
- `src/plcc/lang/ext/javascript/templates/class_file.js.jinja` — per-class file template
- `src/plcc/lang/ext/javascript/templates/main.js.jinja` — entry-point template

**New files — runtime (JS):**
- `src/plcc/lang/ext/javascript/runtime/base.js` — `Node` and `Token` classes
- `src/plcc/lang/ext/javascript/runtime/registry.js` — `Registry` class
- `src/plcc/lang/ext/javascript/runtime/deserialize.js` — `deserialize` function

**New files — runtime tests (Python):**
- `src/plcc/lang/ext/javascript/runtime/base_test.py`
- `src/plcc/lang/ext/javascript/runtime/registry_test.py`
- `src/plcc/lang/ext/javascript/runtime/deserialize_test.py`

**Modified files:**
- `pyproject.toml` — add two `[project.scripts]` entries (Task 5)

---

## Task 1: Runtime base.js

Scaffold the extension directory and implement `Node` and `Token`.

**Files:**
- Create: `src/plcc/lang/ext/javascript/__init__.py`
- Create: `src/plcc/lang/ext/javascript/runtime/base.js`
- Create: `src/plcc/lang/ext/javascript/runtime/base_test.py`

**Interfaces:**
- Produces: `Node` (empty base class), `Token(kind, lexeme)` with `.toString()` returning lexeme — both exported via `module.exports = { Node, Token }`

- [ ] **Step 1: Create the extension package**

```bash
mkdir -p src/plcc/lang/ext/javascript/runtime
mkdir -p src/plcc/lang/ext/javascript/templates
touch src/plcc/lang/ext/javascript/__init__.py
```

- [ ] **Step 2: Write the failing tests**

Create `src/plcc/lang/ext/javascript/runtime/base_test.py`:

```python
import subprocess
from pathlib import Path

RUNTIME_DIR = Path(__file__).parent


def _node(code):
    return subprocess.run(
        ['node', '-e', code],
        capture_output=True, text=True,
        cwd=str(RUNTIME_DIR),
    )


def test_node_is_a_class():
    r = _node("const { Node } = require('./base'); console.log(new Node() instanceof Node);")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true'


def test_token_stores_kind_and_lexeme():
    r = _node("const { Token } = require('./base'); const t = new Token('NUM', '42'); console.log(t.kind, t.lexeme);")
    assert r.returncode == 0
    assert r.stdout.strip() == 'NUM 42'


def test_token_tostring_returns_lexeme():
    r = _node("const { Token } = require('./base'); const t = new Token('NUM', '42'); console.log(String(t));")
    assert r.returncode == 0
    assert r.stdout.strip() == '42'


def test_token_is_not_a_node():
    r = _node("const { Node, Token } = require('./base'); console.log(new Token('X', 'x') instanceof Node);")
    assert r.returncode == 0
    assert r.stdout.strip() == 'false'
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/runtime/base_test.py -v
```

Expected: 4 failures mentioning `Cannot find module './base'`

- [ ] **Step 4: Implement base.js**

Create `src/plcc/lang/ext/javascript/runtime/base.js`:

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

module.exports = { Node, Token };
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/runtime/base_test.py -v
```

Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/javascript/
git commit -m "feat(javascript): scaffold extension and add runtime base.js"
```

---

## Task 2: Runtime registry.js

**Files:**
- Create: `src/plcc/lang/ext/javascript/runtime/registry.js`
- Create: `src/plcc/lang/ext/javascript/runtime/registry_test.py`

**Interfaces:**
- Consumes: nothing from earlier tasks
- Produces: `Registry` class — `register(...classes)` reads `cls._RULE_NAME` and `cls._FIELDS`; `lookup(ruleName, fieldNames)` returns the matching class or throws; exported via `module.exports = { Registry }`

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/lang/ext/javascript/runtime/registry_test.py`:

```python
import subprocess
from pathlib import Path

RUNTIME_DIR = Path(__file__).parent


def _node(code):
    return subprocess.run(
        ['node', '-e', code],
        capture_output=True, text=True,
        cwd=str(RUNTIME_DIR),
    )


def test_register_and_lookup_by_rule_and_fields():
    r = _node("""
const { Registry } = require('./registry');
class Foo { static _RULE_NAME = 'foo'; static _FIELDS = ['x', 'y']; }
const reg = new Registry();
reg.register(Foo);
console.log(reg.lookup('foo', ['x', 'y']) === Foo);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true'


def test_lookup_unknown_rule_throws():
    r = _node("""
const { Registry } = require('./registry');
const reg = new Registry();
try { reg.lookup('missing', []); console.log('no error'); }
catch(e) { console.log('threw'); }
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'threw'


def test_lookup_wrong_fields_throws():
    r = _node("""
const { Registry } = require('./registry');
class Foo { static _RULE_NAME = 'foo'; static _FIELDS = ['x']; }
const reg = new Registry();
reg.register(Foo);
try { reg.lookup('foo', ['y']); console.log('no error'); }
catch(e) { console.log('threw'); }
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'threw'


def test_field_order_does_not_matter():
    r = _node("""
const { Registry } = require('./registry');
class Foo { static _RULE_NAME = 'foo'; static _FIELDS = ['x', 'y']; }
const reg = new Registry();
reg.register(Foo);
console.log(reg.lookup('foo', ['y', 'x']) === Foo);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true'


def test_two_classes_same_rule_different_fields():
    r = _node("""
const { Registry } = require('./registry');
class A { static _RULE_NAME = 'r'; static _FIELDS = ['x']; }
class B { static _RULE_NAME = 'r'; static _FIELDS = ['x', 'y']; }
const reg = new Registry();
reg.register(A, B);
console.log(reg.lookup('r', ['x']) === A, reg.lookup('r', ['x', 'y']) === B);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true true'
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/runtime/registry_test.py -v
```

Expected: 5 failures mentioning `Cannot find module './registry'`

- [ ] **Step 3: Implement registry.js**

Create `src/plcc/lang/ext/javascript/runtime/registry.js`:

```javascript
class Registry {
    constructor() {
        this._byRule = {};
    }

    register(...classes) {
        for (const cls of classes) {
            const ruleName = cls._RULE_NAME;
            const key = JSON.stringify([...cls._FIELDS].sort());
            if (!this._byRule[ruleName]) {
                this._byRule[ruleName] = {};
            }
            this._byRule[ruleName][key] = cls;
        }
    }

    lookup(ruleName, fieldNames) {
        const candidates = this._byRule[ruleName];
        if (!candidates) {
            throw new Error(`No class registered for rule '${ruleName}'`);
        }
        const key = JSON.stringify([...fieldNames].sort());
        const cls = candidates[key];
        if (!cls) {
            throw new Error(`No class for rule '${ruleName}' with fields [${[...fieldNames].join(', ')}]`);
        }
        return cls;
    }
}

module.exports = { Registry };
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/runtime/registry_test.py -v
```

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/ext/javascript/runtime/registry.js src/plcc/lang/ext/javascript/runtime/registry_test.py
git commit -m "feat(javascript): add runtime registry.js"
```

---

## Task 3: Runtime deserialize.js

**Files:**
- Create: `src/plcc/lang/ext/javascript/runtime/deserialize.js`
- Create: `src/plcc/lang/ext/javascript/runtime/deserialize_test.py`

**Interfaces:**
- Consumes: `Token` from `./base`; `Registry.lookup` from Task 2
- Produces: `deserialize(tree, registry)` — returns a `Token` for `{kind: 'token', ...}` nodes, or a class instance for rule nodes; exported via `module.exports = { deserialize }`

Tree format (from model JSON produced by `plcc-model`):
- Token node: `{ kind: 'token', name: 'TOKNAME', lexeme: 'text' }`
- Rule node: `{ kind: 'rule', rule: 'ruleName', children: [['fieldName', value], ...] }`
- `value` is a token node, a rule node, or an array of either

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/lang/ext/javascript/runtime/deserialize_test.py`:

```python
import subprocess
from pathlib import Path

RUNTIME_DIR = Path(__file__).parent


def _node(code):
    return subprocess.run(
        ['node', '-e', code],
        capture_output=True, text=True,
        cwd=str(RUNTIME_DIR),
    )


def test_deserialize_token_node():
    r = _node("""
const { deserialize } = require('./deserialize');
const { Token } = require('./base');
const t = deserialize({ kind: 'token', name: 'NUM', lexeme: '42' }, null);
console.log(t instanceof Token, t.kind, t.lexeme);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true NUM 42'


def test_deserialize_rule_node_with_token_field():
    r = _node("""
const { deserialize } = require('./deserialize');
const { Registry } = require('./registry');
const { Token } = require('./base');
class Num {
    static _RULE_NAME = 'num'; static _FIELDS = ['val'];
    constructor(val) { this.val = val; }
}
const reg = new Registry(); reg.register(Num);
const node = deserialize({
    kind: 'rule', rule: 'num',
    children: [['val', { kind: 'token', name: 'INT', lexeme: '5' }]]
}, reg);
console.log(node instanceof Num, node.val instanceof Token, node.val.lexeme);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true true 5'


def test_deserialize_nested_rule_nodes():
    r = _node("""
const { deserialize } = require('./deserialize');
const { Registry } = require('./registry');
class Inner {
    static _RULE_NAME = 'inner'; static _FIELDS = [];
    constructor() {}
}
class Outer {
    static _RULE_NAME = 'outer'; static _FIELDS = ['inner'];
    constructor(inner) { this.inner = inner; }
}
const reg = new Registry(); reg.register(Inner, Outer);
const node = deserialize({
    kind: 'rule', rule: 'outer',
    children: [['inner', { kind: 'rule', rule: 'inner', children: [] }]]
}, reg);
console.log(node instanceof Outer, node.inner instanceof Inner);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true true'


def test_deserialize_list_field():
    r = _node("""
const { deserialize } = require('./deserialize');
const { Registry } = require('./registry');
const { Token } = require('./base');
class Lst {
    static _RULE_NAME = 'lst'; static _FIELDS = ['items'];
    constructor(items) { this.items = items; }
}
const reg = new Registry(); reg.register(Lst);
const node = deserialize({
    kind: 'rule', rule: 'lst',
    children: [['items', [
        { kind: 'token', name: 'N', lexeme: '1' },
        { kind: 'token', name: 'N', lexeme: '2' },
    ]]]
}, reg);
console.log(Array.isArray(node.items), node.items.length, node.items[0].lexeme);
""")
    assert r.returncode == 0
    assert r.stdout.strip() == 'true 2 1'
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/runtime/deserialize_test.py -v
```

Expected: 4 failures mentioning `Cannot find module './deserialize'`

- [ ] **Step 3: Implement deserialize.js**

Create `src/plcc/lang/ext/javascript/runtime/deserialize.js`:

```javascript
const { Token } = require('./base');

function deserialize(tree, registry) {
    if (tree.kind === 'token') {
        return new Token(tree.name, tree.lexeme);
    }
    const children = tree.children || [];
    const fieldNames = children.map(([name]) => name);
    const cls = registry.lookup(tree.rule, fieldNames);
    const args = children.map(([, val]) => _deserializeValue(val, registry));
    return new cls(...args);
}

function _deserializeValue(val, registry) {
    if (Array.isArray(val)) {
        return val.map(item => _deserializeValue(item, registry));
    }
    if (val && typeof val === 'object' && val.kind === 'token') {
        return new Token(val.name, val.lexeme);
    }
    if (val && typeof val === 'object') {
        return deserialize(val, registry);
    }
    return val;
}

module.exports = { deserialize };
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/runtime/deserialize_test.py -v
```

Expected: 4 passed

- [ ] **Step 5: Run all runtime tests together**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/runtime/ -v
```

Expected: 13 passed

- [ ] **Step 6: Commit**

```bash
git add src/plcc/lang/ext/javascript/runtime/deserialize.js src/plcc/lang/ext/javascript/runtime/deserialize_test.py
git commit -m "feat(javascript): add runtime deserialize.js"
```

---

## Task 4: Templates + emit.py

**Files:**
- Create: `src/plcc/lang/ext/javascript/templates/class_file.js.jinja`
- Create: `src/plcc/lang/ext/javascript/templates/main.js.jinja`
- Create: `src/plcc/lang/ext/javascript/emit.py`
- Create: `src/plcc/lang/ext/javascript/emit_test.py`

**Interfaces:**
- Consumes: runtime files from Tasks 1–3 (copied to output dir by `_copy_runtime`)
- Produces: `plcc.lang.ext.javascript.emit:main` — reads model JSON from stdin, writes `<ClassName>.js`, `_Start.js`, `main.js`, and `runtime/` to `--output` dir

Model JSON schema (what `plcc-model` produces, passed via stdin):
```json
{
  "start": "program",
  "classes": [
    {
      "name": "Program",
      "abstract": false,
      "extends": null,
      "rule_name": "program",
      "fields": [{"name": "expr", "type": "Expr"}]
    }
  ],
  "semantic_sections": [
    {
      "language": "javascript",
      "fragments": [
        {"class_name": "Program", "kind": "body", "body": "method() {}"}
      ]
    }
  ]
}
```

- [ ] **Step 1: Write the failing emit tests**

Create `src/plcc/lang/ext/javascript/emit_test.py`:

```python
import io
import json
import os
import signal
import subprocess
import sys
import time

import pytest
from docopt import DocoptExit

from .emit import main as run_main


def _minimal_model():
    return {
        "start": "program",
        "classes": [
            {"name": "Program", "abstract": False, "extends": None,
             "fields": [], "rule_name": "program"},
        ],
        "semantic_sections": [],
    }


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
                     "body": "_run() {\n    return this.expr.eval();\n}"},
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


def test_no_args_prints_usage():
    with pytest.raises((DocoptExit, SystemExit)):
        run_main([])


def test_emit_generates_start_js(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / '_Start.js').exists()


def test_start_class_extends_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Program.js').read_text()
    assert "require('./_Start')" in content
    assert 'class Program extends _Start' in content


def test_start_class_with_explicit_parent_does_not_get_start(tmp_path, monkeypatch):
    model = _minimal_model()
    model['classes'][0]['extends'] = 'SomeBase'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Program.js').read_text()
    assert '_Start' not in content


def test_non_start_class_does_not_extend_start(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Term.js').read_text()
    assert '_Start' not in content


def test_emit_produces_one_js_file_per_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    for name in ["Program", "Expr", "ExprRest", "AddRest", "NilRest", "Term"]:
        assert (tmp_path / f'{name}.js').exists(), f'{name}.js missing'


def test_emit_produces_main_js(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'main.js').exists()


def test_emit_copies_runtime_directory(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_minimal_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'runtime' / 'base.js').exists()
    assert (tmp_path / 'runtime' / 'registry.js').exists()
    assert (tmp_path / 'runtime' / 'deserialize.js').exists()
    assert not (tmp_path / 'runtime' / 'base_test.py').exists()


def test_concrete_class_has_rule_name_and_fields(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Term.js').read_text()
    assert '_RULE_NAME' in content
    assert '_FIELDS' in content
    assert 'constructor' in content


def test_abstract_class_has_no_rule_name_or_constructor(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'ExprRest.js').read_text()
    assert '_RULE_NAME' not in content
    assert '_FIELDS' not in content
    assert 'constructor' not in content


def test_subclass_requires_parent(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'AddRest.js').read_text()
    assert "require('./ExprRest')" in content
    assert 'class AddRest extends ExprRest' in content


def test_body_fragment_placed_in_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Term.js').read_text()
    assert 'eval()' in content
    assert 'parseInt(this.num.lexeme)' in content


def test_top_fragment_placed_before_requires(tmp_path, monkeypatch):
    model = _minimal_model()
    model['semantic_sections'] = [{"language": "javascript", "fragments": [
        {"class_name": "Program", "kind": "top", "body": "'use strict';"}
    ]}]
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Program.js').read_text()
    assert content.index("'use strict';") < content.index("require(")


def test_import_fragment_placed_before_class(tmp_path, monkeypatch):
    model = _minimal_model()
    model['semantic_sections'] = [{"language": "javascript", "fragments": [
        {"class_name": "Program", "kind": "import", "body": "const fs = require('fs');"}
    ]}]
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Program.js').read_text()
    assert content.index("const fs = require('fs');") < content.index('class Program')


def test_init_fragment_placed_in_constructor(tmp_path, monkeypatch):
    model = _minimal_model()
    model['classes'][0]['fields'] = [{"name": "x", "type": "Token"}]
    model['semantic_sections'] = [{"language": "javascript", "fragments": [
        {"class_name": "Program", "kind": "init", "body": "this.extra = 42;"}
    ]}]
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Program.js').read_text()
    ctor_start = content.index('constructor(')
    ctor_end = content.index('}', ctor_start)
    ctor_body = content[ctor_start:ctor_end]
    assert 'this.extra = 42;' in ctor_body


def test_file_fragment_replaces_entire_file(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Env", "kind": "file", "body": "class Env {}\nmodule.exports = { Env };\n"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Env.js').read_text()
    assert content == "class Env {}\nmodule.exports = { Env };\n"


def test_language_tag_is_case_insensitive(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['language'] = 'JavaScript'
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'Term.js').read_text()
    assert 'parseInt(this.num.lexeme)' in content


def test_emit_generated_main_is_runnable(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    result = subprocess.run(
        ['node', str(tmp_path / 'main.js')],
        input='', capture_output=True, text=True,
    )
    assert result.returncode == 0


def test_emit_generated_main_exits_130_on_sigint(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    env = {k: v for k, v in os.environ.items() if not k.startswith('COV_CORE')}
    proc = subprocess.Popen(
        ['node', str(tmp_path / 'main.js')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env,
    )
    time.sleep(0.1)
    proc.send_signal(signal.SIGINT)
    try:
        stdout, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        pytest.fail("subprocess did not exit after SIGINT within 5 seconds")
    assert proc.returncode == 130
    assert b'Traceback' not in stderr
    assert b'User interrupted execution by ^C.' in stdout
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/emit_test.py -v
```

Expected: all failures mentioning `cannot import name 'main' from 'plcc.lang.ext.javascript.emit'`

- [ ] **Step 3: Create the Jinja2 class template**

Create `src/plcc/lang/ext/javascript/templates/class_file.js.jinja`:

```jinja2
{% for frag in top_fragments %}{{ frag.body }}
{% endfor %}const { Node, Token } = require('./runtime/base');
{% if cls.extends %}const { {{ cls.extends }} } = require('./{{ cls.extends }}');
{% endif %}{% for frag in import_fragments %}{{ frag.body }}
{% endfor %}
class {{ cls.name }} extends {% if cls.extends %}{{ cls.extends }}{% else %}Node{% endif %} {
{% if not cls.abstract %}

    static _RULE_NAME = {{ cls.rule_name | tojson }};
    static _FIELDS = [{% for field in cls.fields %}{{ field.name | tojson }}{% if not loop.last %}, {% endif %}{% endfor %}];

    constructor({% for field in cls.fields %}{{ field.name }}{% if not loop.last %}, {% endif %}{% endfor %}) {
        super();
{% for field in cls.fields %}        this.{{ field.name }} = {{ field.name }};
{% endfor %}{% for frag in init_fragments %}        {{ frag.body | indent(8) }}
{% endfor %}    }

{% endif %}{% for frag in body_fragments %}    {{ frag.body | indent(4) }}

{% endfor %}}

module.exports = { {{ cls.name }} };
```

- [ ] **Step 4: Create the Jinja2 main template**

Create `src/plcc/lang/ext/javascript/templates/main.js.jinja`:

```jinja2
{% set concrete = classes | selectattr('abstract', 'equalto', false) | list %}
const { Registry } = require('./runtime/registry');
const { deserialize } = require('./runtime/deserialize');
{% for cls in concrete %}const { {{ cls.name }} } = require('./{{ cls.name }}');
{% endfor %}
const registry = new Registry();
registry.register({% for cls in concrete %}{{ cls.name }}{% if not loop.last %}, {% endif %}{% endfor %});

process.on('SIGINT', () => {
    process.stdout.write('User interrupted execution by ^C.\n');
    process.exit(130);
});

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
        console.log(JSON.stringify({ kind: 'error', type: e.constructor.name, message: e.message ?? '' }));
    }
});
```

- [ ] **Step 5: Implement emit.py**

Create `src/plcc/lang/ext/javascript/emit.py`:

```python
"""plcc-javascript-emit
    Emit a JavaScript interpreter from model JSON.

Usage:
    plcc-javascript-emit --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
"""

import enum
import json
import shutil
import sys
from pathlib import Path

import jinja2
from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS

_DEFAULT_ENTRY_POINT = '_run'

_START_JS = """\
const { Node } = require('./runtime/base');

class _Start extends Node {
    _run() {
        console.log(String(this));
    }
}

module.exports = { _Start };
"""


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-javascript-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')

    model = json.load(sys.stdin)
    output_dir.mkdir(parents=True, exist_ok=True)

    _copy_runtime(output_dir)

    classes = model['classes']
    start_class_name = model['start'][0].upper() + model['start'][1:]
    section = _find_javascript_section(model)
    entry_point = _DEFAULT_ENTRY_POINT
    fragments_by_class = _group_fragments(section.get('fragments', []) if section else [])

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(Path(__file__).parent / 'templates')),
        keep_trailing_newline=True,
    )
    class_template = env.get_template('class_file.js.jinja')
    main_template = env.get_template('main.js.jinja')

    for cls in classes:
        cls = dict(cls)
        if cls['name'] == start_class_name and cls['extends'] is None:
            cls['extends'] = '_Start'
        frags = fragments_by_class.get(cls['name'], [])
        content = class_template.render(
            cls=cls,
            top_fragments=[f for f in frags if f['kind'] == 'top'],
            import_fragments=[f for f in frags if f['kind'] == 'import'],
            init_fragments=[f for f in frags if f['kind'] == 'init'],
            body_fragments=[f for f in frags if f['kind'] == 'body'],
        )
        (output_dir / f"{cls['name']}.js").write_text(content)

    (output_dir / '_Start.js').write_text(_START_JS)

    all_frags = section.get('fragments', []) if section else []
    for frag in all_frags:
        if frag['kind'] == 'file':
            (output_dir / f"{frag['class_name']}.js").write_text(frag['body'])

    main_content = main_template.render(classes=classes, entry_point=entry_point)
    (output_dir / 'main.js').write_text(main_content)

    verbose.emit(Events.FINISHED, message='done')


def _copy_runtime(output_dir):
    src = Path(__file__).parent / 'runtime'
    dst = output_dir / 'runtime'
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('*_test.py'))


def _find_javascript_section(model):
    for s in model.get('semantic_sections', []):
        if s.get('language', '').lower() == 'javascript':
            return s
    return None


def _group_fragments(fragments):
    groups = {}
    for frag in fragments:
        groups.setdefault(frag['class_name'], []).append(frag)
    return groups
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/emit_test.py -v
```

Expected: all passed. If `test_emit_generated_main_exits_130_on_sigint` is flaky on the CI environment (SIGINT timing), that is acceptable to skip with `@pytest.mark.skip`.

- [ ] **Step 7: Run full unit suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: all passing (973+ tests).

- [ ] **Step 8: Commit**

```bash
git add src/plcc/lang/ext/javascript/emit.py \
        src/plcc/lang/ext/javascript/emit_test.py \
        src/plcc/lang/ext/javascript/templates/
git commit -m "feat(javascript): add emit.py and Jinja2 templates"
```

---

## Task 5: run.py + entry points

**Files:**
- Create: `src/plcc/lang/ext/javascript/run.py`
- Create: `src/plcc/lang/ext/javascript/run_test.py`
- Modify: `pyproject.toml` (add two entries under `[project.scripts]`)

**Interfaces:**
- Consumes: `node` on PATH, output directory from emit (Task 4)
- Produces: `plcc.lang.ext.javascript.run:main` — invokes `node main.js` passing stdin/stdout/stderr through

- [ ] **Step 1: Write the failing run tests**

Create `src/plcc/lang/ext/javascript/run_test.py`:

```python
import subprocess

import pytest

from .run import main as run_main


def test_keyboard_interrupt_exits_130(monkeypatch, tmp_path):
    def raise_ki(*a, **kw):
        raise KeyboardInterrupt()
    monkeypatch.setattr(subprocess, 'run', raise_ki)
    exit_code = None
    try:
        run_main([f'--output={tmp_path}'])
    except SystemExit as e:
        exit_code = e.code
    except KeyboardInterrupt:
        pytest.fail("KeyboardInterrupt escaped — should be converted to sys.exit(130)")
    assert exit_code == 130


def test_run_exits_with_node_return_code(monkeypatch, tmp_path):
    class FakeResult:
        returncode = 42
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: FakeResult())
    exit_code = None
    try:
        run_main([f'--output={tmp_path}'])
    except SystemExit as e:
        exit_code = e.code
    assert exit_code == 42
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/run_test.py -v
```

Expected: 2 failures mentioning `cannot import name 'main' from 'plcc.lang.ext.javascript.run'`

- [ ] **Step 3: Implement run.py**

Create `src/plcc/lang/ext/javascript/run.py`:

```python
"""plcc-javascript-run
    Run a generated JavaScript interpreter.

Usage:
    plcc-javascript-run --output=DIR [-v ...] [options]

Options:
    --output=DIR    Directory containing generated JavaScript files.
    -h --help       Show this message.
"""

import enum
import os
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
    verbose = VerboseContext.from_args("plcc-javascript-run", Events, args)
    output_dir = args['--output']
    main_js = os.path.join(output_dir, 'main.js')
    verbose.emit(Events.STARTED, message=f'running {main_js}')
    try:
        result = subprocess.run(
            ['node', main_js],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    except KeyboardInterrupt:
        sys.exit(130)
    verbose.emit(Events.FINISHED, message=f'exit {result.returncode}')
    sys.exit(result.returncode)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/lang/ext/javascript/run_test.py -v
```

Expected: 2 passed

- [ ] **Step 5: Add entry points to pyproject.toml**

In `pyproject.toml`, find the block with `plcc-python-emit` and add after `plcc-java-run`:

```toml
plcc-javascript-emit = "plcc.lang.ext.javascript.emit:main"
plcc-javascript-run  = "plcc.lang.ext.javascript.run:main"
```

The relevant section of `pyproject.toml` currently ends with:
```toml
plcc-java-emit  = "plcc.lang.ext.java.emit:main"
plcc-java-build = "plcc.lang.ext.java.build:main"
plcc-java-run   = "plcc.lang.ext.java.run:main"
plcc-version = "plcc.version:main"
```

It should become:
```toml
plcc-java-emit  = "plcc.lang.ext.java.emit:main"
plcc-java-build = "plcc.lang.ext.java.build:main"
plcc-java-run   = "plcc.lang.ext.java.run:main"
plcc-javascript-emit = "plcc.lang.ext.javascript.emit:main"
plcc-javascript-run  = "plcc.lang.ext.javascript.run:main"
plcc-version = "plcc.version:main"
```

- [ ] **Step 6: Reinstall to register the entry points**

```bash
bin/build/package.bash
```

Expected: build succeeds, ends with `Built wheel at dist/...`

- [ ] **Step 7: Verify entry points are on PATH**

```bash
which plcc-javascript-emit && which plcc-javascript-run
```

Expected: both resolve to paths under `.venv/bin/`

- [ ] **Step 8: Smoke-test the full pipeline with a minimal grammar**

Run the following. It pipes a hand-crafted model JSON (matching a grammar with one `Program` class that has no fields) directly to the emitter, then runs it:

```bash
OUTDIR=$(mktemp -d)
echo '{"start":"program","classes":[{"name":"Program","abstract":false,"extends":null,"rule_name":"program","fields":[]}],"semantic_sections":[]}' \
  | plcc-javascript-emit --output="$OUTDIR"
echo '{"kind":"rule","rule":"program","children":[]}' \
  | plcc-javascript-run --output="$OUTDIR"
```

Expected: second command prints something like `{"kind":"result","value":null}` or similar (the default `_run()` in `_Start` calls `console.log(String(this))`; with no `toString()` override on `Program`, it prints `[object Object]` as the result).

- [ ] **Step 9: Run full unit suite**

```bash
bin/test/units.bash
```

Expected: all tests pass.

- [ ] **Step 10: Commit**

```bash
git add src/plcc/lang/ext/javascript/run.py \
        src/plcc/lang/ext/javascript/run_test.py \
        pyproject.toml
git commit -m "feat(javascript): add run.py and register entry points"
```
