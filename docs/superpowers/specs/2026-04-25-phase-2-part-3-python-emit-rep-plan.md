# Phase 2 Part 3: Python Emitter and Interactive REPL — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver `plcc-python-emit` (full Jinja2 code generation, one `.py` per class) and `plcc-rep` (interactive REPL using pre-built `build/` artifacts), so that `plcc-make arith.plcc && plcc-rep arith.plcc` evaluates `1 + 2` to `3`.

**Architecture:** Five sequential areas: (1) extend `plcc-spec` to capture an optional entry-point method name in the semantic section header; (2) thread that value through `plcc-model`; (3) add `rule_name` to every model class to enable field-based tree deserialization; (4) generate one `.py` file per class via Jinja2 templates plus a shared runtime library; (5) rewrite `plcc-rep` as a long-lived REPL that streams over pre-built `build/` artifacts.

**Tech Stack:** Python 3.12, Jinja2, dataclasses, subprocess.Popen, bats for integration/e2e tests.

---

## File Structure

**Files created:**
- `src/plcc/lang/ext/python/runtime/base.py` — `Node` and `Token` base classes
- `src/plcc/lang/ext/python/runtime/registry.py` — `Registry`: maps (rule_name, field-set) → class
- `src/plcc/lang/ext/python/runtime/deserialize.py` — recursive parse-tree JSON → object graph
- `src/plcc/lang/ext/python/runtime/base_test.py` — unit tests for base.py
- `src/plcc/lang/ext/python/runtime/registry_test.py` — unit tests for registry.py
- `src/plcc/lang/ext/python/runtime/deserialize_test.py` — unit tests for deserialize.py
- `src/plcc/lang/ext/python/templates/class_file.py.jinja` — per-class code template
- `src/plcc/lang/ext/python/templates/main.py.jinja` — interpreter entry-point template
- `tests/bats/integration/python-emit.bats` — integration test: emit → run
- `tests/bats/e2e/plcc-rep.bats` — end-to-end test: plcc-rep arith

**Files modified:**
- `src/plcc/spec/rough/Divider.py` — add `entry_point: str | None = None`
- `src/plcc/spec/rough/parse_dividers.py` — capture 3rd token as entry_point
- `src/plcc/spec/rough/parse_dividers_test.py` — update `make_divider` + add tests
- `src/plcc/spec/semantics/SemanticSpec.py` — add `entry_point: str | None = None`
- `src/plcc/spec/semantics/parse_semantic_spec.py` — pass `entry_point` from divider
- `src/plcc/schemas/spec.schema.json` — add `entry_point` to semantics items
- `src/plcc/model/build_model.py` — propagate `entry_point`; add `rule_name` to classes
- `src/plcc/model/build_model_test.py` — tests for entry_point + rule_name
- `src/plcc/schemas/model.schema.json` — add `entry_point` + `rule_name` fields
- `tests/fixtures/arith.plcc` — add `_run` to header; add `Program` and `Expr` fragments
- `tests/fixtures/trivial-python.plcc` — capture NUM field; add `_run` header + fragment
- `pyproject.toml` — add `jinja2` dependency
- `src/plcc/lang/ext/python/emit.py` — full rewrite using Jinja2
- `src/plcc/lang/ext/python/emit_test.py` — update for new emit behaviour
- `src/plcc/lang/ext/python/run.py` — add `-u` flag
- `src/plcc/cmd/rep.py` — full rewrite as interactive REPL
- `tests/bats/commands/plcc-python-run.bats` — update to use new tree format + eval records

**Files deleted:**
- `src/plcc/lang/ext/python/runtime/main.py` — replaced by generated file from template

---

## Task 1: `plcc-spec` — entry_point in Divider and parsers

**Files:**
- Modify: `src/plcc/spec/rough/Divider.py`
- Modify: `src/plcc/spec/rough/parse_dividers.py`
- Modify: `src/plcc/spec/rough/parse_dividers_test.py`
- Modify: `src/plcc/spec/semantics/SemanticSpec.py`
- Modify: `src/plcc/spec/semantics/parse_semantic_spec.py`

- [ ] **Step 1: Update the `make_divider` helper and add two new tests in `parse_dividers_test.py`**

The existing test `test_one_divider_only_takes_first_two_lines` asserts that the third token is ignored. That must change — the third token is now `entry_point`. Update it and add an explicit null-entry-point test. Also update `make_divider` to accept `entry_point`.

In `src/plcc/spec/rough/parse_dividers_test.py`, change:
```python
def make_divider(tool, language, line):
    return Divider(tool=tool, language=language, line=line)
```
to:
```python
def make_divider(tool, language, line, entry_point=None):
    return Divider(tool=tool, language=language, line=line, entry_point=entry_point)
```

Replace this test:
```python
def test_one_divider_only_takes_first_two_lines():
    lines_ = list(lines.parseLines('% java python c++'))
    assert list(parse_dividers(lines_)) == [
        make_divider(tool='java', language='python', line=lines_[0])
    ]
```
with:
```python
def test_one_divider_with_entry_point():
    lines_ = list(lines.parseLines('% java python c++'))
    assert list(parse_dividers(lines_)) == [
        make_divider(tool='java', language='python', line=lines_[0], entry_point='c++')
    ]


def test_one_divider_without_entry_point_has_null():
    lines_ = list(lines.parseLines('% java python'))
    assert list(parse_dividers(lines_)) == [
        make_divider(tool='java', language='python', line=lines_[0], entry_point=None)
    ]
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k test_one_divider
```
Expected: `FAILED` (Divider has no `entry_point` field yet).

- [ ] **Step 3: Add `entry_point` to `Divider`**

Replace `src/plcc/spec/rough/Divider.py`:
```python
from dataclasses import dataclass, field

from ...lines import Line


@dataclass
class Divider:
    tool: str
    language: str
    line: Line
    entry_point: str | None = None
```

- [ ] **Step 4: Extend `parse_dividers.py` to capture the 3rd token**

In `src/plcc/spec/rough/parse_dividers.py`, change `_compilePatternDictionary`:
```python
def _compilePatternDictionary(self):
    return {
        'divider': re.compile(r'^%(?:\s.*)?$'),
        'toolLanguage': re.compile(r'^%\s*(?P<tool>\S+)\s+(?P<language>\S+)(?:\s+(?P<entry_point>\S+))?.*$'),
        'toolOnly': re.compile(r'^%\s*(?P<tool>\S+)\s*$')
    }
```

Add a `_getEntryPoint` method and update `_parseDivider` and `_createDivider`:
```python
def _parseDivider(self, line):
    matchToolLanguage = self._matchToolLanguage(line.string)
    matchToolOnly = self._matchToolOnly(line.string)
    tool = self._getTool(matchToolLanguage, matchToolOnly)
    language = self._getLanguage(matchToolLanguage, matchToolOnly)
    entry_point = self._getEntryPoint(matchToolLanguage)
    return self._createDivider(tool, language, entry_point, line)

def _getEntryPoint(self, matchToolLanguage):
    if matchToolLanguage:
        return matchToolLanguage['entry_point']  # None when group absent
    return None

def _createDivider(self, toolName, languageName, entry_point, line):
    return Divider(tool=toolName, language=languageName, line=line, entry_point=entry_point)
```

- [ ] **Step 5: Run the tests to confirm they pass**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k test_one_divider
```
Expected: all divider tests `PASSED`.

- [ ] **Step 6: Add `entry_point` to `SemanticSpec` and `parse_semantic_spec`**

Replace `src/plcc/spec/semantics/SemanticSpec.py`:
```python
from dataclasses import dataclass

from .CodeFragment import CodeFragment


@dataclass
class SemanticSpec:
    language: str
    tool: str
    codeFragmentList: list[CodeFragment]
    entry_point: str | None = None
```

Replace the body of `parse_semantic_spec.py`:
```python
from ...lines import Line
from ..rough import Block, Divider
from .parse_code_fragments import parse_code_fragments
from .SemanticSpec import SemanticSpec


def parse_semantic_spec(semantic_spec: list[Divider | Line | Block]) -> SemanticSpec:
    divider = semantic_spec[0]
    codeFragmentList = parse_code_fragments(semantic_spec[1:])
    return SemanticSpec(
        language=divider.language,
        tool=divider.tool,
        codeFragmentList=codeFragmentList,
        entry_point=divider.entry_point,
    )
```

- [ ] **Step 7: Run all unit tests**

```bash
cd .worktrees/multi-lang && bin/test/units.bash
```
Expected: all tests `PASSED`.

- [ ] **Step 8: Commit**

```bash
cd .worktrees/multi-lang
git add src/plcc/spec/rough/Divider.py \
        src/plcc/spec/rough/parse_dividers.py \
        src/plcc/spec/rough/parse_dividers_test.py \
        src/plcc/spec/semantics/SemanticSpec.py \
        src/plcc/spec/semantics/parse_semantic_spec.py
git commit -m "feat(plcc-spec): capture optional entry_point in semantic section header"
```

---

## Task 2: `spec.schema.json` — add `entry_point` field

**Files:**
- Modify: `src/plcc/schemas/spec.schema.json`

- [ ] **Step 1: Add `entry_point` to semantics items in the spec schema**

In `src/plcc/schemas/spec.schema.json`, update the `semantics.items.properties` block:

```json
"semantics": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["language", "tool"],
    "properties": {
      "language":    { "type": "string" },
      "tool":        { "type": "string" },
      "entry_point": { "type": ["string", "null"] }
    }
  }
}
```

- [ ] **Step 2: Verify `plcc-spec arith.plcc` validates against the updated schema**

```bash
cd .worktrees/multi-lang && pdm install
plcc-spec tests/fixtures/arith.plcc > /tmp/spec.json
check-jsonschema --schemafile src/plcc/schemas/spec.schema.json /tmp/spec.json
```
Expected: `ok -- validation done`. Also verify `entry_point` is still `null` (arith.plcc doesn't declare one yet).

```bash
python3 -c "import json; d = json.load(open('/tmp/spec.json')); print(d['semantics'][0].get('entry_point'))"
```
Expected: `None`.

- [ ] **Step 3: Commit**

```bash
cd .worktrees/multi-lang
git add src/plcc/schemas/spec.schema.json
git commit -m "feat(spec.schema): add entry_point field to semantics items"
```

---

## Task 3: `plcc-model` — propagate `entry_point` + `rule_name`

**Files:**
- Modify: `src/plcc/model/build_model.py`
- Modify: `src/plcc/model/build_model_test.py`
- Modify: `src/plcc/schemas/model.schema.json`

- [ ] **Step 1: Write failing tests in `build_model_test.py`**

Append these tests to `src/plcc/model/build_model_test.py`:

```python
# ---- entry_point pass-through ----

def test_semantic_section_entry_point_null_when_absent():
    model = build_model(_TRIVIAL_SPEC)
    assert model['semantic_sections'][0].get('entry_point') is None


def test_semantic_section_entry_point_when_present():
    spec = {
        "lexical": {"ruleList": []},
        "syntax": {"rules": []},
        "semantics": [{"language": "Python", "tool": "calc", "entry_point": "_run", "codeFragmentList": []}]
    }
    model = build_model(spec)
    assert model['semantic_sections'][0]['entry_point'] == '_run'


# ---- rule_name on classes ----

def test_trivial_class_has_rule_name():
    model = build_model(_TRIVIAL_SPEC)
    assert model['classes'][0]['rule_name'] == 'program'


def test_arith_abstract_class_has_rule_name():
    model = build_model(_ARITH_SPEC)
    exprrest = next(c for c in model['classes'] if c['name'] == 'ExprRest')
    assert exprrest['rule_name'] == 'ExprRest'


def test_arith_concrete_subclass_has_parent_rule_name():
    model = build_model(_ARITH_SPEC)
    addrest = next(c for c in model['classes'] if c['name'] == 'AddRest')
    assert addrest['rule_name'] == 'ExprRest'


def test_arith_nilrest_has_parent_rule_name():
    model = build_model(_ARITH_SPEC)
    nilrest = next(c for c in model['classes'] if c['name'] == 'NilRest')
    assert nilrest['rule_name'] == 'ExprRest'


def test_arith_expr_has_rule_name():
    model = build_model(_ARITH_SPEC)
    expr = next(c for c in model['classes'] if c['name'] == 'Expr')
    assert expr['rule_name'] == 'Expr'
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k "entry_point or rule_name"
```
Expected: `FAILED` (keys not in model yet).

- [ ] **Step 3: Update `build_model.py`**

In `src/plcc/model/build_model.py`, make two changes:

**Change 1** — add `rule_name` to every class dict in `_build_classes`:

```python
def _build_classes(spec):
    rules = spec.get('syntax', {}).get('rules', [])

    groups = {}
    order = []
    for rule in rules:
        name = rule['lhs']['name']
        if name not in groups:
            groups[name] = []
            order.append(name)
        groups[name].append(rule)

    classes = []
    for nt_name in order:
        nt_rules = groups[nt_name]
        class_name = nt_name[:1].upper() + nt_name[1:]
        is_abstract = any(r['lhs'].get('altName') for r in nt_rules)

        if is_abstract:
            classes.append({
                'name': class_name,
                'abstract': True,
                'extends': None,
                'fields': [],
                'rule_name': nt_name,
            })
            for rule in nt_rules:
                alt_name = rule['lhs']['altName']
                classes.append({
                    'name': alt_name,
                    'abstract': False,
                    'extends': class_name,
                    'fields': _extract_fields(rule.get('rhsSymbolList', [])),
                    'rule_name': nt_name,
                })
        else:
            rule = nt_rules[0]
            classes.append({
                'name': class_name,
                'abstract': False,
                'extends': None,
                'fields': _extract_fields(rule.get('rhsSymbolList', [])),
                'rule_name': nt_name,
            })

    return classes
```

**Change 2** — add `entry_point` to each semantic section dict in `_build_semantic_sections`:

```python
def _build_semantic_sections(spec, known_class_names):
    sections = []
    for s in spec.get('semantics', []):
        fragments = [
            _build_fragment(frag, known_class_names)
            for frag in s.get('codeFragmentList', [])
        ]
        sections.append({
            'language': s['language'],
            'tool': s['tool'],
            'entry_point': s.get('entry_point'),
            'fragments': fragments,
        })
    return sections
```

- [ ] **Step 4: Run the new tests**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k "entry_point or rule_name"
```
Expected: all `PASSED`.

- [ ] **Step 5: Run all unit tests to check for regressions**

```bash
cd .worktrees/multi-lang && bin/test/units.bash
```
Expected: all `PASSED`.

- [ ] **Step 6: Update `model.schema.json`**

In `src/plcc/schemas/model.schema.json`, add `rule_name` to class items and `entry_point` to semantic section items:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Model",
  "description": "Output of plcc-model: language-neutral OO code model.",
  "type": "object",
  "required": ["start", "classes", "semantic_sections"],
  "properties": {
    "start": { "type": "string" },
    "classes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "abstract", "fields", "rule_name"],
        "properties": {
          "name":      { "type": "string" },
          "abstract":  { "type": "boolean" },
          "extends":   { "type": ["string", "null"] },
          "rule_name": { "type": "string" },
          "fields": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["name", "type"],
              "properties": {
                "name": { "type": "string" },
                "type": { "type": "string" }
              }
            }
          }
        }
      }
    },
    "semantic_sections": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["tool", "language", "fragments"],
        "properties": {
          "tool":        { "type": "string" },
          "language":    { "type": "string" },
          "entry_point": { "type": ["string", "null"] },
          "fragments": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["class_name", "kind", "body"],
              "properties": {
                "class_name": { "type": "string" },
                "kind": {
                  "type": "string",
                  "enum": ["top", "import", "class", "init", "body", "file"]
                },
                "body": { "type": "string" }
              }
            }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 7: Verify `plcc-spec arith.plcc | plcc-model` validates against updated schema**

```bash
cd .worktrees/multi-lang
plcc-spec tests/fixtures/arith.plcc | plcc-model | check-jsonschema --schemafile src/plcc/schemas/model.schema.json /dev/stdin
```
Expected: `ok -- validation done`.

- [ ] **Step 8: Commit**

```bash
cd .worktrees/multi-lang
git add src/plcc/model/build_model.py \
        src/plcc/model/build_model_test.py \
        src/plcc/schemas/model.schema.json
git commit -m "feat(plcc-model): add entry_point pass-through and rule_name to class dicts"
```

---

## Task 4: Update `arith.plcc` fixture

**Files:**
- Modify: `tests/fixtures/arith.plcc`

- [ ] **Step 1: Update `arith.plcc`**

Replace `tests/fixtures/arith.plcc`:
```
token NUM   '\d+'
token PLUS  '\+'
skip  SPACE '\s+'
%
<program>              ::= <Expr>expr
<Expr>                 ::= <Term>term <ExprRest>rest
<ExprRest>:AddRest     ::= PLUS <Term>term <ExprRest>rest
<ExprRest>:NilRest     ::=
<Term>                 ::= <NUM>num
%
% calculate Python _run
Program
%%%
def _run(self):
    return self.expr.eval()
%%%
Expr
%%%
def eval(self):
    return self.rest.eval(self.term.eval())
%%%
AddRest
%%%
def eval(self, acc):
    return self.rest.eval(acc + self.term.eval())
%%%
NilRest
%%%
def eval(self, acc):
    return acc
%%%
Term
%%%
def eval(self):
    return int(self.num.lexeme)
%%%
```

- [ ] **Step 2: Verify `plcc-spec arith.plcc` produces `entry_point: "_run"`**

```bash
cd .worktrees/multi-lang
plcc-spec tests/fixtures/arith.plcc | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['semantics'][0]['entry_point'])"
```
Expected: `_run`.

- [ ] **Step 3: Run all existing tests to check for regressions**

```bash
cd .worktrees/multi-lang && bin/test/units.bash
```
Expected: all `PASSED`.

- [ ] **Step 4: Commit**

```bash
cd .worktrees/multi-lang
git add tests/fixtures/arith.plcc
git commit -m "feat(fixtures): add entry_point and Program/Expr eval fragments to arith.plcc"
```

---

## Task 5: Update `trivial-python.plcc` fixture and `plcc-python-run.bats`

**Files:**
- Modify: `tests/fixtures/trivial-python.plcc`
- Modify: `tests/bats/commands/plcc-python-run.bats`

The current emit stub produces a `main.py` that prints `"evaluated: {rule} (tree)"`. After the Task 12 rewrite, `main.py` emits JSONL eval records. Update the fixture and bats test now so that the rewrite doesn't break the bats test mid-task.

- [ ] **Step 1: Update `trivial-python.plcc` to capture `NUM` and declare `_run`**

Replace `tests/fixtures/trivial-python.plcc`:
```
token NUM '\d+'
%
<program> ::= <NUM>num
% py Python _run
Program
%%%
def _run(self):
    return int(self.num.lexeme)
%%%
```

- [ ] **Step 2: Verify the fixture parses correctly**

```bash
cd .worktrees/multi-lang
plcc-spec tests/fixtures/trivial-python.plcc | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('entry_point:', d['semantics'][0]['entry_point'])
print('rule:', d['syntax']['rules'][0]['rhsSymbolList'][0]['name'])
"
```
Expected:
```
entry_point: _run
rule: NUM
```

- [ ] **Step 3: Update `plcc-python-run.bats` for new eval-record output format**

The test must use a tree JSON that matches `trivial-python.plcc` (`program` has one field `num` of type `Token`), and check for the JSONL eval record.

Replace `tests/bats/commands/plcc-python-run.bats`:
```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-python.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-python-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-python-run is on PATH" { command -v plcc-python-run; }

@test "plcc-python-run evaluates parse-tree JSONL and returns eval record" {
    TREE='{"kind":"tree","rule":"program","children":[["num",{"kind":"token","name":"NUM","lexeme":"42"}]]}'
    run bash -c "echo '${TREE}' | plcc-python-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"value"'* ]]
    [[ "$output" == *'42'* ]]
}

@test "plcc-python-run exits 0 on empty input" {
    run bash -c "echo '' | plcc-python-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 4: Run bats commands test (will still pass with old emit since bats checks output format)**

```bash
cd .worktrees/multi-lang && bin/test/commands.bash 2>&1 | tail -20
```
Note: this test will likely fail (`"evaluated: program (tree)"` ≠ eval record) — that is expected and will be fixed in Task 12. The point here is that the test is written correctly before the implementation.

- [ ] **Step 5: Commit**

```bash
cd .worktrees/multi-lang
git add tests/fixtures/trivial-python.plcc \
        tests/bats/commands/plcc-python-run.bats
git commit -m "feat(fixtures): update trivial-python.plcc to capture NUM and declare _run"
```

---

## Task 6: Add `jinja2` dependency and write `runtime/base.py`

**Files:**
- Modify: `pyproject.toml`
- Create: `src/plcc/lang/ext/python/runtime/base.py`
- Create: `src/plcc/lang/ext/python/runtime/base_test.py`

- [ ] **Step 1: Write a failing test for `Node` and `Token`**

Create `src/plcc/lang/ext/python/runtime/base_test.py`:
```python
from .base import Node, Token


def test_node_is_base_class():
    n = Node()
    assert isinstance(n, Node)


def test_token_stores_kind_and_lexeme():
    t = Token(kind='NUM', lexeme='42')
    assert t.kind == 'NUM'
    assert t.lexeme == '42'


def test_token_is_not_node():
    t = Token(kind='NUM', lexeme='1')
    assert not isinstance(t, Node)
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k "test_node or test_token"
```
Expected: `FAILED` (module not found).

- [ ] **Step 3: Add `jinja2` to `pyproject.toml`**

In `pyproject.toml`, change the `dependencies` list:
```toml
dependencies = [
    "docopt-ng>=0.9.0",
    "jinja2>=3.1.0",
]
```

Then install:
```bash
cd .worktrees/multi-lang && pdm install
```

- [ ] **Step 4: Create `runtime/base.py`**

Write `src/plcc/lang/ext/python/runtime/base.py`:
```python
class Node:
    pass


class Token:
    def __init__(self, kind, lexeme):
        self.kind = kind
        self.lexeme = lexeme
```

- [ ] **Step 5: Run the tests**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k "test_node or test_token"
```
Expected: all `PASSED`.

- [ ] **Step 6: Commit**

```bash
cd .worktrees/multi-lang
git add pyproject.toml \
        src/plcc/lang/ext/python/runtime/base.py \
        src/plcc/lang/ext/python/runtime/base_test.py
git commit -m "feat(runtime): add Node/Token base classes and jinja2 dependency"
```

---

## Task 7: `runtime/registry.py` — field-based class lookup

**Files:**
- Create: `src/plcc/lang/ext/python/runtime/registry.py`
- Create: `src/plcc/lang/ext/python/runtime/registry_test.py`

Background: parse-tree JSON uses the parent nonterminal's name as the `rule` key for all concrete subclasses. `ExprRest:AddRest` and `ExprRest:NilRest` both appear as `"rule": "ExprRest"` in tree JSON. The Registry disambiguates by matching the set of field names in the tree's children against each class's `_fields` class attribute.

- [ ] **Step 1: Write failing tests**

Create `src/plcc/lang/ext/python/runtime/registry_test.py`:
```python
import pytest
from .registry import Registry
from .base import Node


class FakeProgram(Node):
    _rule_name = 'program'
    _fields = ['expr']

    def __init__(self, expr):
        self.expr = expr


class FakeAddRest(Node):
    _rule_name = 'ExprRest'
    _fields = ['term', 'rest']

    def __init__(self, term, rest):
        self.term = term
        self.rest = rest


class FakeNilRest(Node):
    _rule_name = 'ExprRest'
    _fields = []

    def __init__(self):
        pass


class FakeAbstract(Node):
    _rule_name = 'ExprRest'
    _fields = []
    _abstract = True


def test_registry_lookup_simple():
    reg = Registry()
    reg.register(FakeProgram)
    cls = reg.lookup('program', ['expr'])
    assert cls is FakeProgram


def test_registry_lookup_by_field_set_disambiguation():
    reg = Registry()
    reg.register(FakeAddRest, FakeNilRest)
    assert reg.lookup('ExprRest', ['term', 'rest']) is FakeAddRest
    assert reg.lookup('ExprRest', []) is FakeNilRest


def test_registry_lookup_field_order_independent():
    reg = Registry()
    reg.register(FakeAddRest)
    assert reg.lookup('ExprRest', ['rest', 'term']) is FakeAddRest


def test_registry_lookup_unknown_rule_raises():
    reg = Registry()
    with pytest.raises(KeyError):
        reg.lookup('unknown', [])


def test_registry_skips_abstract_classes():
    reg = Registry()
    reg.register(FakeAbstract, FakeNilRest)
    # FakeAbstract._abstract=True so NilRest should win for empty field set
    assert reg.lookup('ExprRest', []) is FakeNilRest
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k "registry"
```
Expected: `FAILED`.

- [ ] **Step 3: Implement `registry.py`**

Create `src/plcc/lang/ext/python/runtime/registry.py`:
```python
class Registry:
    def __init__(self):
        self._by_rule = {}

    def register(self, *classes):
        for cls in classes:
            if getattr(cls, '_abstract', False):
                continue
            rule_name = cls._rule_name
            fields = frozenset(cls._fields)
            self._by_rule.setdefault(rule_name, {})[fields] = cls

    def lookup(self, rule_name, field_names):
        candidates = self._by_rule.get(rule_name)
        if candidates is None:
            raise KeyError(f"No class registered for rule '{rule_name}'")
        key = frozenset(field_names)
        cls = candidates.get(key)
        if cls is None:
            raise KeyError(
                f"No class for rule '{rule_name}' with fields {set(field_names)}"
            )
        return cls

    def deserialize(self, tree):
        from .deserialize import deserialize
        return deserialize(tree, self)
```

- [ ] **Step 4: Run the tests**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k "registry"
```
Expected: all `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd .worktrees/multi-lang
git add src/plcc/lang/ext/python/runtime/registry.py \
        src/plcc/lang/ext/python/runtime/registry_test.py
git commit -m "feat(runtime): add Registry with field-based disambiguation"
```

---

## Task 8: `runtime/deserialize.py` — recursive tree reconstruction

**Files:**
- Create: `src/plcc/lang/ext/python/runtime/deserialize.py`
- Create: `src/plcc/lang/ext/python/runtime/deserialize_test.py`

Tree JSON format (from `plcc-tree`):
- Nonterminal: `{"kind": "tree", "rule": "ExprRest", "children": [["term", {...}], ["rest", {...}]]}`
- Terminal: `{"kind": "token", "name": "NUM", "lexeme": "42", "source": {...}}`
- Children are `[field_name, node]` pairs.

- [ ] **Step 1: Write failing tests**

Create `src/plcc/lang/ext/python/runtime/deserialize_test.py`:
```python
from .deserialize import deserialize
from .registry import Registry
from .base import Node, Token


class FakeProgram(Node):
    _rule_name = 'program'
    _fields = ['num']

    def __init__(self, num):
        self.num = num


class FakeExprRest(Node):
    _rule_name = 'ExprRest'
    _fields = ['term', 'rest']

    def __init__(self, term, rest):
        self.term = term
        self.rest = rest


class FakeNilRest(Node):
    _rule_name = 'ExprRest'
    _fields = []

    def __init__(self):
        pass


def _make_registry():
    reg = Registry()
    reg.register(FakeProgram, FakeExprRest, FakeNilRest)
    return reg


def test_deserialize_token_node():
    tree = {"kind": "token", "name": "NUM", "lexeme": "42"}
    reg = _make_registry()
    result = deserialize(tree, reg)
    assert isinstance(result, Token)
    assert result.kind == 'NUM'
    assert result.lexeme == '42'


def test_deserialize_leaf_nonterminal():
    tree = {"kind": "tree", "rule": "program", "children": [
        ["num", {"kind": "token", "name": "NUM", "lexeme": "7"}]
    ]}
    reg = _make_registry()
    result = deserialize(tree, reg)
    assert isinstance(result, FakeProgram)
    assert isinstance(result.num, Token)
    assert result.num.lexeme == '7'


def test_deserialize_empty_children_nonterminal():
    tree = {"kind": "tree", "rule": "ExprRest", "children": []}
    reg = _make_registry()
    result = deserialize(tree, reg)
    assert isinstance(result, FakeNilRest)


def test_deserialize_nested():
    tree = {"kind": "tree", "rule": "ExprRest", "children": [
        ["term", {"kind": "token", "name": "NUM", "lexeme": "1"}],
        ["rest", {"kind": "tree", "rule": "ExprRest", "children": []}],
    ]}
    reg = _make_registry()
    result = deserialize(tree, reg)
    assert isinstance(result, FakeExprRest)
    assert isinstance(result.term, Token)
    assert isinstance(result.rest, FakeNilRest)
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k "deserialize"
```
Expected: `FAILED`.

- [ ] **Step 3: Implement `deserialize.py`**

Create `src/plcc/lang/ext/python/runtime/deserialize.py`:
```python
from .base import Token


def deserialize(tree, registry):
    if tree['kind'] == 'token':
        return Token(kind=tree['name'], lexeme=tree['lexeme'])

    children = tree.get('children', [])
    field_names = [pair[0] for pair in children]
    cls = registry.lookup(tree['rule'], field_names)
    kwargs = {name: deserialize(node, registry) for name, node in children}
    return cls(**kwargs)
```

- [ ] **Step 4: Run the tests**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k "deserialize"
```
Expected: all `PASSED`.

- [ ] **Step 5: Run all unit tests**

```bash
cd .worktrees/multi-lang && bin/test/units.bash
```
Expected: all `PASSED`.

- [ ] **Step 6: Commit**

```bash
cd .worktrees/multi-lang
git add src/plcc/lang/ext/python/runtime/deserialize.py \
        src/plcc/lang/ext/python/runtime/deserialize_test.py
git commit -m "feat(runtime): add recursive parse-tree deserializer"
```

---

## Task 9: Jinja2 templates — `class_file.py.jinja` and `main.py.jinja`

**Files:**
- Create: `src/plcc/lang/ext/python/templates/class_file.py.jinja`
- Create: `src/plcc/lang/ext/python/templates/main.py.jinja`

Templates are rendered by `emit.py` in Task 10. Create them now with known-good content; the emit tests validate rendering.

- [ ] **Step 1: Create the `templates/` directory and `class_file.py.jinja`**

Create `src/plcc/lang/ext/python/templates/class_file.py.jinja`:

```jinja
{% for frag in top_fragments %}{{ frag.body }}
{% endfor %}
import runtime.base as _plcc
{% if cls.extends %}from {{ cls.extends }} import {{ cls.extends }}
{% endif %}
{% for frag in import_fragments %}{{ frag.body }}
{% endfor %}

class {{ cls.name }}({% if cls.extends %}{{ cls.extends }}{% else %}_plcc.Node{% endif %}{% for frag in class_fragments %}, {{ frag.body }}{% endfor %}):

    _rule_name = {{ cls.rule_name | tojson }}
    _fields = [{% for field in cls.fields %}{{ field.name | tojson }}{% if not loop.last %}, {% endif %}{% endfor %}]

    def __init__(self{% for field in cls.fields %}, {{ field.name }}{% endfor %}):
        super().__init__()
{% for field in cls.fields %}        self.{{ field.name }} = {{ field.name }}
{% endfor %}{% for frag in init_fragments %}        {{ frag.body | indent(8) }}
{% endfor %}
{% for frag in body_fragments %}    {{ frag.body | indent(4) }}

{% endfor %}
```

- [ ] **Step 2: Create `main.py.jinja`**

Create `src/plcc/lang/ext/python/templates/main.py.jinja`:

```jinja
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runtime.registry import Registry
{% for cls in classes %}from {{ cls.name }} import {{ cls.name }}
{% endfor %}

registry = Registry()
registry.register({% for cls in classes if not cls.abstract %}{{ cls.name }}{% if not loop.last %}, {% endif %}{% endfor %})

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

- [ ] **Step 3: Manually test template rendering with Jinja2**

```bash
cd .worktrees/multi-lang
python3 - <<'EOF'
import jinja2, pathlib

tpl_dir = pathlib.Path("src/plcc/lang/ext/python/templates")
env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(tpl_dir)), keep_trailing_newline=True)
tpl = env.get_template("main.py.jinja")
print(tpl.render(
    classes=[
        {"name": "Program", "abstract": False},
        {"name": "ExprRest", "abstract": True},
        {"name": "AddRest", "abstract": False},
    ],
    entry_point="_run"
))
EOF
```
Expected: Python source that imports Program, AddRest (not ExprRest), registers them, and calls `tree._run()`.

- [ ] **Step 4: Commit**

```bash
cd .worktrees/multi-lang
git add src/plcc/lang/ext/python/templates/
git commit -m "feat(templates): add class_file.py.jinja and main.py.jinja"
```

---

## Task 10: Rewrite `plcc-python-emit`

**Files:**
- Modify: `src/plcc/lang/ext/python/emit.py`
- Modify: `src/plcc/lang/ext/python/emit_test.py`
- Delete: `src/plcc/lang/ext/python/runtime/main.py`

- [ ] **Step 1: Write failing tests in `emit_test.py`**

Replace `src/plcc/lang/ext/python/emit_test.py`:
```python
import io
import json
import subprocess
import sys

import pytest
from docopt import DocoptExit

from .emit import main as run_main


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
                "tool": "calculate",
                "entry_point": "_run",
                "fragments": [
                    {"class_name": "Program", "kind": "body", "body": "def _run(self):\n    return self.expr.eval()"},
                    {"class_name": "AddRest", "kind": "body", "body": "def eval(self, acc):\n    return self.rest.eval(acc + self.term.eval())"},
                    {"class_name": "NilRest", "kind": "body", "body": "def eval(self, acc):\n    return acc"},
                    {"class_name": "Term", "kind": "body", "body": "def eval(self):\n    return int(self.num.lexeme)"},
                    {"class_name": "Expr", "kind": "body", "body": "def eval(self):\n    return self.rest.eval(self.term.eval())"},
                ]
            }
        ]
    }


def test_no_args_prints_usage():
    with pytest.raises((DocoptExit, SystemExit)):
        run_main([])


def test_emit_produces_one_py_file_per_class(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    class_names = ["Program", "Expr", "ExprRest", "AddRest", "NilRest", "Term"]
    for name in class_names:
        assert (tmp_path / f'{name}.py').exists(), f"{name}.py missing"


def test_emit_produces_main_py(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'main.py').exists()


def test_emit_copies_runtime_directory(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'runtime' / 'base.py').exists()
    assert (tmp_path / 'runtime' / 'registry.py').exists()
    assert (tmp_path / 'runtime' / 'deserialize.py').exists()


def test_emit_class_file_contains_body_fragment(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    term_py = (tmp_path / 'Term.py').read_text()
    assert 'def eval(self):' in term_py
    assert 'int(self.num.lexeme)' in term_py


def test_emit_class_file_imports_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    program_py = (tmp_path / 'Program.py').read_text()
    assert 'import runtime.base as _plcc' in program_py


def test_emit_subclass_imports_parent(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    addrest_py = (tmp_path / 'AddRest.py').read_text()
    assert 'from ExprRest import ExprRest' in addrest_py


def test_emit_main_py_contains_entry_point(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    main_py = (tmp_path / 'main.py').read_text()
    assert 'tree._run()' in main_py


def test_emit_main_py_entry_point_defaults_to_run_when_null(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['entry_point'] = None
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    main_py = (tmp_path / 'main.py').read_text()
    assert 'tree._run()' in main_py


def test_emit_file_fragment_written_verbatim(tmp_path, monkeypatch):
    model = _arith_model()
    model['semantic_sections'][0]['fragments'].append(
        {"class_name": "Env", "kind": "file", "body": "class Env:\n    pass\n"}
    )
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(model)))
    run_main([f'--output={tmp_path}'])
    env_py = (tmp_path / 'Env.py').read_text()
    assert 'class Env:' in env_py


def test_emit_generated_main_is_runnable(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_arith_model())))
    run_main([f'--output={tmp_path}'])
    result = subprocess.run(
        [sys.executable, str(tmp_path / 'main.py')],
        input='',
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k "emit" 2>&1 | tail -30
```
Expected: most tests `FAILED` (old emit just copies the stub `main.py`).

- [ ] **Step 3: Rewrite `emit.py`**

Replace `src/plcc/lang/ext/python/emit.py`:
```python
"""plcc-python-emit
    Emit a Python interpreter from model JSON.

Usage:
    plcc-python-emit --output=DIR [options]

Options:
    --output=DIR    Directory to write output files into.
    -h --help       Show this message.
"""

import enum
import json
import os
import shutil
import sys
from pathlib import Path

import jinja2
from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = __doc__ + VERBOSE_OPTIONS

_DEFAULT_ENTRY_POINT = '_run'


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-python-emit", Events, args)
    output_dir = Path(args['--output'])
    verbose.emit(Events.STARTED, message=f'emitting to {output_dir}')

    model = json.load(sys.stdin)
    output_dir.mkdir(parents=True, exist_ok=True)

    _copy_runtime(output_dir)

    classes = model['classes']
    section = _find_python_section(model)
    entry_point = (section.get('entry_point') if section else None) or _DEFAULT_ENTRY_POINT
    fragments_by_class = _group_fragments(section.get('fragments', []) if section else [])

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(Path(__file__).parent / 'templates')),
        keep_trailing_newline=True,
    )
    class_template = env.get_template('class_file.py.jinja')
    main_template = env.get_template('main.py.jinja')

    for cls in classes:
        frags = fragments_by_class.get(cls['name'], [])
        content = class_template.render(
            cls=cls,
            top_fragments=[f for f in frags if f['kind'] == 'top'],
            import_fragments=[f for f in frags if f['kind'] == 'import'],
            class_fragments=[f for f in frags if f['kind'] == 'class'],
            init_fragments=[f for f in frags if f['kind'] == 'init'],
            body_fragments=[f for f in frags if f['kind'] == 'body'],
        )
        (output_dir / f"{cls['name']}.py").write_text(content)

    all_frags = section.get('fragments', []) if section else []
    class_names = {c['name'] for c in classes}
    for frag in all_frags:
        if frag['kind'] == 'file':
            (output_dir / f"{frag['class_name']}.py").write_text(frag['body'])

    main_content = main_template.render(classes=classes, entry_point=entry_point)
    (output_dir / 'main.py').write_text(main_content)

    verbose.emit(Events.FINISHED, message='done')


def _copy_runtime(output_dir):
    src = Path(__file__).parent / 'runtime'
    dst = output_dir / 'runtime'
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _find_python_section(model):
    for s in model.get('semantic_sections', []):
        if s.get('language') == 'Python':
            return s
    return None


def _group_fragments(fragments):
    groups = {}
    for frag in fragments:
        groups.setdefault(frag['class_name'], []).append(frag)
    return groups
```

- [ ] **Step 4: Delete the old `runtime/main.py` stub**

```bash
cd .worktrees/multi-lang
git rm src/plcc/lang/ext/python/runtime/main.py
```

- [ ] **Step 5: Run the emit tests**

```bash
cd .worktrees/multi-lang && bin/test/units.bash -k "emit"
```
Expected: all `PASSED`.

- [ ] **Step 6: Run all unit tests**

```bash
cd .worktrees/multi-lang && bin/test/units.bash
```
Expected: all `PASSED`.

- [ ] **Step 7: Commit**

```bash
cd .worktrees/multi-lang
git add src/plcc/lang/ext/python/emit.py \
        src/plcc/lang/ext/python/emit_test.py
git commit -m "feat(plcc-python-emit): full Jinja2-based code generation, one file per class"
```

---

## Task 11: `plcc-python-run` — add `-u` (unbuffered) flag

**Files:**
- Modify: `src/plcc/lang/ext/python/run.py`

Without `-u`, Python uses block buffering when stdout is piped. `plcc-rep` writes to the interpreter and reads back a response — block buffering causes deadlock because the interpreter's `print()` is held in a buffer that never flushes.

- [ ] **Step 1: Add one line to `run.py`**

In `src/plcc/lang/ext/python/run.py`, change:
```python
    result = subprocess.run(
        [sys.executable, main_py],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
```
to:
```python
    result = subprocess.run(
        [sys.executable, '-u', main_py],
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
```

- [ ] **Step 2: Manually verify the `-u` flag is passed**

```bash
cd .worktrees/multi-lang
TMP="$(mktemp -d)"
plcc-spec tests/fixtures/trivial-python.plcc | plcc-model | plcc-python-emit --output="${TMP}"
TREE='{"kind":"tree","rule":"program","children":[["num",{"kind":"token","name":"NUM","lexeme":"7"}]]}'
echo "${TREE}" | plcc-python-run --output="${TMP}"
rm -rf "${TMP}"
```
Expected: `{"kind": "result", "value": "7"}`.

- [ ] **Step 3: Run all unit tests**

```bash
cd .worktrees/multi-lang && bin/test/units.bash
```
Expected: all `PASSED`.

- [ ] **Step 4: Commit**

```bash
cd .worktrees/multi-lang
git add src/plcc/lang/ext/python/run.py
git commit -m "fix(plcc-python-run): add -u flag to prevent buffering deadlock in plcc-rep"
```

---

## Task 12: Rewrite `plcc-rep` as interactive REPL

**Files:**
- Modify: `src/plcc/cmd/rep.py`

`plcc-rep` no longer builds the language. It uses pre-built `build/` artifacts and keeps the interpreter subprocess alive for the whole session.

- [ ] **Step 1: Write the new `rep.py`**

Replace `src/plcc/cmd/rep.py` entirely:
```python
import enum
import json
import os
import subprocess
import sys

from docopt import docopt

from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-rep
    REPL — read, eval, print loop for a PLCC grammar.

Usage:
    plcc-rep [options] GRAMMAR [SOURCE ...]

Arguments:
    GRAMMAR     Path to the PLCC grammar file (used to locate build/).
    SOURCE      Source files to evaluate before entering interactive mode.

Options:
    --tool=NAME         Semantic section to run (inferred if only one exists).
    --verbose-format=FMT  Output format: text or json [default: text].
    -h --help           Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-rep", Events, args)
    sources = args['SOURCE']
    tool_name = args['--tool']
    verbose_format = args['--verbose-format'] or 'text'

    verbose.emit(Events.STARTED, message='starting rep')

    spec_path = os.path.join('build', 'spec.json')
    ll1_path = os.path.join('build', 'll1.json')

    if not os.path.exists(spec_path) or not os.path.exists(ll1_path):
        print('plcc-rep: build/ not found. Run plcc-make first.', file=sys.stderr)
        sys.exit(1)

    with open(spec_path) as f:
        spec = json.load(f)

    tool_name, language = _resolve_tool(spec, tool_name)
    tool_dir = os.path.join('build', tool_name)

    if not os.path.exists(tool_dir):
        print(f'plcc-rep: build/{tool_name}/ not found. Run plcc-make first.', file=sys.stderr)
        sys.exit(1)

    interpreter = subprocess.Popen(
        ['plcc-lang-run', f'--target={language}', f'--output={tool_dir}'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None,
    )

    try:
        for src in sources:
            with open(src, 'rb') as f:
                chunk = f.read()
            _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format)

        if not sources:
            interactive = sys.stdin.isatty()
            if interactive:
                while True:
                    try:
                        print('>>> ', end='', flush=True, file=sys.stderr)
                        line = sys.stdin.readline()
                        if not line:
                            break
                        chunk = line.encode()
                        _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format)
                    except KeyboardInterrupt:
                        print(file=sys.stderr)
                        break
            else:
                chunk = sys.stdin.buffer.read()
                if chunk.strip():
                    _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format)
    finally:
        try:
            interpreter.stdin.close()
        except BrokenPipeError:
            pass
        interpreter.wait()

    verbose.emit(Events.FINISHED, message='done')


def _resolve_tool(spec, tool_name):
    sections = spec.get('semantics', [])
    if tool_name:
        for s in sections:
            if s['tool'] == tool_name:
                return s['tool'], s['language']
        print(f"plcc-rep: no semantic section with tool '{tool_name}'", file=sys.stderr)
        sys.exit(1)

    if len(sections) == 1:
        return sections[0]['tool'], sections[0]['language']

    names = [s['tool'] for s in sections]
    print(f"plcc-rep: multiple semantic sections: {names}. Use --tool=NAME.", file=sys.stderr)
    sys.exit(1)


def _eval_chunk(chunk, interpreter, spec_path, ll1_path, verbose_format):
    tokens_proc = subprocess.Popen(
        ['plcc-tokens', spec_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    tree_proc = subprocess.Popen(
        ['plcc-tree', f'--ll1={ll1_path}'],
        stdin=tokens_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    tokens_proc.stdout.close()
    tokens_proc.stdin.write(chunk)
    tokens_proc.stdin.close()

    tree_out, _ = tree_proc.communicate()
    tokens_proc.wait()

    if tokens_proc.returncode != 0 or tree_proc.returncode != 0:
        print('plcc-rep: parse error', file=sys.stderr)
        return

    tree_line = tree_out.strip()
    if not tree_line:
        return

    interpreter.stdin.write(tree_line + b'\n')
    interpreter.stdin.flush()

    _read_response(interpreter.stdout, verbose_format)


def _read_response(stdout, verbose_format):
    while True:
        raw = stdout.readline()
        if not raw:
            print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
            sys.exit(1)
        line = raw.decode('utf-8', errors='replace').rstrip('\n')
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            print(line)
            continue
        if 'kind' not in record:
            print(line)
            continue
        _render_record(record, verbose_format)
        return


def _render_record(record, verbose_format):
    if verbose_format == 'json':
        print(json.dumps(record))
        return
    if record['kind'] == 'result':
        value = record.get('value')
        if value is not None:
            print(value)
    elif record['kind'] == 'error':
        print(f"error: {record.get('type')}: {record.get('message')}", file=sys.stderr)
```

- [ ] **Step 2: Run all unit tests**

```bash
cd .worktrees/multi-lang && bin/test/units.bash
```
Expected: all `PASSED` (rep.py has no unit tests — tested via bats in Tasks 13-14).

- [ ] **Step 3: Smoke test manually (requires `plcc-make` to have been run)**

```bash
cd .worktrees/multi-lang
TMP="$(mktemp -d)"
(
    cd "${TMP}"
    plcc-make "$(git rev-parse --show-toplevel)/tests/fixtures/arith.plcc"
    echo "1 + 2" | plcc-rep arith.plcc
)
rm -rf "${TMP}"
```
Expected: `3`.

- [ ] **Step 4: Commit**

```bash
cd .worktrees/multi-lang
git add src/plcc/cmd/rep.py
git commit -m "feat(plcc-rep): rewrite as interactive REPL using pre-built build/ artifacts"
```

---

## Task 13: Integration bats test — `python-emit.bats`

**Files:**
- Create: `tests/bats/integration/python-emit.bats`

- [ ] **Step 1: Create `tests/bats/integration/python-emit.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    WORK_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/arith.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-python-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}" "${MODEL_JSON}"
    rm -rf "${WORK_DIR}"
}

@test "emit produces one py file per class" {
    for name in Program Expr ExprRest AddRest NilRest Term; do
        [ -f "${WORK_DIR}/${name}.py" ]
    done
}

@test "emit produces main.py" {
    [ -f "${WORK_DIR}/main.py" ]
}

@test "emit copies runtime directory" {
    [ -f "${WORK_DIR}/runtime/base.py" ]
    [ -f "${WORK_DIR}/runtime/registry.py" ]
    [ -f "${WORK_DIR}/runtime/deserialize.py" ]
}

@test "main.py evaluates 1+2 to 3 via plcc-python-run" {
    TREE_JSON="$(
        echo '1 + 2' \
        | plcc-tokens "${SPEC_JSON}" \
        | plcc-tree --ll1=<(plcc-ll1 < "${SPEC_JSON}")
    )"
    run bash -c "echo '${TREE_JSON}' | plcc-python-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"value"'* ]]
    [[ "$output" == *'3'* ]]
}

@test "main.py is runnable standalone" {
    run python3 "${WORK_DIR}/main.py" <<< ""
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 2: Run the integration tests**

```bash
cd .worktrees/multi-lang && bin/test/integration.bash 2>&1 | tail -30
```
Expected: new `python-emit.bats` tests `PASSED`; existing integration tests unchanged.

- [ ] **Step 3: Run the command tests (verifies `plcc-python-run.bats` fix from Task 5)**

```bash
cd .worktrees/multi-lang && bin/test/commands.bash 2>&1 | tail -20
```
Expected: `plcc-python-run.bats` tests `PASSED`.

- [ ] **Step 4: Commit**

```bash
cd .worktrees/multi-lang
git add tests/bats/integration/python-emit.bats
git commit -m "test(integration): add python-emit.bats end-to-end emit + run tests"
```

---

## Task 14: e2e bats test — `plcc-rep.bats`

**Files:**
- Create: `tests/bats/e2e/plcc-rep.bats`

- [ ] **Step 1: Create `tests/bats/e2e/plcc-rep.bats`**

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    plcc-make "${FIXTURES}/arith.plcc"
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-rep is on PATH" {
    command -v plcc-rep
}

@test "plcc-rep evaluates 1+2 to 3 in batch mode" {
    run bash -c "echo '1 + 2' | plcc-rep '${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == "3" ]]
}

@test "plcc-rep evaluates file argument" {
    echo '1 + 2' > input.txt
    run plcc-rep "${FIXTURES}/arith.plcc" input.txt
    [ "$status" -eq 0 ]
    [[ "$output" == "3" ]]
}

@test "plcc-rep continues after a parse error" {
    run bash -c "printf '1 + 2\nbad input here\n' | plcc-rep '${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == "3" ]]
}

@test "plcc-rep emits json eval record with --verbose-format=json" {
    run bash -c "echo '1 + 2' | plcc-rep --verbose-format=json '${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"result"'* ]]
    [[ "$output" == *'3'* ]]
}

@test "plcc-rep exits non-zero without build/" {
    EMPTY_DIR="$(mktemp -d)"
    run bash -c "cd '${EMPTY_DIR}' && plcc-rep '${FIXTURES}/arith.plcc'"
    [ "$status" -ne 0 ]
    [[ "$output" == *"plcc-make"* ]] || [[ "${lines[*]}" == *"plcc-make"* ]]
    rm -rf "${EMPTY_DIR}"
}

@test "plcc-make arith produces build/calculate/" {
    [ -d build/calculate ]
    [ -f build/calculate/main.py ]
    [ -f build/calculate/Program.py ]
}

@test "standalone invocation: plcc-tokens | plcc-tree | python main.py" {
    echo '1 + 2' \
    | plcc-tokens build/spec.json \
    | plcc-tree --ll1=build/ll1.json \
    | python3 -u build/calculate/main.py \
    | python3 -c "import json,sys; r=json.loads(sys.stdin.read()); assert r['value']=='3', r"
}
```

- [ ] **Step 2: Run the e2e tests**

```bash
cd .worktrees/multi-lang && bin/test/e2e.bash 2>&1 | tail -30
```
Expected: all `plcc-rep.bats` tests `PASSED`; existing e2e tests unchanged.

- [ ] **Step 3: Run the full test suite**

```bash
cd .worktrees/multi-lang && bin/test/all.bash 2>&1 | tail -40
```
Expected: all tests `PASSED`.

- [ ] **Step 4: Commit**

```bash
cd .worktrees/multi-lang
git add tests/bats/e2e/plcc-rep.bats
git commit -m "test(e2e): add plcc-rep.bats end-to-end REPL acceptance tests"
```

---

## Self-Review

Spec sections checked against plan tasks:

| Spec section | Task |
|---|---|
| §4 entry-point declaration in `plcc-spec` | Task 1 |
| §4.4 `spec.json` `entry_point` field | Tasks 1–2 |
| §5 `model.json` `entry_point` pass-through | Task 3 |
| §6 `arith.plcc` fixture update | Task 4 |
| §7.1 one `.py` per class | Task 10 |
| §7.2 plugin source layout + templates | Tasks 9–10 |
| §7.3 `import runtime.base as _plcc` | Task 9 template |
| §7.4 `class_file.py.jinja` | Task 9 |
| §7.5 `file` fragments written verbatim | Task 10 |
| §7.6 `main.py.jinja` | Task 9 |
| §7.7 `-u` flag | Task 11 |
| §8 runtime library (base, registry, deserialize) | Tasks 6–8 |
| §9 eval record schema | Tasks 9–10 |
| §10 `plcc-rep` REPL | Task 12 |
| §11 acceptance criteria 1–12 | Tasks 1–14 |

**No placeholders found.**

**Type consistency verified:** `rule_name` added in Task 3 (`build_model.py`) is consumed in Task 10 (`emit.py` → `class_file.py.jinja` sets `_rule_name = cls.rule_name`); `Registry.lookup` uses `_rule_name`/`_fields` set in template.

**Scope:** all 12 acceptance criteria in the spec are covered. Out-of-scope items (`plcc-make` diagram integration, Java emitter) are untouched.
