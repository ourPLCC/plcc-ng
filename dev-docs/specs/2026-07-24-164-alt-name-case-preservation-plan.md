# camelCase Alt-Name Case Preservation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop four independent field-name-derivation call sites from lowercasing explicit alt-names, so a camelCase alt-name like `<Exp:testExp>` produces the same field name (`testExp`) in both the generated class and the runtime parse tree, instead of crashing with `KeyError` at runtime.

**Architecture:** No new abstractions. Each of four existing functions computes a field name via an `alt if alt else name`-shaped expression that currently lowercases the whole result; each is changed to lowercase only the `name` fallback branch, leaving an explicit `alt` untouched. One pre-existing site (`build_model.py::_extract_fields`) already does this correctly and is left alone.

**Tech Stack:** Python 3, pytest, bats (CLI/e2e tests). No new dependencies.

## Global Constraints

- Bare-name (no explicit alt-name) field derivation must remain unchanged — it still fully lowercases the symbol's grammar name. This is tracked separately as issue [#168](../issues/168-bare-name-decapitalization-not-camelcase.md) and is explicitly out of scope here.
- Follow CONTRIBUTING.md's TDD loop: write the failing test, confirm the failure, write the minimal fix, confirm the pass, commit.
- Run `bin/test/units.bash <path>` to scope pytest runs to the file(s) touched in each task; run the full `bin/test/units.bash` before the final commit of the branch.

---

### Task 1: Preserve alt-name case in the runtime parser's field-name decoder

**Files:**
- Modify: `src/plcc/ll1/spec_json_decoder.py:67-79` (`_arbno_field`, `_field`)
- Test: `src/plcc/ll1/spec_json_decoder_test.py`

**Interfaces:**
- Consumes: nothing new — same `sym: dict` shape (`{"name": ..., "altName": ..., "isTerminal": ..., "isCapturing": ...}`) already used throughout this file.
- Produces: `_field(sym)` and `_arbno_field(sym)` keep their existing signatures (`dict -> str | None` and `dict -> str`); only the value returned when `sym["altName"]` is set changes (case preserved instead of lowercased). Task 4's fixture depends on this behavior end-to-end.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/ll1/spec_json_decoder_test.py`, directly after `test_capturing_terminal_uses_alt_name` (around line 78):

```python
def test_capturing_terminal_preserves_camelcase_alt_name():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("E", [_terminal("NUM", capturing=True, alt_name="testExp")])
    ]))
    assert productions == {("E", ("NUM",)): Rule(alt=None, fields=["testExp"])}
```

Add to the same file, directly after `test_arbno_terminal_rhs_item` (at the end of the file, after line 210):

```python


def test_arbno_field_preserves_camelcase_alt_name():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("expr", capturing=True, alt_name="testExp")],
                    "COMMA"),
        _rule("expr", [_terminal("NUM")]),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["rands"]["rhs"] == [
        {"field": "testExpList", "symbol": "expr", "is_terminal": False}
    ]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py -v`
Expected: `test_capturing_terminal_preserves_camelcase_alt_name` FAILS — `fields=["testexp"]` (actual) != `fields=["testExp"]` (expected). `test_arbno_field_preserves_camelcase_alt_name` FAILS — `{"field": "testexpList", ...}` (actual) != `{"field": "testExpList", ...}` (expected). All other tests in the file still PASS.

- [ ] **Step 3: Fix `_field()` and `_arbno_field()`**

In `src/plcc/ll1/spec_json_decoder.py`, current code:

```python
def _arbno_field(sym: dict) -> str:
    alt = sym.get("altName")
    name = sym["name"]
    return (alt if alt else name).lower() + "List"


def _field(sym: dict) -> str | None:
    """Return the field name for a symbol dict, or None if elided."""
    if not sym.get("isCapturing", False):
        return None
    alt = sym.get("altName")
    name = sym["name"]
    return (alt if alt else name).lower()
```

Change to:

```python
def _arbno_field(sym: dict) -> str:
    alt = sym.get("altName")
    name = sym["name"]
    return (alt if alt else name.lower()) + "List"


def _field(sym: dict) -> str | None:
    """Return the field name for a symbol dict, or None if elided."""
    if not sym.get("isCapturing", False):
        return None
    alt = sym.get("altName")
    name = sym["name"]
    return alt if alt else name.lower()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py -v`
Expected: all tests PASS, including the two new ones.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/ll1/spec_json_decoder.py src/plcc/ll1/spec_json_decoder_test.py
git commit -m "fix(ll1): preserve alt-name case in runtime field-name decoding"
```

---

### Task 2: Preserve alt-name case in arbno code generation

**Files:**
- Modify: `src/plcc/model/build_model.py:80-94` (`_extract_arbno_fields`)
- Test: `src/plcc/model/build_model_test.py`

**Interfaces:**
- Consumes: same rule/symbol dict shape already used elsewhere in `build_model.py` (see `_ARBNO_SPEC` in the test file for the exact shape).
- Produces: `_extract_arbno_fields(rhs_symbol_list)` keeps its existing signature (`list[dict] -> list[dict]`, each returned dict has `name`/`type`/`is_list` keys); only the `name` value changes when `altName` is set (case preserved instead of lowercased).

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/model/build_model_test.py`, directly after `_ARBNO_SPEC` (after line 377, before `test_arbno_class_field_has_is_list_true`):

```python
_ARBNO_CAMELCASE_SPEC = {
    "lexical": {"ruleList": []},
    "syntax": {
        "rules": [
            {
                "lhs": {"name": "Program", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "Rands", "isTerminal": False, "isCapturing": True, "altName": "rands"}
                ]
            },
            {
                "lhs": {"name": "Rands", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "Expr", "isTerminal": False, "isCapturing": True, "altName": "testExp"}
                ],
                "separator": {"name": "COMMA", "isTerminal": True, "isCapturing": False}
            },
            {
                "lhs": {"name": "Expr", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "NUM", "isTerminal": True, "isCapturing": True, "altName": "num"}
                ]
            }
        ]
    },
    "semantics": None
}
```

Then add this test directly after `test_arbno_token_field_has_correct_type` (at the end of the arbno block, after line 424, before `test_extract_body_strips_percent_markers_with_trailing_newlines`):

```python


def test_arbno_field_name_preserves_camelcase_alt_name():
    model = build_model(_ARBNO_CAMELCASE_SPEC)
    rands = next(c for c in model['classes'] if c['name'] == 'Rands')
    assert rands['fields'][0]['name'] == 'testExpList'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/test/units.bash src/plcc/model/build_model_test.py -v`
Expected: `test_arbno_field_name_preserves_camelcase_alt_name` FAILS — actual field name is `testexpList`, expected `testExpList`. All other tests in the file still PASS.

- [ ] **Step 3: Fix `_extract_arbno_fields()`**

In `src/plcc/model/build_model.py`, current code:

```python
def _extract_arbno_fields(rhs_symbol_list):
    fields = []
    for symbol in rhs_symbol_list:
        if not symbol.get('isCapturing'):
            continue
        alt = symbol.get('altName')
        name = symbol.get('name', '')
        field_name = (alt if alt else name).lower() + 'List'
        if symbol.get('isTerminal'):
            field_type = 'Token'
        else:
            n = symbol.get('name', 'Object')
            field_type = n
        fields.append({'name': field_name, 'type': field_type, 'is_list': True})
    return fields
```

Change the `field_name` line to:

```python
        field_name = (alt if alt else name.lower()) + 'List'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bin/test/units.bash src/plcc/model/build_model_test.py -v`
Expected: all tests PASS, including the new one.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/model/build_model.py src/plcc/model/build_model_test.py
git commit -m "fix(model): preserve alt-name case in arbno field-name generation"
```

---

### Task 3: Preserve alt-name case in duplicate-capture validation

**Files:**
- Modify: `src/plcc/spec/syntax/CapturingSymbol.py:10-14` (`getAttributeName`)
- Test: `src/plcc/spec/syntax/validations/validate_rhs_test.py`

**Interfaces:**
- Consumes: `CapturingSymbol.altName` and `CapturingSymbol.name` (existing dataclass fields — no change).
- Produces: `getAttributeName()` keeps its existing signature (`() -> str`); only the return value when `altName` is set changes (case preserved instead of lowercased). Used by `validate_rhs.py::_validateNoDuplicateRhsSymbols` to detect duplicate captures within a rule.

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/spec/syntax/validations/validate_rhs_test.py`, directly after `test_duplicate_rhs_nonterminal_with_different_alt_name_allowed` (after line 47):

```python


def test_duplicate_rhs_nonterminal_with_case_differing_alt_name_allowed():
    # <Verb:testExp> attr "testExp"; <Verb:testexp> attr "testexp" (once
    # case is preserved) — different, so no duplicate.
    assertValid(DuplicateAttribute, '''<Verb> ::=
<Sentence> ::= <Verb:testExp> <Verb:testexp>''')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/test/units.bash src/plcc/spec/syntax/validations/validate_rhs_test.py -v`
Expected: `test_duplicate_rhs_nonterminal_with_case_differing_alt_name_allowed` FAILS — `getAttributeName()` currently lowercases both alt-names to `testexp`, so they collide and a spurious `DuplicateAttribute` error is raised. All other tests in the file still PASS.

- [ ] **Step 3: Fix `getAttributeName()`**

In `src/plcc/spec/syntax/CapturingSymbol.py`, current code:

```python
    def getAttributeName(self):
        if self.altName is None:
            return self.name.lower()
        else:
            return self.altName.lower()
```

Change to:

```python
    def getAttributeName(self):
        if self.altName is None:
            return self.name.lower()
        else:
            return self.altName
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bin/test/units.bash src/plcc/spec/syntax/validations/validate_rhs_test.py -v`
Expected: all tests PASS, including the new one.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/spec/syntax/CapturingSymbol.py src/plcc/spec/syntax/validations/validate_rhs_test.py
git commit -m "fix(syntax): preserve alt-name case in duplicate-capture validation"
```

---

### Task 4: End-to-end regression test reproducing issue 164

**Files:**
- Create: `tests/fixtures/multi-capture-camelcase.plcc`
- Modify: `tests/bats/e2e/plcc-rep.bats`

**Interfaces:**
- Consumes: the fixes from Tasks 1–3 (this task has no unit-level interface of its own — it's a black-box proof that `plcc-rep` no longer raises `KeyError` on a grammar using camelCase alt-names for a multi-capture rule).

- [ ] **Step 1: Confirm the crash still reproduces before the fix (sanity check on the original bug)**

This step is diagnostic only, not part of the permanent test suite. Run from the repo root:

```bash
cd "$(mktemp -d)"
cat > spec.plcc << 'EOF'
skip WHITESPACE '\s+'
token LIT '\d+'
token IF 'if'
token THEN 'then'
token ELSE 'else'
%
<Program>    ::= <Exp>
<Exp:LitExp> ::= <LIT>
<Exp:IfExp>  ::= IF <Exp:testExp> THEN <Exp:trueExp> ELSE <Exp:falseExp>
%
Python
Program
%%%
def _run(self):
    return str(self.exp.eval())
%%%
LitExp
%%%
def eval(self):
    return int(self.lit.lexeme)
%%%
IfExp
%%%
def eval(self):
    if self.testExp.eval() != 0:
        return self.trueExp.eval()
    else:
        return self.falseExp.eval()
%%%
EOF
echo 'if 1 then 2 else 3' | plcc-rep --spec=spec.plcc
```

Expected (this step runs *after* Tasks 1–3 are already committed, so it should already print `2`, not raise `KeyError`). If it prints `2`, the fix is confirmed working; proceed to Step 2 to lock it in as a permanent regression test. If it still raises `KeyError`, stop and re-check Tasks 1–3 before continuing.

- [ ] **Step 2: Create the permanent fixture**

Create `tests/fixtures/multi-capture-camelcase.plcc`:

```
skip WHITESPACE '\s+'
token LIT '\d+'
token IF 'if'
token THEN 'then'
token ELSE 'else'
%
<Program>    ::= <Exp>
<Exp:LitExp> ::= <LIT>
<Exp:IfExp>  ::= IF <Exp:testExp> THEN <Exp:trueExp> ELSE <Exp:falseExp>
%
Python
Program
%%%
def _run(self):
    return str(self.exp.eval())
%%%
LitExp
%%%
def eval(self):
    return int(self.lit.lexeme)
%%%
IfExp
%%%
def eval(self):
    if self.testExp.eval() != 0:
        return self.trueExp.eval()
    else:
        return self.falseExp.eval()
%%%
```

- [ ] **Step 3: Add the bats case**

In `tests/bats/e2e/plcc-rep.bats`, add at the end of the file (after the existing `@test "plcc-rep --verbose-format=json shows a real value for the default _run()"` case):

```bash

@test "plcc-rep evaluates camelCase alt-name multi-capture rule (issue 164)" {
    run --separate-stderr bash -c "echo 'if 1 then 2 else 3' | plcc-rep --spec='${FIXTURES}/multi-capture-camelcase.plcc'"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "2" ]]
}
```

- [ ] **Step 4: Run the new bats case to verify it passes**

Run: `bin/test/e2e.bash tests/bats/e2e/plcc-rep.bats`
Expected: all cases in the file PASS, including `plcc-rep evaluates camelCase alt-name multi-capture rule (issue 164)`.

- [ ] **Step 5: Run the full unit suite as a final check**

Run: `bin/test/units.bash`
Expected: all tests PASS (same or greater count than the pre-work baseline of 1181 passed, 3 skipped), 0 failures.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures/multi-capture-camelcase.plcc tests/bats/e2e/plcc-rep.bats
git commit -m "test(e2e): add regression case for issue 164 (camelCase alt-name multi-capture)"
```

---

## After this plan

Issue 164 can be closed as the final commit of this branch, per CLAUDE.md's issue-closing convention:

```bash
bin/issues/close.bash 164
```

This moves `dev-docs/issues/164-multi-capture-alt-name-case-mismatch.md` to `dev-docs/issues/done/` and updates `dev-docs/roadmap.md`. Verify with `bin/issues/check.bash` afterward.
