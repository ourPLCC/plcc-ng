# Phase 2 Part 3: Python Emitter and Interactive REPL — Design

**Date:** 2026-04-25
**Status:** APPROVED
**Companion architectural spec:** `docs/design/2026-04-12-multi-lang-pipeline.md`
**Roadmap reference:** `docs/design/2026-04-12-multi-lang-implementation-plan.md` §5

---

## 1. Goal

Deliver a complete, tested `plcc-python-emit` implementation and a fully interactive
`plcc-rep` REPL. After Part 3:

```sh
plcc-make arith.plcc
plcc-rep arith.plcc
>>> 1 + 2
3
```

produces a running Python interpreter for the arithmetic grammar with a persistent
read-eval loop.

---

## 2. Phase Structure

Phase 2 is divided into three parts:

| Part | Scope | Status |
| --- | --- | --- |
| Part 1 | LL(1) parser (`plcc-ll1`, `plcc-parser-table`) | Complete |
| Part 2 | Full `plcc-model` + `plcc-diagram-*` system | Complete |
| **Part 3** | **`plcc-spec` entry-point, `plcc-python-emit`, `plcc-rep`** | **This design** |

---

## 3. Scope

Part 3 touches five areas in sequence:

| Area | What changes |
| --- | --- |
| `plcc-spec` + `spec.json` | Parse optional 3rd token in `% <tool> <lang> [<method>]`; add `entry_point` to spec JSON |
| `plcc-model` + `model.json` | Pass `entry_point` through from spec JSON to model JSON |
| `arith.plcc` fixture | Add `Program._run()` semantic body and declare entry point in header |
| `plcc-python-emit` | Full implementation: Jinja2 templates, one file per class, runtime copy |
| `plcc-rep` | Full interactive REPL using pre-built `build/` artifacts |

**Out of scope for Part 3:**
- `plcc-make` diagram integration (Phase 4)
- Java emitter (Phase 3)
- Error recovery in `plcc-tree` (Phase 3+)
- `plcc-scan` / `plcc-parse` visualizers (Phase 4)

---

## 4. Entry-Point Method Declaration

### 4.1 Grammar syntax

The semantic section header gains an optional third token declaring the entry-point
method name:

```
% calculate Python          →  entry_point: null   (emitter uses its language default)
% calculate Python _run     →  entry_point: "_run"
%                           →  entry_point: null   (v8 legacy; Java emitter uses $run)
```

The change is additive — no existing grammars break.

### 4.2 Language-specific defaults

Each emitter plugin defines its own default when `entry_point` is null:

| Language | Default entry-point |
| --- | --- |
| Python | `_run` |
| Java | `$run` (backwards compat with v8) |

### 4.3 `plcc-spec` implementation

Locate the student-written grammar parser code that handles semantic section headers
and extend it surgically to capture a third token when present. Do not restructure or
replace the student code. Use `git mv` if any file must be relocated to preserve
history.

### 4.4 `spec.json` schema change

Each semantic section object gains one new field:

```json
{
  "tool": "calculate",
  "language": "Python",
  "entry_point": "_run",
  "codeFragmentList": [...]
}
```

`entry_point` is a string when declared, `null` when absent. All existing consumers
of `spec.json` ignore unknown fields — this change is non-breaking.

---

## 5. `plcc-model` and `model.json`

`plcc-model` copies `entry_point` verbatim from each spec JSON semantic section into
the corresponding model JSON semantic section. No interpretation — `plcc-model` is
language-neutral.

```json
{
  "language": "Python",
  "tool": "calculate",
  "entry_point": "_run",
  "fragments": [...]
}
```

`null` when not declared. The emitter reads this and applies its language-specific
default when null.

---

## 6. `arith.plcc` Fixture Update

### 6.1 Header change

```
% calculate Python
```
becomes:
```
% calculate Python _run
```

### 6.2 New `Program` semantic fragment

```
Program
%%%
def _run(self):
    return self.expr.eval(0)
%%%
```

`Program._run()` seeds the accumulator at `0` and delegates to `Expr.eval()`.
The existing fragments for `AddRest`, `NilRest`, and `Term` are unchanged.

The fixture remains LL(1) and all existing Part 2 tests continue to pass — the
semantic section change is invisible to `plcc-model`'s class derivation and diagram
generation.

---

## 7. `plcc-python-emit`

### 7.1 Generated output layout

```
<dir>/
├── Program.py
├── Expr.py
├── ExprRest.py
├── AddRest.py
├── NilRest.py
├── Term.py
├── main.py
└── runtime/
    ├── base.py
    ├── deserialize.py
    └── registry.py
```

One `.py` file per class. Standalone `file` fragments write additional files by
`class_name`. The runtime is copied verbatim from the plugin's bundled
`runtime/` directory.

### 7.2 Plugin source layout

```
src/plcc/lang/ext/python/
├── emit.py
├── emit_test.py
├── run.py
├── templates/
│   ├── class_file.py.jinja
│   └── main.py.jinja
└── runtime/
    ├── base.py
    ├── deserialize.py
    └── registry.py
```

`emit.py` locates templates via `pathlib.Path(__file__).parent / "templates"`.

### 7.3 Class name namespacing

Generated classes import the runtime under a private alias to avoid collisions with
grammar-defined class names:

```python
import runtime.base as _plcc
```

A grammar that defines a nonterminal named `Node` or `Token` does not collide with
the runtime base classes.

### 7.4 `class_file.py.jinja` template

Applied once per class in `model.classes`. Handles all fragment kinds in order:

```jinja
{# top fragments — module-level code before imports #}
{% for frag in top_fragments %}{{ frag.body }}
{% endfor %}
{# import fragments #}
import runtime.base as _plcc
{% for frag in import_fragments %}{{ frag.body }}
{% endfor %}

class {{ cls.name }}({{ parent }}{% for frag in class_fragments %}, {{ frag.body }}{% endfor %}):

    def __init__(self{% for field in cls.fields %}, {{ field.name }}{% endfor %}):
        super().__init__()
        {% for field in cls.fields %}self.{{ field.name }} = {{ field.name }}
        {% endfor %}
        {% for frag in init_fragments %}{{ frag.body | indent(8) }}{% endfor %}

    {% for frag in body_fragments %}{{ frag.body | indent(4) }}{% endfor %}
```

`parent` is the capitalized `extends` value when non-null (imported from its own
module); otherwise `_plcc.Node`.

Abstract classes have `fields: []` and no `__init__` body beyond `super().__init__()`.

### 7.5 `file` fragments

`file` fragments (`kind == "file"`) are written as `{class_name}.py` with the
fragment body as complete file contents — no template applied. This is how grammar
authors inject standalone helper files (e.g., singleton environments, shared state).

Other class files reference standalone files via `:import` hooks:

```
AddRest:import
%%%
from Env import Env
%%%
```

### 7.6 `main.py.jinja` template

```jinja
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime.registry import Registry
{% for cls in classes %}from {{ cls.name }} import {{ cls.name }}
{% endfor %}

registry = Registry()
registry.register({% for cls in classes %}{{ cls.name }}{% if not loop.last %}, {% endif %}{% endfor %})

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        tree = registry.deserialize(json.loads(line))
        result = tree.{{ entry_point }}()
        print(json.dumps({"kind": "result", "value": repr(result) if result is not None else None}), flush=True)
    except Exception as e:
        print(json.dumps({"kind": "error", "type": type(e).__name__, "message": str(e)}), flush=True)
```

`entry_point` is taken from `model.semantic_sections[].entry_point`, falling back
to `_run` when null.

`sys.path.insert(0, ...)` ensures `import runtime.base` works regardless of the
working directory the interpreter is invoked from.

### 7.7 `python -u` flag

`plcc-python-run` spawns `main.py` with the `-u` (unbuffered) flag:

```python
subprocess.Popen([sys.executable, "-u", main_py], ...)
```

This ensures all `print()` calls from semantic methods flush immediately to the pipe,
preventing deadlock when `plcc-rep` is waiting for output.

---

## 8. Python Runtime Library

Lives at `src/plcc/lang/ext/python/runtime/` and is copied verbatim into
`<output>/runtime/` by `plcc-python-emit`.

**`runtime/base.py`:**
- `Node` — base class for all generated nonterminal classes. Bare class; exists for
  `isinstance` checks and a common parent.
- `Token` — wraps a terminal from the parse tree. Has `lexeme` (string) and `kind`
  (string) attributes.

**`runtime/deserialize.py`:**
- Recursively reconstructs an object tree from a parse-tree JSON dict.
- Uses `kind` field to look up the correct class in the registry.
- Terminals become `Token` instances; nonterminals become instances of the
  registered generated class.

**`runtime/registry.py`:**
- `Registry.register(*classes)` — maps class name strings to class objects.
- `Registry.deserialize(dict)` — entry point called by `main.py`.

---

## 9. Evaluation Record Schema

The generated `main.py` writes one JSONL record to stdout per tree evaluated, then
flushes. These are an **internal pipe protocol** between `main.py` and `plcc-rep` —
the user never sees them directly.

**Success:**
```json
{"kind": "result", "value": "3"}
```
`value` is `repr(result)` when `_run()` returns a non-None value; `null` when
`_run()` returns `None` (grammar author used `print()` for side effects).

**Runtime error:**
```json
{"kind": "error", "type": "ZeroDivisionError", "message": "division by zero"}
```

The harness catches all exceptions, emits an error record, and continues the loop —
the session stays alive.

**Pass-through output:** any `print()` calls from semantic methods flow directly to
stdout between records. `plcc-rep` passes these through verbatim to its own stdout.

**`plcc-rep` rendering** (following Level 2 output contract, arch spec §9):
- `--verbose-format=text` (default): print `value` as plain text; print runtime
  errors as `error: {type}: {message}` to stderr
- `--verbose-format=json`: re-emit structured JSONL records on stdout

---

## 10. `plcc-rep` REPL

`plcc-rep` is a **fixed Python orchestrator** — written once, language-agnostic,
ships with `plcc`. It is not generated. The generated artifact is only the
interpreter (`build/<tool>/main.py`).

### 10.1 Separation of responsibilities

- **`plcc-make`** — builds the project: spec → ll1 → model → emit → build. Must be
  run before `plcc-rep`.
- **`plcc-rep`** — runs the REPL using pre-built artifacts from `build/`. Does not
  build the language.

This matches the original PLCC behaviour where `rep`, `scan`, and `parse` did not
build the language.

### 10.2 Session lifecycle

1. Check `build/spec.json` and `build/ll1.json` exist — if not, exit with:
   `"plcc-rep: build/ not found. Run plcc-make first."`
2. Resolve tool:
   - If `--tool` specified: use it
   - If absent and exactly one semantic section in `build/spec.json`: use it
   - If absent and multiple sections exist: print available tool names and exit
     nonzero
3. Look up language for the selected tool from `build/spec.json`
4. Check `build/<tool>/` exists — if not, exit with:
   `"plcc-rep: build/<tool>/ not found. Run plcc-make first."`
5. Spawn `plcc-lang-run --target=<lang> --output=build/<tool>/` as the long-lived
   interpreter subprocess (one process for the entire session)
6. Process file arguments, then enter read-eval loop

### 10.3 Read-eval loop — two chunk sources in order

**File arguments (`SOURCE ...`):** feed each file as one chunk sequentially, no
prompting.

**Stdin:**
- If tty: emit `>>> ` prompt to stderr, read one line per chunk
- If redirected: read entire stdin as one chunk, then exit

### 10.4 Per-chunk processing

1. Spawn a fresh `plcc-tokens --spec=build/spec.json | plcc-tree --ll1=build/ll1.json`
   subpipeline; feed the chunk; collect the tree JSON line
2. Write the tree JSON line to the interpreter's stdin pipe
3. Read lines from the interpreter's stdout:
   - Lines that are not a `{"kind": ...}` JSONL record: pass through verbatim to
     `plcc-rep`'s stdout
   - First `{"kind": ...}` record: render per §9 and continue

### 10.5 Session end

EOF on all chunk sources → close interpreter's stdin pipe → interpreter's read loop
falls off naturally → interpreter process exits → `plcc-rep` exits 0.

### 10.6 Error handling

- `plcc-tokens` or `plcc-tree` failure per chunk → print error to stderr, continue
  loop (session stays alive)
- Interpreter process dies unexpectedly → print error to stderr, exit `plcc-rep`

### 10.7 Statefulness

Because the interpreter is a single long-lived process, any module-level state
(singleton environments, class variables, shared dictionaries) defined in generated
classes or standalone `file` fragments persists naturally between evaluations. No
special mechanism required.

---

## 11. Acceptance Criteria

1. **`plcc-spec` entry-point parsing:** `plcc-spec arith.plcc` produces `spec.json`
   with `entry_point: "_run"` in the `calculate`/`Python` semantic section.
2. **Null entry-point:** a grammar with `% calculate Python` (no third token)
   produces `entry_point: null` in `spec.json`.
3. **Model pass-through:** `plcc-spec arith.plcc | plcc-model` produces `model.json`
   with `entry_point: "_run"` in the semantic section.
4. **Emit produces one file per class:** `plcc-python-emit --output=<dir> <
   model.json` produces one `.py` file per class in `model.classes`, plus `main.py`
   and `runtime/`.
5. **All fragment kinds applied:** generated class files correctly apply `top`,
   `import`, `class`, `init`, and `body` fragments; `file` fragments are written
   verbatim.
6. **Entry-point default:** when `model.json` has `entry_point: null`, the generated
   `main.py` calls `_run()`.
7. **`plcc-make` produces full build:** `plcc-make arith.plcc` produces
   `build/spec.json`, `build/ll1.json`, `build/model.json`, and `build/calculate/`.
8. **Interactive REPL:** `plcc-rep arith.plcc` starts a REPL; typing `1 + 2`
   produces `3`; a malformed expression produces an error message and the session
   continues.
9. **File argument:** `plcc-rep arith.plcc program.txt` evaluates the file and exits.
10. **Batch mode:** `plcc-rep arith.plcc < program.txt` runs silently with no prompts.
11. **Standalone invocation:** `plcc-tokens --spec build/spec.json < program.txt |
    plcc-tree --ll1 build/ll1.json | python build/calculate/main.py` works from the
    project root without changing directory.
12. **All existing tests pass:** no regressions from `plcc-spec` and `plcc-model`
    changes.
