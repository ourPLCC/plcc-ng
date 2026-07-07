# JavaScript Emitter Design

**Issue:** 066
**Date:** 2026-06-22

## Overview

Add a JavaScript (Node.js) language backend to plcc-ng, following the same extension pattern as the existing `java` and `python` backends. The generated code uses CommonJS modules and requires no compilation step.

JavaScript was chosen over TypeScript, C++, and Rust because:

- No build step (interpreted, like Python)
- Native `JSON.parse` — no runtime library needed for deserialization
- Node.js is ubiquitous in classrooms
- ES6 classes map directly onto the class-per-rule design
- Highest market share of the candidates in 2026

## Extension Location

```text
src/plcc/lang/ext/javascript/
  __init__.py
  emit.py
  emit_test.py
  run.py
  run_test.py
  templates/
    class_file.js.jinja
    main.js.jinja
  runtime/
    base.js
    base_test.py
    registry.js
    registry_test.py
    deserialize.js
    deserialize_test.py
```

## Entry Points

Two entries added to `pyproject.toml` `[project.scripts]`:

```toml
plcc-javascript-emit = "plcc.lang.ext.javascript.emit:main"
plcc-javascript-run  = "plcc.lang.ext.javascript.run:main"
```

No `plcc-javascript-build` entry point. `plcc-lang-build` exits 0 when the build command is absent, so the pipeline skips the build step automatically — identical to Python's behavior.

## Spec Section Tag

Users tag semantic sections with `javascript` (lowercase), consistent with the existing `java` and `python` tags:

```text
%javascript
ClassName
%%%
body
    someMethod() { ... }
%%%
```

## Fragment Kinds

Matches Python's set minus `class`. The original PLCC's `class` hook served two purposes: in Java it injected content into the class declaration line to add `implements` clauses; in Python it added comma-separated base classes for multiple inheritance. JavaScript has neither interfaces nor multiple inheritance, so there is no equivalent and `class` is intentionally omitted.

Note: plcc-ng's Java emitter is currently missing `class` fragment support from the original PLCC. That gap is tracked separately (see issue 067).

| Kind     | Placement in generated file                                   |
|----------|---------------------------------------------------------------|
| `top`    | Before the class definition (e.g., `const x = require(...)`)  |
| `import` | After the generated `require` lines, before the class         |
| `init`   | Inside the constructor body, after field assignments          |
| `body`   | Methods on the class                                          |
| `file`   | Replaces the entire class file                                |

## Generated Output Structure

```text
<output>/
  main.js             # entry point
  _Start.js           # default base for the start class
  <ClassName>.js      # one file per class from the model
  runtime/
    base.js
    registry.js
    deserialize.js
```

## Generated Class File (`class_file.js.jinja`)

```javascript
// top fragments
const { Node, Token } = require('./runtime/base');
// if cls.extends: const { ParentClass } = require('./ParentClass');
// import fragments

class ClassName extends ParentOrNode {
    // abstract classes: body fragments only, no static fields or constructor

    static _RULE_NAME = 'rule_name';      // concrete classes only
    static _FIELDS = ['field1', 'field2']; // concrete classes only

    constructor(field1, field2) {          // concrete classes only
        super();
        this.field1 = field1;
        this.field2 = field2;
        // init fragments
    }

    // body fragments
}

module.exports = { ClassName };
```

Abstract classes omit `_RULE_NAME`, `_FIELDS`, and the constructor — they are not registered and cannot be instantiated by the registry. This mirrors Python's behavior.

## `_Start.js`

Injected into the output directory when the grammar's start class has no explicit `extends`. Provides a default `_run()` that prints the node's string representation:

```javascript
const { Node } = require('./runtime/base');

class _Start extends Node {
    _run() {
        console.log(String(this));
    }
}

module.exports = { _Start };
```

The start class `extends _Start` instead of `extends Node` when it has no explicit parent.

## `main.js` (`main.js.jinja`)

Reads JSON lines from stdin, deserializes each into an object tree, calls `_run()` on the root, and prints a JSON result or error record — identical protocol to Java and Python:

```javascript
const { Registry } = require('./runtime/registry');
const { deserialize } = require('./runtime/deserialize');
const { ConcreteClass1 } = require('./ConcreteClass1');
// ... one require per concrete class

const registry = new Registry();
registry.register(ConcreteClass1, ...);

const readline = require('readline');
const rl = readline.createInterface({ input: process.stdin });

rl.on('line', (line) => {
    line = line.trim();
    if (!line) return;
    try {
        const tree = deserialize(JSON.parse(line), registry);
        const result = tree._run();
        console.log(JSON.stringify({
            kind: 'result',
            value: result != null ? String(result) : null
        }));
    } catch (e) {
        console.log(JSON.stringify({
            kind: 'error',
            type: e.constructor.name,
            message: e.message ?? ''
        }));
    }
});
```

## Runtime Library

### `runtime/base.js`

`Node` — empty base class all generated classes ultimately extend.

`Token` — holds `kind` and `lexeme`; `toString()` returns `lexeme`. Not a subclass of `Node`.

### `runtime/registry.js`

`Registry` — registers concrete classes by `_RULE_NAME` + `_FIELDS` set; `lookup(ruleName, fieldNames)` returns the matching class. Same algorithm as Python's registry.

### `runtime/deserialize.js`

`deserialize(tree, registry)` — recursive. Token nodes (`kind === 'token'`) produce `Token` instances. All other nodes look up their class in the registry and construct it with positional field arguments extracted from the `children` array.

## `emit.py`

Mirrors `python/emit.py` closely:

- Reads model JSON from stdin
- Creates output directory
- Copies `runtime/` (excluding `*_test.py`)
- Renders `class_file.js.jinja` for each class
- Writes `_Start.js` inline (string constant, like Python/Java)
- Renders `main.js.jinja`
- Applies `file` fragments (overwrite entire class file)
- Filters fragments by kind per class

## `run.py`

Invokes `node main.js` in the output directory, passing stdin/stdout/stderr through. Handles `KeyboardInterrupt` with exit code 130. No compilation step.

## Testing

### `emit_test.py`

Pytest unit tests for the emitter:

- Correct file names generated for concrete and abstract classes
- `_RULE_NAME`, `_FIELDS`, constructor present on concrete classes
- `_RULE_NAME`, `_FIELDS`, constructor absent on abstract classes
- `_Start.js` written when start class has no explicit `extends`
- Start class `extends _Start` when it has no explicit parent
- Fragment kinds placed in correct positions (`top`, `import`, `init`, `body`)
- `file` fragment replaces entire class file
- Runtime directory copied to output

### `run_test.py`

Pytest unit tests for the runner:

- Invokes `node main.js` with the output directory
- Passes stdin/stdout/stderr through
- Exits with the node process's return code

### `runtime/base_test.py`, `registry_test.py`, `deserialize_test.py`

Pytest tests using `subprocess.run(['node', '-e', '...'])` to exercise the JS runtime modules. Node.js must be available in the test environment (a reasonable requirement given it is the target runtime).

Tests cover:

- `Node` is a valid base class
- `Token` stores kind and lexeme; `toString()` returns lexeme
- `Registry.register` and `lookup` by rule name and field set
- `deserialize` handles tokens, single nodes, nested nodes, list fields

## Module System

CommonJS throughout. All generated files use `require()` and `module.exports`. No `package.json` is written to the output directory — Node.js resolves `require('./runtime/base')` without one.

If ESM support is ever needed, it would be a separate `javascript-esm` extension, not a flag on this one.
