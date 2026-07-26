# Bare-Name Field Derivation Decapitalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop bare (no explicit alt-name) capture field-name derivation from full-lowercasing nonterminal names, so a multi-word PascalCase nonterminal like `<OneMore>` produces field `oneMore` (decapitalized) instead of `onemore` (fully lowercased), matching the PascalCase-to-camelCase convention plcc-ng otherwise follows and matching legacy PLCC's equivalent behavior.

**Architecture:** No new abstractions beyond one small private helper per file. Three call sites currently derive a bare-name field via `name.lower()`; each gets an `isTerminal`-gated helper that keeps terminals fully lowercased (unchanged) and decapitalizes only the first letter of nonterminals. Two sites (`spec_json_decoder.py`, `build_model.py`) feed runtime parse-tree field names and generated class field names respectively — they must change together, in the same commit, because they must always agree (this is exactly the class of bug issue #164 fixed for the alt-name branch; leaving one side unfixed would reintroduce that mismatch for the bare-name branch). The third site (`CapturingSymbol.py::getAttributeName()`) feeds duplicate-capture validation only, not codegen/runtime, and is independent.

**Tech Stack:** Python 3, pytest, bats (CLI/e2e tests). No new dependencies.

## Global Constraints

- Terminal bare-name field derivation (e.g. `NUM` → `num`, `MY_TOKEN` → `my_token`) must remain unchanged — full-lowercase, not decapitalized. Decapitalizing a SCREAMING_SNAKE_CASE terminal would be wrong (`NUM` → `nUM`).
- Single-word nonterminal bare-name derivation (e.g. `Term` → `term`) is unaffected by this change — decapitalize-first-letter and full-lowercase produce the same result for a single word. Existing tests locking this in must keep passing unchanged.
- Follow CONTRIBUTING.md's TDD loop: write the failing test, confirm the failure, write the minimal fix, confirm the pass, commit.
- Run `bin/test/units.bash <path>` to scope pytest runs to the file(s) touched in each task; run the full `bin/test/units.bash` before the final commit of the branch. Baseline (before this plan): 1185 passed, 3 skipped.
- `docs/migration.md` was already updated with a clarifying note on this translation, in the design phase (commit `docs(migration): note bare nonterminal auto-naming decapitalization`) — no task in this plan touches it.
- Design of record: `dev-docs/specs/2026-07-24-168-bare-name-decapitalization-design.md`. If anything here seems to contradict it, the spec wins — stop and reconcile before continuing.

---

### Task 1: Decapitalize bare nonterminal field names in runtime decoding and code generation

**Files:**
- Modify: `src/plcc/ll1/spec_json_decoder.py:67-79` (`_arbno_field`, `_field`)
- Modify: `src/plcc/model/build_model.py:80-109` (`_extract_arbno_fields`, `_extract_fields`)
- Test: `src/plcc/ll1/spec_json_decoder_test.py`
- Test: `src/plcc/model/build_model_test.py`

**Interfaces:**
- Consumes: nothing new — same `sym`/`symbol` dict shape (`{"name": ..., "altName": ..., "isTerminal": ..., "isCapturing": ...}`) already used throughout both files.
- Produces: `_field(sym)`, `_arbno_field(sym)` (in `spec_json_decoder.py`) and `_extract_fields(rhs_symbol_list)`, `_extract_arbno_fields(rhs_symbol_list)` (in `build_model.py`) all keep their existing signatures. New private helper `_bare_field_name(sym)` added to each file (not shared between them — the two packages don't currently share code, and the function is a 3-line conditional). Only the value returned when there's no explicit alt-name and the symbol is a nonterminal changes (decapitalized instead of fully lowercased).

- [ ] **Step 1: Write the failing tests in `spec_json_decoder_test.py`**

Add directly after `test_capturing_terminal_uses_name_lower` (around line 70):

```python
def test_capturing_terminal_multiword_bare_name_stays_full_lower():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("E", [_terminal("MY_TOKEN", capturing=True)])
    ]))
    assert productions == {("E", ("MY_TOKEN",)): Rule(alt=None, fields=["my_token"])}
```

Add directly after `test_capturing_nonterminal_uses_name_lower` (around line 91):

```python
def test_capturing_nonterminal_multiword_bare_name_decapitalizes():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("E", [_nonterminal("OneMore", capturing=True)])
    ]))
    assert productions == {("E", ("OneMore",)): Rule(alt=None, fields=["oneMore"])}
```

Add at the end of the file, directly after `test_arbno_field_preserves_camelcase_alt_name` (after line 230):

```python


def test_arbno_field_bare_multiword_nonterminal_decapitalizes():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("OneMore", capturing=True)],
                    "COMMA"),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["rands"]["rhs"] == [
        {"field": "oneMoreList", "symbol": "OneMore", "is_terminal": False}
    ]
```

- [ ] **Step 2: Write the failing tests in `build_model_test.py`**

Add directly after `test_class_has_num_field` (around line 51):

```python
_BARE_MULTIWORD_SPEC = {
    "lexical": {"ruleList": []},
    "syntax": {
        "rules": [
            {
                "lhs": {"name": "Program", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "OneMore", "isTerminal": False, "isCapturing": True}
                ]
            }
        ]
    },
    "semantics": None
}


def test_bare_multiword_nonterminal_capture_decapitalizes():
    model = build_model(_BARE_MULTIWORD_SPEC)
    fields = model['classes'][0]['fields']
    assert any(f['name'] == 'oneMore' for f in fields)
```

Add directly after `test_arbno_field_name_preserves_camelcase_alt_name` (around line 459, before `test_extract_body_strips_percent_markers_with_trailing_newlines`):

```python


_ARBNO_BARE_MULTIWORD_SPEC = {
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
                    {"name": "OneMore", "isTerminal": False, "isCapturing": True}
                ],
                "separator": {"name": "COMMA", "isTerminal": True, "isCapturing": False}
            }
        ]
    },
    "semantics": None
}


def test_arbno_field_name_bare_multiword_nonterminal_decapitalizes():
    model = build_model(_ARBNO_BARE_MULTIWORD_SPEC)
    rands = next(c for c in model['classes'] if c['name'] == 'Rands')
    assert rands['fields'][0]['name'] == 'oneMoreList'
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py src/plcc/model/build_model_test.py -v`

Expected: the four new tests FAIL —
- `test_capturing_terminal_multiword_bare_name_stays_full_lower` currently PASSES already (no change needed here, it locks in existing behavior) — if it fails, something else is wrong; stop and investigate.
- `test_capturing_nonterminal_multiword_bare_name_decapitalizes` FAILS: actual `fields=["onemore"]` != expected `fields=["oneMore"]`.
- `test_arbno_field_bare_multiword_nonterminal_decapitalizes` FAILS: actual `{"field": "onemoreList", ...}` != expected `{"field": "oneMoreList", ...}`.
- `test_bare_multiword_nonterminal_capture_decapitalizes` FAILS: no field named `oneMore` exists (it's `onemore`).
- `test_arbno_field_name_bare_multiword_nonterminal_decapitalizes` FAILS: actual `onemoreList` != expected `oneMoreList`.

All other tests in both files still PASS.

- [ ] **Step 4: Fix `spec_json_decoder.py`**

Current code (lines 67-79):

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

Change to:

```python
def _bare_field_name(sym: dict) -> str:
    name = sym["name"]
    if sym.get("isTerminal", False):
        return name.lower()
    return name[:1].lower() + name[1:]


def _arbno_field(sym: dict) -> str:
    alt = sym.get("altName")
    return (alt if alt else _bare_field_name(sym)) + "List"


def _field(sym: dict) -> str | None:
    """Return the field name for a symbol dict, or None if elided."""
    if not sym.get("isCapturing", False):
        return None
    alt = sym.get("altName")
    return alt if alt else _bare_field_name(sym)
```

- [ ] **Step 5: Fix `build_model.py`**

Current code (lines 80-109):

```python
def _extract_arbno_fields(rhs_symbol_list):
    fields = []
    for symbol in rhs_symbol_list:
        if not symbol.get('isCapturing'):
            continue
        alt = symbol.get('altName')
        name = symbol.get('name', '')
        field_name = (alt if alt else name.lower()) + 'List'
        if symbol.get('isTerminal'):
            field_type = 'Token'
        else:
            n = symbol.get('name', 'Object')
            field_type = n
        fields.append({'name': field_name, 'type': field_type, 'is_list': True})
    return fields


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
            field_type = name
        fields.append({'name': field_name, 'type': field_type, 'is_list': False})
    return fields
```

Change to:

```python
def _bare_field_name(symbol):
    name = symbol.get('name', '')
    if symbol.get('isTerminal'):
        return name.lower()
    return name[:1].lower() + name[1:]


def _extract_arbno_fields(rhs_symbol_list):
    fields = []
    for symbol in rhs_symbol_list:
        if not symbol.get('isCapturing'):
            continue
        alt = symbol.get('altName')
        field_name = (alt if alt else _bare_field_name(symbol)) + 'List'
        if symbol.get('isTerminal'):
            field_type = 'Token'
        else:
            n = symbol.get('name', 'Object')
            field_type = n
        fields.append({'name': field_name, 'type': field_type, 'is_list': True})
    return fields


def _extract_fields(rhs_symbol_list):
    fields = []
    for symbol in rhs_symbol_list:
        if not symbol.get('isCapturing'):
            continue
        field_name = symbol.get('altName') or _bare_field_name(symbol)
        if symbol.get('isTerminal'):
            field_type = 'Token'
        else:
            name = symbol.get('name', 'Object')
            field_type = name
        fields.append({'name': field_name, 'type': field_type, 'is_list': False})
    return fields
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py src/plcc/model/build_model_test.py -v`
Expected: all tests PASS, including the five new/checked ones.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/ll1/spec_json_decoder.py src/plcc/ll1/spec_json_decoder_test.py \
        src/plcc/model/build_model.py src/plcc/model/build_model_test.py
git commit -m "$(cat <<'EOF'
fix(model)!: decapitalize bare multi-word nonterminal capture field names

Bare (no alt-name) capture field names were derived by full-lowercasing
the symbol's grammar name instead of decapitalizing just the first
letter, e.g. `<OneMore>` produced field `onemore` instead of `oneMore`.
Terminals are unaffected (SCREAMING_SNAKE_CASE terminals are still
correctly full-lowercased); only bare nonterminal captures change.

Although this is a breaking change for plcc-ng, it brings bare-capture
auto-naming back in line with legacy PLCC's original behavior: PLCC
required nonterminals to already be lowerCamelCase and used the name
verbatim for a bare capture's field, which was already the identity
transform. plcc-ng's PascalCase nonterminal convention (see the
migration guide) means the equivalent identity transform is
decapitalize-first-letter, not full-lowercase - the full-lowercase
behavior was a plcc-ng-only regression from the intended
PLCC-equivalent naming, not a deliberate design choice.

BREAKING CHANGE: a bare (no `:fieldname`) multi-word nonterminal
capture now generates/validates a camelCase field name instead of an
all-lowercase one, e.g. `<OneMore>` now produces field `oneMore`
instead of `onemore`. Semantic-section code referencing the old
all-lowercase field name (`self.onemore`) must update to the new
camelCase name (`self.oneMore`), or add an explicit `<OneMore:onemore>`
alt-name to keep the old spelling. Single-word nonterminal captures and
all terminal captures are unaffected.
EOF
)"
```

---

### Task 2: Decapitalize bare nonterminal names in duplicate-capture validation

**Files:**
- Modify: `src/plcc/spec/syntax/CapturingSymbol.py:10-14` (`getAttributeName`)
- Test: `src/plcc/spec/syntax/validations/validate_rhs_test.py`

**Interfaces:**
- Consumes: `CapturingSymbol.altName`, `CapturingSymbol.name`, and `CapturingSymbol.isTerminal` — all existing fields (`isTerminal` comes from the `Terminal`/`NonTerminal` mixin already combined with `CapturingSymbol` in `CapturingTerminal`/`RhsNonTerminal`; no new field needed).
- Produces: `getAttributeName()` keeps its existing signature (`() -> str`); only the return value for a bare (no `altName`) nonterminal capture changes (decapitalized instead of fully lowercased). Used by `validate_rhs.py::_validateNoDuplicateRhsSymbols` to detect duplicate captures within a rule.

This is not a breaking change: it makes validation *more permissive* (two bare captures that collided under full-lowercase but wouldn't collide under decapitalize are no longer incorrectly flagged as duplicates), matching the codegen/runtime behavior fixed in Task 1.

- [ ] **Step 1: Write the failing test**

Add to `src/plcc/spec/syntax/validations/validate_rhs_test.py`, directly after `test_one_nonterminal_with_different_altName_allowed` (after line 94):

```python


def test_duplicate_bare_multiword_nonterminals_differing_only_by_case_allowed():
    # <OneMore> has attr "oneMore"; <Onemore> has attr "onemore" (once
    # bare-name decapitalization lands) - different, so no duplicate.
    assertValid(DuplicateAttribute, '''<OneMore> ::=
<Onemore> ::=
<Sentence> ::= <OneMore> <Onemore>''')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bin/test/units.bash src/plcc/spec/syntax/validations/validate_rhs_test.py -v`
Expected: `test_duplicate_bare_multiword_nonterminals_differing_only_by_case_allowed` FAILS — `getAttributeName()` currently full-lowercases both bare names to `onemore`, so they collide and a spurious `DuplicateAttribute` error is raised. All other tests in the file still PASS.

- [ ] **Step 3: Fix `getAttributeName()`**

Current code (`src/plcc/spec/syntax/CapturingSymbol.py:10-14`):

```python
    def getAttributeName(self):
        if self.altName is None:
            return self.name.lower()
        else:
            return self.altName
```

Change to:

```python
    def getAttributeName(self):
        if self.altName is not None:
            return self.altName
        if self.isTerminal:
            return self.name.lower()
        return self.name[:1].lower() + self.name[1:]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bin/test/units.bash src/plcc/spec/syntax/validations/validate_rhs_test.py -v`
Expected: all tests PASS, including the new one.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/spec/syntax/CapturingSymbol.py src/plcc/spec/syntax/validations/validate_rhs_test.py
git commit -m "fix(syntax): decapitalize bare nonterminal names in duplicate-capture validation"
```

---

### Task 3: Correct the field-naming description in the language guide

**Files:**
- Modify: `docs/language-guide/syntactic.md:105-113` ("Capturing nonterminals" section)

**Interfaces:** None — documentation only.

- [ ] **Step 1: Update the doc text**

Current text (lines 105-113):

````markdown
### Capturing nonterminals

All nonterminals are captured. Their field names will be the nonterminal
name lower-cased. You may provide a different field name using `:fieldname`.

```text
<Program> ::= <Expr>              # captures Expr as field `expr`
<Program> ::= <Expr:expression>   # captures Expr as field `expression`
```
````

Change to:

````markdown
### Capturing nonterminals

All nonterminals are captured. Their field name is the nonterminal name
with its first letter decapitalized (PascalCase -> camelCase), not the
whole name lower-cased. You may provide a different field name using
`:fieldname`.

```text
<Program> ::= <Expr>              # captures Expr as field `expr`
<Program> ::= <Expr:expression>   # captures Expr as field `expression`
<Program> ::= <OneMore>           # captures OneMore as field `oneMore`
```
````

- [ ] **Step 2: Verify the change**

Run: `grep -n "decapitalized\|lower-cased" docs/language-guide/syntactic.md`
Expected: the "Capturing nonterminals" section shows the new "decapitalized" wording; the "Capturing terminals" section's unrelated "lower-cased name of the terminal" text (line ~83) is untouched.

- [ ] **Step 3: Commit**

```bash
git add docs/language-guide/syntactic.md
git commit -m "docs(language-guide): correct bare-nonterminal field-naming description"
```

---

### Task 4: End-to-end regression test reproducing issue 168

**Files:**
- Create: `tests/fixtures/bare-multiword-nonterminal.plcc`
- Modify: `tests/bats/e2e/plcc-rep.bats`

**Interfaces:**
- Consumes: the fix from Task 1 (this task has no unit-level interface of its own — it's a black-box proof that `plcc-rep` produces the decapitalized field name end-to-end, using this issue's own repro grammar).

- [ ] **Step 1: Create the fixture**

Create `tests/fixtures/bare-multiword-nonterminal.plcc`:

```
token LIT '\d+'
skip WS '\s+'
%
<Program>  ::= <OneMore>
<OneMore>  ::= <LIT>
%
Python
Program
%%%
def _run(self):
    return self.oneMore.lit.lexeme
%%%
```

- [ ] **Step 2: Add the bats case**

In `tests/bats/e2e/plcc-rep.bats`, add at the end of the file (after the existing `@test "plcc-rep evaluates camelCase alt-name multi-capture rule (issue 164)"` case):

```bash

@test "plcc-rep evaluates bare multi-word nonterminal capture field (issue 168)" {
    run --separate-stderr bash -c "echo '42' | plcc-rep --spec='${FIXTURES}/bare-multiword-nonterminal.plcc'"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "42" ]]
}
```

- [ ] **Step 3: Run the new bats case to verify it passes**

Run: `bin/test/e2e.bash tests/bats/e2e/plcc-rep.bats`
Expected: all cases in the file PASS, including `plcc-rep evaluates bare multi-word nonterminal capture field (issue 168)`.

- [ ] **Step 4: Run the full unit suite as a final check**

Run: `bin/test/units.bash`
Expected: all tests PASS (same or greater count than the pre-work baseline of 1185 passed, 3 skipped), 0 failures.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/bare-multiword-nonterminal.plcc tests/bats/e2e/plcc-rep.bats
git commit -m "test(e2e): add regression case for issue 168 (bare multi-word nonterminal field)"
```

---

## After this plan

Issue 168 can be closed as the final commit of this branch, per CLAUDE.md's issue-closing convention:

```bash
bin/issues/close.bash 168
```

This moves `dev-docs/issues/done/168-bare-name-decapitalization-not-camelcase.md` to `dev-docs/issues/done/` and updates `dev-docs/roadmap.md`. Verify with `bin/issues/check.bash` afterward.

Note: issue #169 (add a `whats-new.md` entry covering this branch's whole release) is a separate, already-filed follow-up — do it once for the entire branch before merging, not as part of this plan.
