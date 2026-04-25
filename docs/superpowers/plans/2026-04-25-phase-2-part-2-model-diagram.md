# Phase 2 Part 2: Code Model and Diagram System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement full `plcc-model` (inheritance + semantic pass-through), the `plcc-diagram-*` plugin system, retire `plcc-plantuml-emit`, and validate end-to-end with an arithmetic grammar fixture.

**Architecture:** `plcc-model` reads spec JSON and emits `model.json` with a full class hierarchy (abstract bases + concrete subclasses) and opaque semantic fragments. Three new commands (`plcc-diagram`, `plcc-diagram-list`, `plcc-plantuml-diagram`) form a plugin namespace parallel to `plcc-lang-*`. The old `plcc-plantuml-emit` language plugin is deleted; the diagram system replaces it.

**Tech Stack:** Python 3.12, docopt-ng, pytest, pyfakefs (tests), bats (command tests), check-jsonschema (schema validation), JSON Schema draft-07.

---

## Spec Reference

Design doc: `docs/superpowers/specs/2026-04-25-phase-2-part-2-model-diagram-design.md`

Key facts about the spec JSON produced by `plcc-spec`:

- `spec.syntax.rules[i].lhs.altName` — alternative class name (e.g. `"AddRest"` from `<ExprRest>:AddRest`); `null` when no alternative
- `spec.syntax.rules[i].rhsSymbolList[j].altName` — field name for capturing symbols (e.g. `"expr"` from `<Expr>expr`)
- `spec.syntax.rules[i].rhsSymbolList[j].isCapturing` — `true` iff symbol generates a field
- `spec.syntax.rules[i].rhsSymbolList[j].isTerminal` — `true` for tokens, `false` for nonterminals
- `spec.semantics[i].codeFragmentList[j].targetLocator.className` — free-form string (class name or file stem)
- `spec.semantics[i].codeFragmentList[j].targetLocator.modifier` — one of `"top"`, `"import"`, `"class"`, `"init"`, or `null`
- `spec.semantics[i].codeFragmentList[j].block.lines` — array of `{"string": "...", "number": N, "file": ...}`; first and last lines are `"%%%"` delimiters

A bare `%` separator in a PLCC grammar produces a default `{"language": "Java", "tool": "Java", ...}` semantic section. This is by design and `build_model` must handle it (it will produce a semantic section with `fragments: []`).

---

## File Map

### New files
| File | Role |
| --- | --- |
| `tests/fixtures/arith.plcc` | Test grammar fixture (arithmetic evaluator) |
| `src/plcc/diagram/__init__.py` | Package marker |
| `src/plcc/diagram/list.py` | `plcc-diagram-list` command |
| `src/plcc/diagram/list_test.py` | Unit tests for list |
| `src/plcc/diagram/dispatch.py` | `plcc-diagram` dispatcher |
| `src/plcc/diagram/dispatch_test.py` | Unit tests for dispatcher |
| `src/plcc/diagram/plantuml/__init__.py` | Package marker |
| `src/plcc/diagram/plantuml/emit.py` | `plcc-plantuml-diagram` command |
| `src/plcc/diagram/plantuml/emit_test.py` | Unit tests for plantuml emitter |
| `tests/bats/commands/plcc-diagram.bats` | Command-level bats tests |
| `tests/bats/commands/plcc-diagram-list.bats` | Command-level bats tests |
| `tests/bats/commands/plcc-plantuml-diagram.bats` | Command-level bats tests |

### Modified files
| File | Change |
| --- | --- |
| `src/plcc/schemas/model.schema.json` | Add `abstract` (required), `fragments` to semantic sections, remove `methods` |
| `src/plcc/model/build_model.py` | Full class derivation with inheritance; full semantic pass-through |
| `src/plcc/model/build_model_test.py` | Add tests for inheritance + semantic fragments; update fixture |
| `pyproject.toml` | Add 3 new scripts; remove `plcc-plantuml-emit` |
| `tests/fixtures/trivial.plcc` | Remove `% diagram PlantUML` line |
| `tests/fixtures/trivial-full.plcc` | Remove `% diagram PlantUML` line |
| `tests/bats/commands/plcc-lang-list.bats` | Remove "finds plantuml" test |
| `tests/bats/integration/model-lang-emit.bats` | Remove or replace plantuml test |
| `tests/bats/e2e/happy-path.bats` | Replace plantuml-emit tests with diagram pipeline tests |

### Deleted files
| File | Reason |
| --- | --- |
| `src/plcc/lang/ext/plantuml/emit.py` | `plcc-plantuml-emit` retired |
| `src/plcc/lang/ext/plantuml/emit_test.py` | Retired with plugin |
| `tests/bats/commands/plcc-plantuml-emit.bats` | Retired with plugin |
| `tests/fixtures/plantuml_only.plcc` | Only used by retired smoke test path |
| `tests/fixtures/trivial-plantuml.plcc` | Only existed to test plantuml plugin |

---

## Task 1: Create the arith.plcc fixture

**Files:**
- Create: `tests/fixtures/arith.plcc`

- [ ] **Step 1: Write the fixture**

```
tests/fixtures/arith.plcc
```

```text
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
% calculate Python
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

- [ ] **Step 2: Verify it parses without error**

```bash
plcc-spec tests/fixtures/arith.plcc > /dev/null
echo "exit: $?"
```
Expected: `exit: 0`

- [ ] **Step 3: Verify it is LL(1)**

```bash
plcc-spec tests/fixtures/arith.plcc | plcc-ll1 | python3 -c "import json,sys; d=json.load(sys.stdin); print('is_ll1:', d['is_ll1'])"
```
Expected: `is_ll1: True`

- [ ] **Step 4: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add tests/fixtures/arith.plcc
git -C "$(git rev-parse --show-toplevel)" commit -m "test(fixtures): add arith.plcc arithmetic evaluator grammar"
```

---

## Task 2: Update model.schema.json

Add `abstract` (required) to class objects, add `fragments` to semantic sections (optional, for now), remove `methods`.

**Files:**
- Modify: `src/plcc/schemas/model.schema.json`

- [ ] **Step 1: Write failing test expectation (schema)**

Run the current model output through the CURRENT schema — it passes. After this task the schema will require `abstract`, which current output does not have. We update the schema first so the test suite fails, then fix `build_model` in Task 3.

```bash
plcc-spec tests/fixtures/trivial.plcc | plcc-model | check-jsonschema --schemafile src/plcc/schemas/model.schema.json -
echo "Schema validation exit: $?"
```
Expected now: `exit: 0` (passes with old schema)

- [ ] **Step 2: Update the schema**

Replace `src/plcc/schemas/model.schema.json` with:

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
        "required": ["name", "abstract", "fields"],
        "properties": {
          "name":     { "type": "string" },
          "abstract": { "type": "boolean" },
          "extends":  { "type": ["string", "null"] },
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
          "tool":     { "type": "string" },
          "language": { "type": "string" },
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

- [ ] **Step 3: Confirm schema validation now fails**

```bash
plcc-spec tests/fixtures/trivial.plcc | plcc-model | check-jsonschema --schemafile src/plcc/schemas/model.schema.json -
echo "Schema validation exit: $?"
```
Expected: `exit: 1` (fails because `abstract` is now required and `fragments` is now required but current output lacks both)

- [ ] **Step 4: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/schemas/model.schema.json
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(schema): update model schema for abstract classes and semantic fragments"
```

---

## Task 3: Implement class derivation with inheritance in build_model

Groups syntax rules by nonterminal name, detects abstract nonterminals (any rule with non-null `altName`), and emits abstract base + concrete subclasses.

**Files:**
- Modify: `src/plcc/model/build_model.py`
- Modify: `src/plcc/model/build_model_test.py`

- [ ] **Step 1: Write failing tests**

Add these tests to `src/plcc/model/build_model_test.py`. These test the inheritance model using a handcrafted spec dict that mirrors what `plcc-spec arith.plcc` produces.

Append to `src/plcc/model/build_model_test.py`:

```python
_ARITH_SPEC = {
    "lexical": {"ruleList": []},
    "syntax": {
        "rules": [
            {
                "lhs": {"name": "program", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "Expr", "isTerminal": False, "isCapturing": True, "altName": "expr"}
                ]
            },
            {
                "lhs": {"name": "Expr", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "Term", "isTerminal": False, "isCapturing": True, "altName": "term"},
                    {"name": "ExprRest", "isTerminal": False, "isCapturing": True, "altName": "rest"}
                ]
            },
            {
                "lhs": {"name": "ExprRest", "altName": "AddRest", "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "PLUS", "isTerminal": True, "isCapturing": False},
                    {"name": "Term", "isTerminal": False, "isCapturing": True, "altName": "term"},
                    {"name": "ExprRest", "isTerminal": False, "isCapturing": True, "altName": "rest"}
                ]
            },
            {
                "lhs": {"name": "ExprRest", "altName": "NilRest", "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": []
            },
            {
                "lhs": {"name": "Term", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "NUM", "isTerminal": True, "isCapturing": True, "altName": "num"}
                ]
            }
        ]
    },
    "semantics": [
        {"language": "Python", "tool": "calculate", "codeFragmentList": []}
    ]
}


def test_trivial_class_has_abstract_false():
    model = build_model(_TRIVIAL_SPEC)
    assert model['classes'][0]['abstract'] == False


def test_trivial_class_has_no_methods_key():
    model = build_model(_TRIVIAL_SPEC)
    assert 'methods' not in model['classes'][0]


def test_arith_start_is_program():
    model = build_model(_ARITH_SPEC)
    assert model['start'] == 'program'


def test_arith_exprrest_is_abstract():
    model = build_model(_ARITH_SPEC)
    exprrest = next(c for c in model['classes'] if c['name'] == 'ExprRest')
    assert exprrest['abstract'] == True


def test_arith_exprrest_has_no_fields():
    model = build_model(_ARITH_SPEC)
    exprrest = next(c for c in model['classes'] if c['name'] == 'ExprRest')
    assert exprrest['fields'] == []


def test_arith_exprrest_extends_none():
    model = build_model(_ARITH_SPEC)
    exprrest = next(c for c in model['classes'] if c['name'] == 'ExprRest')
    assert exprrest['extends'] is None


def test_arith_addrest_is_concrete():
    model = build_model(_ARITH_SPEC)
    addrest = next(c for c in model['classes'] if c['name'] == 'AddRest')
    assert addrest['abstract'] == False


def test_arith_addrest_extends_exprrest():
    model = build_model(_ARITH_SPEC)
    addrest = next(c for c in model['classes'] if c['name'] == 'AddRest')
    assert addrest['extends'] == 'ExprRest'


def test_arith_addrest_has_term_and_rest_fields():
    model = build_model(_ARITH_SPEC)
    addrest = next(c for c in model['classes'] if c['name'] == 'AddRest')
    field_names = [f['name'] for f in addrest['fields']]
    assert 'term' in field_names
    assert 'rest' in field_names


def test_arith_nilrest_extends_exprrest():
    model = build_model(_ARITH_SPEC)
    nilrest = next(c for c in model['classes'] if c['name'] == 'NilRest')
    assert nilrest['extends'] == 'ExprRest'


def test_arith_nilrest_has_no_fields():
    model = build_model(_ARITH_SPEC)
    nilrest = next(c for c in model['classes'] if c['name'] == 'NilRest')
    assert nilrest['fields'] == []


def test_arith_term_has_token_field():
    model = build_model(_ARITH_SPEC)
    term = next(c for c in model['classes'] if c['name'] == 'Term')
    fields = {f['name']: f['type'] for f in term['fields']}
    assert fields.get('num') == 'Token'


def test_arith_abstract_before_concrete():
    model = build_model(_ARITH_SPEC)
    names = [c['name'] for c in model['classes']]
    assert names.index('ExprRest') < names.index('AddRest')
    assert names.index('ExprRest') < names.index('NilRest')


def test_arith_expr_extends_none():
    model = build_model(_ARITH_SPEC)
    expr = next(c for c in model['classes'] if c['name'] == 'Expr')
    assert expr['extends'] is None
    assert expr['abstract'] == False
```

- [ ] **Step 2: Run failing tests**

```bash
bin/test/units.bash 2>&1 | tail -30
```
Expected: multiple `FAILED` for the new test functions (`test_trivial_class_has_abstract_false`, `test_arith_*`).

- [ ] **Step 3: Implement `_build_classes` with inheritance**

Replace `src/plcc/model/build_model.py` with:

```python
"""Transform spec JSON into a language-neutral code model."""


def build_model(spec):
    classes = _build_classes(spec)
    known_class_names = {c['name'] for c in classes}
    semantic_sections = _build_semantic_sections(spec, known_class_names)
    start = _find_start(spec)
    return {
        'start': start,
        'classes': classes,
        'semantic_sections': semantic_sections,
    }


def _find_start(spec):
    rules = spec.get('syntax', {}).get('rules', [])
    if not rules:
        return None
    return rules[0]['lhs']['name']


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
            })
            for rule in nt_rules:
                alt_name = rule['lhs']['altName']
                classes.append({
                    'name': alt_name,
                    'abstract': False,
                    'extends': class_name,
                    'fields': _extract_fields(rule.get('rhsSymbolList', [])),
                })
        else:
            rule = nt_rules[0]
            classes.append({
                'name': class_name,
                'abstract': False,
                'extends': None,
                'fields': _extract_fields(rule.get('rhsSymbolList', [])),
            })

    return classes


def _extract_fields(rhs_symbol_list):
    fields = []
    for symbol in rhs_symbol_list:
        if not symbol.get('isCapturing'):
            continue
        field_name = symbol.get('altName') or symbol.get('name', '').lower()
        if symbol.get('isTerminal'):
            field_type = 'Token'
        else:
            name = symbol.get('name', 'Object')
            field_type = name[:1].upper() + name[1:]
        fields.append({'name': field_name, 'type': field_type})
    return fields


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
            'fragments': fragments,
        })
    return sections


def _build_fragment(frag, known_class_names):
    locator = frag.get('targetLocator') or {}
    class_name = locator.get('className', '')
    modifier = locator.get('modifier')
    kind = _compute_kind(modifier, class_name, known_class_names)
    body = _extract_body((frag.get('block') or {}).get('lines', []))
    return {
        'class_name': class_name,
        'kind': kind,
        'body': body,
    }


def _compute_kind(modifier, class_name, known_class_names):
    if modifier in ('top', 'import', 'class', 'init'):
        return modifier
    if class_name in known_class_names:
        return 'body'
    return 'file'


def _extract_body(lines):
    strings = [line['string'] for line in lines]
    if strings and strings[0] == '%%%':
        strings = strings[1:]
    if strings and strings[-1] == '%%%':
        strings = strings[:-1]
    return '\n'.join(strings)
```

- [ ] **Step 4: Run tests and confirm they pass**

```bash
bin/test/units.bash 2>&1 | tail -20
```
Expected: all `test_arith_*` and `test_trivial_*` tests pass. The bats schema test (`plcc-model output validates against model schema`) still fails (the bats tests run separately — this is expected until schema-level fixes are in).

Run just the unit tests for build_model:
```bash
pytest src/plcc/model/build_model_test.py -v 2>&1 | tail -30
```
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/model/build_model.py src/plcc/model/build_model_test.py
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(model): implement class inheritance derivation in build_model"
```

---

## Task 4: Add semantic fragment pass-through to build_model

The `_build_semantic_sections` skeleton is already in place from Task 3. This task adds test coverage for the fragment logic: `kind` computation and `body` extraction.

**Files:**
- Modify: `src/plcc/model/build_model_test.py`

- [ ] **Step 1: Write failing tests for semantic fragments**

Append to `src/plcc/model/build_model_test.py`:

```python
_ARITH_SPEC_WITH_FRAGMENTS = {
    "lexical": {"ruleList": []},
    "syntax": {
        "rules": [
            {
                "lhs": {"name": "program", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": []
            },
            {
                "lhs": {"name": "ExprRest", "altName": "AddRest", "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": []
            }
        ]
    },
    "semantics": [
        {
            "language": "Python",
            "tool": "calculate",
            "codeFragmentList": [
                {
                    "targetLocator": {"className": "AddRest", "modifier": None},
                    "block": {"lines": [
                        {"string": "%%%"},
                        {"string": "def eval(self, acc):"},
                        {"string": "    return acc"},
                        {"string": "%%%"}
                    ]}
                },
                {
                    "targetLocator": {"className": "Helper", "modifier": None},
                    "block": {"lines": [
                        {"string": "%%%"},
                        {"string": "class Helper: pass"},
                        {"string": "%%%"}
                    ]}
                },
                {
                    "targetLocator": {"className": "AddRest", "modifier": "import"},
                    "block": {"lines": [
                        {"string": "%%%"},
                        {"string": "import os"},
                        {"string": "%%%"}
                    ]}
                },
                {
                    "targetLocator": {"className": "AddRest", "modifier": "top"},
                    "block": {"lines": [{"string": "%%%"}, {"string": "# top"}, {"string": "%%%"}]}
                },
                {
                    "targetLocator": {"className": "AddRest", "modifier": "class"},
                    "block": {"lines": [{"string": "%%%"}, {"string": "(Mixin)"}, {"string": "%%%"}]}
                },
                {
                    "targetLocator": {"className": "AddRest", "modifier": "init"},
                    "block": {"lines": [{"string": "%%%"}, {"string": "self.x = 1"}, {"string": "%%%"}]}
                }
            ]
        }
    ]
}


def _get_fragments(spec=_ARITH_SPEC_WITH_FRAGMENTS, section_index=0):
    model = build_model(spec)
    return model['semantic_sections'][section_index]['fragments']


def test_fragment_kind_body_for_known_class():
    frags = _get_fragments()
    addrest_body = next(f for f in frags if f['class_name'] == 'AddRest' and f['kind'] == 'body')
    assert addrest_body['kind'] == 'body'


def test_fragment_kind_file_for_unknown_class():
    frags = _get_fragments()
    helper = next(f for f in frags if f['class_name'] == 'Helper')
    assert helper['kind'] == 'file'


def test_fragment_kind_import_from_modifier():
    frags = _get_fragments()
    import_frag = next(f for f in frags if f['kind'] == 'import')
    assert import_frag['class_name'] == 'AddRest'


def test_fragment_kind_top_from_modifier():
    frags = _get_fragments()
    top_frag = next(f for f in frags if f['kind'] == 'top')
    assert top_frag['class_name'] == 'AddRest'


def test_fragment_kind_class_from_modifier():
    frags = _get_fragments()
    class_frag = next(f for f in frags if f['kind'] == 'class')
    assert class_frag['class_name'] == 'AddRest'


def test_fragment_kind_init_from_modifier():
    frags = _get_fragments()
    init_frag = next(f for f in frags if f['kind'] == 'init')
    assert init_frag['class_name'] == 'AddRest'


def test_fragment_body_strips_percent_markers():
    frags = _get_fragments()
    addrest_body = next(f for f in frags if f['class_name'] == 'AddRest' and f['kind'] == 'body')
    assert addrest_body['body'] == 'def eval(self, acc):\n    return acc'


def test_fragment_body_preserves_indentation():
    frags = _get_fragments()
    addrest_body = next(f for f in frags if f['class_name'] == 'AddRest' and f['kind'] == 'body')
    assert '    return acc' in addrest_body['body']


def test_fragment_class_name_passed_verbatim():
    frags = _get_fragments()
    helper = next(f for f in frags if f['class_name'] == 'Helper')
    assert helper['class_name'] == 'Helper'


def test_semantic_section_has_fragments_key():
    model = build_model(_ARITH_SPEC_WITH_FRAGMENTS)
    assert 'fragments' in model['semantic_sections'][0]


def test_empty_codeFragmentList_gives_empty_fragments():
    spec = {
        "lexical": {"ruleList": []},
        "syntax": {"rules": []},
        "semantics": [{"language": "Java", "tool": "Java", "codeFragmentList": []}]
    }
    model = build_model(spec)
    assert model['semantic_sections'][0]['fragments'] == []
```

- [ ] **Step 2: Run failing tests**

```bash
pytest src/plcc/model/build_model_test.py -v -k "fragment" 2>&1 | tail -20
```
Expected: tests pass (the implementation was already written in Task 3 — these tests verify it). If any fail, the issue is in `_build_fragment`, `_compute_kind`, or `_extract_body`.

- [ ] **Step 3: Verify schema validation now passes**

```bash
plcc-spec tests/fixtures/arith.plcc | plcc-model | check-jsonschema --schemafile src/plcc/schemas/model.schema.json -
echo "exit: $?"
```
Expected: `exit: 0`

Also verify trivial.plcc:
```bash
plcc-spec tests/fixtures/trivial.plcc | plcc-model | check-jsonschema --schemafile src/plcc/schemas/model.schema.json -
echo "exit: $?"
```
Expected: `exit: 0`

- [ ] **Step 4: Run all unit tests**

```bash
bin/test/units.bash 2>&1 | tail -10
```
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/model/build_model_test.py
git -C "$(git rev-parse --show-toplevel)" commit -m "test(model): add fragment pass-through tests for build_model"
```

---

## Task 5: Create plcc-diagram-list

Scans PATH for executables matching `plcc-*-diagram` and prints one format name per line.

**Files:**
- Create: `src/plcc/diagram/__init__.py`
- Create: `src/plcc/diagram/list.py`
- Create: `src/plcc/diagram/list_test.py`
- Create: `tests/bats/commands/plcc-diagram-list.bats`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing unit test**

Create `src/plcc/diagram/__init__.py` (empty file).

Create `src/plcc/diagram/list_test.py`:

```python
from .list import find_formats, extract_format_name


def test_extract_format_name_plantuml():
    assert extract_format_name('plcc-plantuml-diagram') == 'plantuml'


def test_extract_format_name_mermaid():
    assert extract_format_name('plcc-mermaid-diagram') == 'mermaid'


def test_extract_ignores_dispatcher():
    assert extract_format_name('plcc-diagram') is None


def test_extract_ignores_non_matching():
    assert extract_format_name('plcc-diagram-list') is None
    assert extract_format_name('python') is None


def test_find_formats_returns_list(monkeypatch):
    monkeypatch.setenv('PATH', '/fake/bin')
    result = find_formats()
    assert isinstance(result, list)


def test_main_prints_sorted_formats(capsys, monkeypatch):
    from .list import main
    monkeypatch.setattr('plcc.diagram.list.find_formats', lambda: ['plantuml', 'mermaid'])
    main([])
    out, _ = capsys.readouterr()
    assert out.splitlines() == ['mermaid', 'plantuml']
```

- [ ] **Step 2: Run failing test**

```bash
pytest src/plcc/diagram/list_test.py -v 2>&1 | tail -10
```
Expected: `ImportError` — module does not exist yet.

- [ ] **Step 3: Implement list.py**

Create `src/plcc/diagram/list.py`:

```python
import enum
import os
import re
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram-list
    List installed diagram plugins.

Usage:
    plcc-diagram-list [options]

Options:
    -h --help   Show this message.
""" + VERBOSE_OPTIONS

_DIAGRAM_PATTERN = re.compile(r'^plcc-(.+)-diagram$')


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram-list", Events, args)
    for fmt in sorted(find_formats()):
        print(fmt)


def find_formats():
    """Scan PATH for plcc-*-diagram commands; return list of format names."""
    formats = []
    seen = set()
    for directory in _path_dirs():
        try:
            for entry in os.scandir(directory):
                name = extract_format_name(entry.name)
                if name and name not in seen and _is_executable(entry):
                    formats.append(name)
                    seen.add(name)
        except (PermissionError, FileNotFoundError):
            continue
    return formats


def extract_format_name(command_name):
    """Return format name from plcc-<fmt>-diagram command name, or None."""
    m = _DIAGRAM_PATTERN.match(command_name)
    if m:
        fmt = m.group(1)
        if fmt != 'diagram':
            return fmt
    return None


def _path_dirs():
    return os.environ.get('PATH', '').split(os.pathsep)


def _is_executable(entry):
    return entry.is_file() and os.access(entry.path, os.X_OK)
```

- [ ] **Step 4: Register in pyproject.toml**

In `pyproject.toml`, add to `[project.scripts]`:
```toml
plcc-diagram-list = "plcc.diagram.list:main"
```

Reinstall:
```bash
pip install -e . -q
```

- [ ] **Step 5: Run unit tests**

```bash
pytest src/plcc/diagram/list_test.py -v 2>&1 | tail -15
```
Expected: all PASS.

- [ ] **Step 6: Write bats command test**

Create `tests/bats/commands/plcc-diagram-list.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-list is on PATH" { command -v plcc-diagram-list; }

@test "plcc-diagram-list exits 0" {
    run plcc-diagram-list
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 7: Run bats command test**

```bash
bats tests/bats/commands/plcc-diagram-list.bats
```
Expected: both tests pass.

- [ ] **Step 8: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add src/plcc/diagram/__init__.py src/plcc/diagram/list.py src/plcc/diagram/list_test.py tests/bats/commands/plcc-diagram-list.bats pyproject.toml
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(diagram): add plcc-diagram-list command"
```

---

## Task 6: Create plcc-plantuml-diagram

Reads model JSON from stdin and writes `diagram.puml` to the output directory. One combined diagram (not per-class like the retired `plcc-plantuml-emit`).

**Files:**
- Create: `src/plcc/diagram/plantuml/__init__.py`
- Create: `src/plcc/diagram/plantuml/emit.py`
- Create: `src/plcc/diagram/plantuml/emit_test.py`
- Create: `tests/bats/commands/plcc-plantuml-diagram.bats`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing unit tests**

Create `src/plcc/diagram/plantuml/__init__.py` (empty file).

Create `src/plcc/diagram/plantuml/emit_test.py`:

```python
import io
import json
import pytest

from .emit import main as run_main, build_diagram


_ARITH_MODEL = {
    "start": "program",
    "classes": [
        {"name": "Program",  "abstract": False, "extends": None,        "fields": [{"name": "expr", "type": "Expr"}]},
        {"name": "Expr",     "abstract": False, "extends": None,        "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
        {"name": "ExprRest", "abstract": True,  "extends": None,        "fields": []},
        {"name": "AddRest",  "abstract": False, "extends": "ExprRest",  "fields": [{"name": "term", "type": "Term"}, {"name": "rest", "type": "ExprRest"}]},
        {"name": "NilRest",  "abstract": False, "extends": "ExprRest",  "fields": []},
        {"name": "Term",     "abstract": False, "extends": None,        "fields": [{"name": "num",  "type": "Token"}]}
    ],
    "semantic_sections": []
}


def test_build_diagram_starts_with_startuml():
    result = build_diagram(_ARITH_MODEL)
    assert result.startswith('@startuml\n')


def test_build_diagram_ends_with_enduml():
    result = build_diagram(_ARITH_MODEL)
    assert result.strip().endswith('@enduml')


def test_build_diagram_contains_program_class():
    result = build_diagram(_ARITH_MODEL)
    assert 'class Program' in result


def test_build_diagram_contains_field():
    result = build_diagram(_ARITH_MODEL)
    assert 'expr: Expr' in result


def test_build_diagram_abstract_class():
    result = build_diagram(_ARITH_MODEL)
    assert 'abstract class ExprRest' in result


def test_build_diagram_concrete_class_with_no_fields():
    result = build_diagram(_ARITH_MODEL)
    assert 'class NilRest {' in result


def test_build_diagram_inheritance_arrow():
    result = build_diagram(_ARITH_MODEL)
    assert 'AddRest --|> ExprRest' in result
    assert 'NilRest --|> ExprRest' in result


def test_build_diagram_no_arrow_for_no_extends():
    result = build_diagram(_ARITH_MODEL)
    assert 'Program --|>' not in result


def test_main_writes_diagram_puml(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_ARITH_MODEL)))
    run_main([f'--output={tmp_path}'])
    assert (tmp_path / 'diagram.puml').exists()


def test_main_diagram_contains_class_name(tmp_path, monkeypatch):
    monkeypatch.setattr('sys.stdin', io.StringIO(json.dumps(_ARITH_MODEL)))
    run_main([f'--output={tmp_path}'])
    content = (tmp_path / 'diagram.puml').read_text()
    assert 'ExprRest' in content


def test_main_no_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])
```

- [ ] **Step 2: Run failing tests**

```bash
pytest src/plcc/diagram/plantuml/emit_test.py -v 2>&1 | tail -10
```
Expected: `ImportError` — module does not exist yet.

- [ ] **Step 3: Implement emit.py**

Create `src/plcc/diagram/plantuml/emit.py`:

```python
import enum
import json
import os
import sys

from docopt import docopt

from ...verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-plantuml-diagram
    Emit a PlantUML class diagram from model JSON.

Usage:
    plcc-plantuml-diagram --output=DIR [options]

Options:
    --output=DIR    Directory to write diagram.puml into.
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-plantuml-diagram", Events, args)
    output_dir = args['--output']
    os.makedirs(output_dir, exist_ok=True)
    model = json.load(sys.stdin)
    content = build_diagram(model)
    path = os.path.join(output_dir, 'diagram.puml')
    with open(path, 'w') as f:
        f.write(content)


def build_diagram(model):
    lines = ['@startuml']
    classes = model.get('classes', [])
    for i, cls in enumerate(classes):
        if i > 0:
            lines.append('')
        lines.extend(_render_class(cls))
        if cls.get('extends'):
            lines.append(f'{cls["name"]} --|> {cls["extends"]}')
    lines.append('@enduml')
    return '\n'.join(lines) + '\n'


def _render_class(cls):
    if cls.get('abstract'):
        return [f'abstract class {cls["name"]}']
    result = [f'class {cls["name"]} {{']
    for field in cls.get('fields', []):
        result.append(f'  {field["name"]}: {field["type"]}')
    result.append('}')
    return result
```

- [ ] **Step 4: Register in pyproject.toml**

In `pyproject.toml`, add to `[project.scripts]`:
```toml
plcc-plantuml-diagram = "plcc.diagram.plantuml.emit:main"
```

Reinstall:
```bash
pip install -e . -q
```

- [ ] **Step 5: Run unit tests**

```bash
pytest src/plcc/diagram/plantuml/emit_test.py -v 2>&1 | tail -20
```
Expected: all PASS.

- [ ] **Step 6: Write bats command test**

Create `tests/bats/commands/plcc-plantuml-diagram.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    MODEL_JSON="$(mktemp)"
    OUTPUT_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model > "${MODEL_JSON}"
}

teardown() {
    rm -f "${MODEL_JSON}"
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-plantuml-diagram is on PATH" { command -v plcc-plantuml-diagram; }

@test "plcc-plantuml-diagram creates diagram.puml" {
    run bash -c "cat '${MODEL_JSON}' | plcc-plantuml-diagram --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
    [ -f "${OUTPUT_DIR}/diagram.puml" ]
}

@test "diagram.puml contains ExprRest" {
    bash -c "cat '${MODEL_JSON}' | plcc-plantuml-diagram --output='${OUTPUT_DIR}'"
    grep 'ExprRest' "${OUTPUT_DIR}/diagram.puml"
}

@test "diagram.puml contains inheritance arrow" {
    bash -c "cat '${MODEL_JSON}' | plcc-plantuml-diagram --output='${OUTPUT_DIR}'"
    grep 'AddRest --|> ExprRest' "${OUTPUT_DIR}/diagram.puml"
}
```

- [ ] **Step 7: Run bats command test**

```bash
bats tests/bats/commands/plcc-plantuml-diagram.bats
```
Expected: all pass.

- [ ] **Step 8: Verify plcc-diagram-list now finds plantuml**

```bash
plcc-diagram-list
```
Expected output includes `plantuml`.

- [ ] **Step 9: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add \
    src/plcc/diagram/plantuml/__init__.py \
    src/plcc/diagram/plantuml/emit.py \
    src/plcc/diagram/plantuml/emit_test.py \
    tests/bats/commands/plcc-plantuml-diagram.bats \
    pyproject.toml
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(diagram): add plcc-plantuml-diagram command"
```

---

## Task 7: Create plcc-diagram dispatcher

**Files:**
- Create: `src/plcc/diagram/dispatch.py`
- Create: `src/plcc/diagram/dispatch_test.py`
- Create: `tests/bats/commands/plcc-diagram.bats`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write failing unit tests**

Create `src/plcc/diagram/dispatch_test.py`:

```python
import io
import json
import subprocess
import pytest
from unittest.mock import patch, MagicMock

from .dispatch import main as run_main


_TRIVIAL_MODEL = json.dumps({
    "start": "program",
    "classes": [
        {"name": "Program", "abstract": False, "extends": None,
         "fields": [{"name": "num", "type": "Token"}]}
    ],
    "semantic_sections": []
})


def test_missing_output_arg_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_dispatches_to_plantuml_diagram(monkeypatch, tmp_path):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-plantuml-diagram'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--output={tmp_path}'])

    assert calls[0][0] == 'plcc-plantuml-diagram'
    assert f'--output={tmp_path}' in calls[0]


def test_default_format_is_plantuml(monkeypatch, tmp_path):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-plantuml-diagram'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--output={tmp_path}'])

    assert 'plcc-plantuml-diagram' in calls[0][0]


def test_custom_format_dispatches_to_correct_command(monkeypatch, tmp_path):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))
    calls = []

    def fake_run(cmd, stdin, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-mermaid-diagram'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--output={tmp_path}', '--format=mermaid'])

    assert calls[0][0] == 'plcc-mermaid-diagram'


def test_missing_plugin_exits_nonzero(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr('sys.stdin', io.StringIO(_TRIVIAL_MODEL))

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--output={tmp_path}', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
```

- [ ] **Step 2: Run failing tests**

```bash
pytest src/plcc/diagram/dispatch_test.py -v 2>&1 | tail -10
```
Expected: `ImportError` — module does not exist yet.

- [ ] **Step 3: Implement dispatch.py**

Create `src/plcc/diagram/dispatch.py`:

```python
import enum
import shutil
import subprocess
import sys

from docopt import docopt

from ..verbose import VerboseContext, VERBOSE_OPTIONS

__doc__ = """plcc-diagram
    Dispatch to the appropriate plcc-<fmt>-diagram command.

Usage:
    plcc-diagram --output=DIR [options]

Options:
    --output=DIR    Directory to write diagram file(s) into.
    --format=FMT    Diagram format [default: plantuml].
    -h --help       Show this message.
""" + VERBOSE_OPTIONS


class Events(enum.Enum):
    STARTED = "started"
    FINISHED = "finished"


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = docopt(__doc__, argv)
    verbose = VerboseContext.from_args("plcc-diagram", Events, args)
    fmt = args['--format'] or 'plantuml'
    output = args['--output']
    cmd = f'plcc-{fmt}-diagram'
    if not shutil.which(cmd):
        print(
            f"No diagram plugin found for '{fmt}'. Is {cmd} installed?\n"
            f"Run plcc-diagram-list to see what is available.",
            file=sys.stderr,
        )
        sys.exit(1)
    result = subprocess.run(
        [cmd, f'--output={output}'] + verbose.child_flags(),
        stdin=sys.stdin,
    )
    sys.exit(result.returncode)
```

- [ ] **Step 4: Register in pyproject.toml**

In `pyproject.toml`, add to `[project.scripts]`:
```toml
plcc-diagram = "plcc.diagram.dispatch:main"
```

Reinstall:
```bash
pip install -e . -q
```

- [ ] **Step 5: Run unit tests**

```bash
pytest src/plcc/diagram/dispatch_test.py -v 2>&1 | tail -15
```
Expected: all PASS.

- [ ] **Step 6: Write bats command test**

Create `tests/bats/commands/plcc-diagram.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    MODEL_JSON="$(mktemp)"
    OUTPUT_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model > "${MODEL_JSON}"
}

teardown() {
    rm -f "${MODEL_JSON}"
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-diagram is on PATH" { command -v plcc-diagram; }

@test "plcc-diagram creates diagram.puml with default plantuml format" {
    run bash -c "cat '${MODEL_JSON}' | plcc-diagram --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
    [ -f "${OUTPUT_DIR}/diagram.puml" ]
}

@test "plcc-diagram --format=plantuml creates diagram.puml" {
    run bash -c "cat '${MODEL_JSON}' | plcc-diagram --output='${OUTPUT_DIR}' --format=plantuml"
    [ "$status" -eq 0 ]
    [ -f "${OUTPUT_DIR}/diagram.puml" ]
}

@test "plcc-diagram fails for unknown format" {
    run bash -c "cat '${MODEL_JSON}' | plcc-diagram --output='${OUTPUT_DIR}' --format=nonexistent"
    [ "$status" -ne 0 ]
}
```

- [ ] **Step 7: Run bats command test**

```bash
bats tests/bats/commands/plcc-diagram.bats
```
Expected: all pass.

- [ ] **Step 8: Test end-to-end pipeline**

```bash
TMPDIR=$(mktemp -d)
plcc-spec tests/fixtures/arith.plcc | plcc-model | plcc-diagram --output="${TMPDIR}"
echo "exit: $?" && ls "${TMPDIR}"
cat "${TMPDIR}/diagram.puml"
rm -rf "${TMPDIR}"
```
Expected: exit 0, `diagram.puml` listed, content shows PlantUML class diagram with ExprRest and inheritance arrows.

- [ ] **Step 9: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add \
    src/plcc/diagram/dispatch.py \
    src/plcc/diagram/dispatch_test.py \
    tests/bats/commands/plcc-diagram.bats \
    pyproject.toml
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(diagram): add plcc-diagram dispatcher"
```

---

## Task 8: Retire plcc-plantuml-emit and update all affected files

Delete the old language plugin and its tests, update fixtures and bats tests that reference it.

**Files:**
- Delete: `src/plcc/lang/ext/plantuml/emit.py`
- Delete: `src/plcc/lang/ext/plantuml/emit_test.py`
- Delete: `tests/bats/commands/plcc-plantuml-emit.bats`
- Delete: `tests/fixtures/plantuml_only.plcc`
- Delete: `tests/fixtures/trivial-plantuml.plcc`
- Modify: `pyproject.toml` — remove `plcc-plantuml-emit` entry
- Modify: `tests/fixtures/trivial.plcc` — remove `% diagram PlantUML` line
- Modify: `tests/fixtures/trivial-full.plcc` — remove `% diagram PlantUML` line
- Modify: `tests/bats/commands/plcc-lang-list.bats` — remove "finds plantuml" test
- Modify: `tests/bats/integration/model-lang-emit.bats` — remove plantuml test

- [ ] **Step 1: Delete retired files**

```bash
git -C "$(git rev-parse --show-toplevel)" rm \
    src/plcc/lang/ext/plantuml/emit.py \
    src/plcc/lang/ext/plantuml/emit_test.py \
    tests/bats/commands/plcc-plantuml-emit.bats \
    tests/fixtures/plantuml_only.plcc \
    tests/fixtures/trivial-plantuml.plcc
```

- [ ] **Step 2: Remove plcc-plantuml-emit from pyproject.toml**

In `pyproject.toml`, remove this line from `[project.scripts]`:
```toml
plcc-plantuml-emit = "plcc.lang.ext.plantuml.emit:main"
```

Reinstall to unregister the command:
```bash
pip install -e . -q
```

- [ ] **Step 3: Update trivial.plcc — remove PlantUML section**

Current content of `tests/fixtures/trivial.plcc`:
```text
token NUM '\d+'
%
<program> ::= NUM
%
% diagram PlantUML
```

New content (remove last line):
```text
token NUM '\d+'
%
<program> ::= NUM
%
```

Write the new content to `tests/fixtures/trivial.plcc`.

- [ ] **Step 4: Update trivial-full.plcc — remove PlantUML section**

Current `tests/fixtures/trivial-full.plcc`:
```text
token NUM '\d+'
%
<program> ::= NUM
% Java Java
% py Python
% diagram PlantUML
```

New content (remove `% diagram PlantUML` line):
```text
token NUM '\d+'
%
<program> ::= NUM
% Java Java
% py Python
```

- [ ] **Step 5: Update plcc-lang-list.bats — remove plantuml test**

Current `tests/bats/commands/plcc-lang-list.bats` has:
```bash
@test "plcc-lang-list finds plantuml" {
    run plcc-lang-list
    [[ "$output" == *"plantuml"* ]]
}
```

Remove that test. The final file should be:
```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-lang-list is on PATH" { command -v plcc-lang-list; }

@test "plcc-lang-list exits 0" {
    run plcc-lang-list
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 6: Update model-lang-emit.bats — remove plantuml test**

Current `tests/bats/integration/model-lang-emit.bats` has a test that pipes to `plcc-lang-emit --target=PlantUML`. Replace the file with:

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    OUTPUT_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}"
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-model | plcc-lang-emit --target=Python produces output" {
    run bash -c "plcc-model '${SPEC_JSON}' | plcc-lang-emit --target=Python --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
}
```

(Python emit is a stub that copies runtime/main.py — it will produce a file even for the trivial grammar.)

- [ ] **Step 7: Run unit tests to confirm no regressions**

```bash
bin/test/units.bash 2>&1 | tail -10
```
Expected: all pass (the deleted plantuml emit_test.py is gone, no other tests reference it).

- [ ] **Step 8: Verify plcc-lang-list no longer finds plantuml**

```bash
plcc-lang-list
```
Expected: `plantuml` is NOT in the output.

- [ ] **Step 9: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add -A
git -C "$(git rev-parse --show-toplevel)" commit -m "feat(model): retire plcc-plantuml-emit language plugin"
```

---

## Task 9: Update the e2e smoke test

Replace the plantuml-emit-based smoke test with a diagram-pipeline-based test using `arith.plcc`.

**Files:**
- Modify: `tests/bats/e2e/happy-path.bats`

- [ ] **Step 1: Write the new smoke test**

Replace `tests/bats/e2e/happy-path.bats` with:

```bash
#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/spec.schema.json"
    MODEL_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/model.schema.json"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    plcc-make "${FIXTURES}/trivial.plcc"
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-make produces build/spec.json" {
    [ -f build/spec.json ]
}

@test "build/spec.json validates against spec schema" {
    check-jsonschema --schemafile "${SPEC_SCHEMA}" build/spec.json
}

@test "plcc-make produces build/model.json" {
    [ -f build/model.json ]
}

@test "build/model.json validates against model schema" {
    check-jsonschema --schemafile "${MODEL_SCHEMA}" build/model.json
}

@test "plcc-make produces build/ll1.json" {
    [ -f build/ll1.json ]
}

@test "plcc-make cleans build/ on rebuild" {
    touch build/stale-marker.txt
    plcc-make "${FIXTURES}/trivial.plcc"
    [ ! -f build/stale-marker.txt ]
}

@test "plcc-spec | plcc-model | plcc-diagram produces diagram.puml" {
    DIAGRAM_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model | plcc-diagram --output="${DIAGRAM_DIR}"
    [ -f "${DIAGRAM_DIR}/diagram.puml" ]
    rm -rf "${DIAGRAM_DIR}"
}

@test "diagram.puml contains expected classes" {
    DIAGRAM_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model | plcc-diagram --output="${DIAGRAM_DIR}"
    grep 'ExprRest' "${DIAGRAM_DIR}/diagram.puml"
    grep 'AddRest --|> ExprRest' "${DIAGRAM_DIR}/diagram.puml"
    rm -rf "${DIAGRAM_DIR}"
}

@test "plcc-diagram-list finds plantuml" {
    run plcc-diagram-list
    [[ "$output" == *"plantuml"* ]]
}

@test "plcc-make trivial-full produces build output for Java and Python" {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    FULL_DIR="$(mktemp -d)"
    (
        cd "${FULL_DIR}"
        plcc-make "${FIXTURES}/trivial-full.plcc"
        [ -f build/ll1.json ]
        [ -d build/Java ]
        [ -d build/py ]
    )
    rm -rf "${FULL_DIR}"
}
```

- [ ] **Step 2: Run the smoke test**

```bash
bats tests/bats/e2e/happy-path.bats
```
Expected: all tests pass (or the JDK test is skipped if javac is not available).

- [ ] **Step 3: Run the full test suite**

```bash
bin/test/all.bash 2>&1 | tail -20
```
Expected: all tests pass. Previous count was 431 Python + 117 bats. New count should be equal or higher (new tests added, old plantuml tests removed).

- [ ] **Step 4: Commit**

```bash
git -C "$(git rev-parse --show-toplevel)" add tests/bats/e2e/happy-path.bats
git -C "$(git rev-parse --show-toplevel)" commit -m "test(e2e): update smoke test for diagram pipeline and plcc-plantuml-emit retirement"
```

---

## Self-Review

### Spec coverage check

| Spec requirement | Task |
| --- | --- |
| `arith.plcc` fixture is LL(1) | Task 1, Step 3 |
| `plcc-model` produces schema-valid model | Task 2 + 3 |
| Classes: correct names, abstract flags, extends, fields | Task 3 |
| Semantic sections: language, tool, fragments with kind | Task 4 |
| `fragment.kind` computed from modifier + known classes | Task 4 |
| `fragment.body` strips `%%%` markers | Task 4 |
| `plcc-diagram-list` scans PATH for `plcc-*-diagram` | Task 5 |
| `plcc-plantuml-diagram` writes `diagram.puml` | Task 6 |
| `plcc-diagram` dispatches by format (default: plantuml) | Task 7 |
| `plcc-diagram` error message for missing plugin | Task 7, Step 3 |
| `plcc-plantuml-emit` removed from pyproject.toml | Task 8 |
| Fixtures updated (remove `% diagram PlantUML`) | Task 8 |
| `plcc-lang-list` no longer finds plantuml | Task 8, Step 8 |
| Smoke test updated to use diagram pipeline | Task 9 |
| End-to-end: `plcc-spec arith | plcc-model | plcc-diagram` | Task 9 |
| `plcc-diagram-list` finds `plantuml` | Task 9 |

### Placeholder scan

No TBD, TODO, or placeholder patterns found.

### Type consistency

- `build_model` returns `{'start': str, 'classes': [...], 'semantic_sections': [...]}`
- Each class has `name: str`, `abstract: bool`, `extends: str|None`, `fields: [...]`
- Each field has `name: str`, `type: str`
- Each semantic section has `language: str`, `tool: str`, `fragments: [...]`
- Each fragment has `class_name: str`, `kind: str`, `body: str`
- `build_diagram(model)` → `str` (the .puml content)
- `_render_class(cls)` → `list[str]` (lines for one class)
- `extract_format_name(str)` → `str | None`
- `find_formats()` → `list[str]`

All types are consistent across Tasks 3, 4, 6, and 7.
