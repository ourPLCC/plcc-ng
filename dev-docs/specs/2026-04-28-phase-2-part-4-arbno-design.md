# Phase 2 Part 4: Arbno Support — Design

**Date:** 2026-04-28
**Status:** APPROVED
**Companion architectural spec:** `docs/superpowers/specs/2026-04-12-multi-lang-pipeline.md`
**Roadmap reference:** `docs/superpowers/specs/2026-04-12-multi-lang-implementation-plan.md` §5

---

## 1. Goal

Add end-to-end support for arbno (repeating) rules (`**=`) so that grammars using
them can be processed by the full pipeline and a working REPL session is possible.
After Part 4:

```sh
plcc-make trivial-arbno.plcc
plcc-rep trivial-arbno.plcc
>>> 1, 2, 3
[1, 2, 3]
```

---

## 2. Motivation

28 of 30 `languages` test-suite grammars use arbno rules. Without arbno support,
Phase 3 (Java emitter + `languages` suite) cannot proceed. Part 4 closes this gap
before Phase 3 begins.

A survey of the `languages` repo also confirmed:

- All arbno-using grammars use the separator form (`**= item +SEP`) for at least one
  rule
- `plcc-spec` already parses v8 legacy grammars correctly (no `% tool lang` header
  defaults to `language: "Java", tool: "Java"`)
- The `!flag=` syntax (used only by `CHAR`) is out of scope for Part 4

---

## 3. Phase Structure

| Part   | Scope                                              | Status           |
| ------ | -------------------------------------------------- | ---------------- |
| Part 1 | LL(1) parser (`plcc-ll1`, `plcc-parser-table`)     | Complete         |
| Part 2 | Full `plcc-model` + `plcc-diagram-*` system        | Complete         |
| Part 3     | `plcc-spec` entry-point, `plcc-python-emit`, `plcc-rep` | Complete         |
| **Part 4** | **Arbno support end-to-end**                            | **This design**  |

---

## 4. `plcc-ll1`: arbno section in `ll1.json`

### 4.1 Internal LL(1) analysis

`plcc-ll1` currently treats `**=` rules as single productions, producing incorrect
FIRST/FOLLOW/predict sets. Part 4 fixes this: `plcc-ll1` expands arbno rules
internally into right-recursive equivalents for LL(1) analysis (computing correct
FIRST, FOLLOW, and predict sets), then discards those internal rules from the output.

### 4.2 The `arbno` section

Arbno nonterminals are **removed from `parse_table`** and placed in a new top-level
`arbno` key instead. `plcc-parser-table` checks `arbno` before `parse_table`.

Schema:

```json
"arbno": {
  "rands": {
    "rhs": [
      {"field": "expList", "symbol": "exp", "is_terminal": false}
    ],
    "separator": "COMMA",
    "lookahead": ["INT", "LPAREN", "VAR"]
  },
  "cmds": {
    "rhs": [
      {"field": "cmdList", "symbol": "cmd", "is_terminal": false}
    ],
    "separator": null,
    "lookahead": ["LT", "GT", "PLUS"]
  }
}
```

Rules:

- `rhs` lists only the **capturing** items in the repeating body — the separator
  token is not included; it is conveyed solely by the `separator` field
- `field` is `symbolNameLower + "List"` for each capturing item
- `separator` is the separator token name, or `null` for plain arbno
- `lookahead` is FIRST of the first RHS item — the set the parser loops on

---

## 5. `plcc-parser-table`: loop mode

When the parser encounters a nonterminal present in `arbno`, it runs a loop instead
of a recursive descent.

### 5.1 No-separator loop (`separator: null`)

1. Initialize one empty list per capturing field
2. While lookahead ∈ `arbno[nt].lookahead`:
   parse each RHS item in order; append capturing items to their lists
3. Emit the flat node

### 5.2 Separator loop (`separator: "TOKEN"`)

1. Initialize empty lists
2. If lookahead ∉ `arbno[nt].lookahead`: emit node with empty lists (zero items valid)
3. Otherwise: parse first iteration's RHS items; then loop — while next token is
   the separator, consume it and parse another iteration
4. Emit the flat node

### 5.3 Tree JSON produced

```json
{"kind": "Rands", "rule": "rands", "expList": [
  {"kind": "LitExpr", "rule": "expr", "num": {"match": "NUM", "lexeme": "1"}},
  {"kind": "LitExpr", "rule": "expr", "num": {"match": "NUM", "lexeme": "2"}}
]}
```

- `kind` is the nonterminal name with first letter uppercased (same as `plcc-model`)
- `rule` is the nonterminal name as-is
- List fields hold JSON arrays; the values follow the same node/token conventions as
  all other tree JSON

---

## 6. `plcc-model`: arbno fields

`plcc-model` detects arbno rules by checking for the presence of a `separator` key
in each spec rule (non-arbno rules have no `separator` key; arbno rules have
`separator: null` or `separator: "TOKEN"`).

For arbno classes, each capturing RHS item becomes a list-typed field. A new boolean
`is_list` on the field signals this to emitters:

```json
{
  "name": "Rands",
  "abstract": false,
  "extends": null,
  "fields": [
    {"name": "expList", "type": "Exp", "is_list": true}
  ],
  "rule_name": "rands"
}
```

Multi-item arbno example (`<formals> **= <VAR> COLON <typeExp> +COMMA`):

```json
{
  "name": "Formals",
  "abstract": false,
  "extends": null,
  "fields": [
    {"name": "varList",     "type": "Token",   "is_list": true},
    {"name": "typeExpList", "type": "TypeExp",  "is_list": true}
  ],
  "rule_name": "formals"
}
```

Rules:

- Only capturing RHS items become fields; bare separator tokens do not
- Field name is `symbolNameLower + "List"` — matching v8's naming convention exactly
- `type` is the base element type (`Token` for terminals, capitalized nonterminal
  name for nonterminals); the emitter applies the list wrapper
- Non-arbno fields have `is_list: false`
- No `is_arbno` flag on the class — `is_list: true` on any field is sufficient signal

---

## 7. `plcc-python-emit` and runtime deserializer

### 7.1 `plcc-python-emit`

No change to the Jinja templates. Python is dynamically typed — `self.expList =
expList` works whether the value is a list or a scalar. The constructor loop in
`class_file.py.jinja` already iterates `cls.fields` by name without type inspection.

### 7.2 `runtime/deserialize.py`

This is where the real change lives. The deserializer currently reconstructs each
field as a single node. It needs to handle JSON arrays for list fields:

```python
def _deserialize_value(v, registry):
    if isinstance(v, list):
        return [_deserialize_value(item, registry) for item in v]
    elif isinstance(v, dict) and v.get('match'):   # token node
        return Token(v['lexeme'], v['match'])
    elif isinstance(v, dict):                       # tree node
        return registry.deserialize(v)
    else:
        return v
```

No field metadata required — dispatch is purely on the JSON value's Python type.
A list value deserializes each element recursively. This handles both arbno list
fields and any future use of JSON arrays in tree nodes.

---

## 8. Test fixture: `trivial-arbno.plcc`

A new fixture that exercises both separator and non-separator arbno:

```text
token NUM   '\d+'
token PLUS  '\+'
token COMMA ','
skip  SPACE '\s+'
%
<program>          ::= <rands>rands
<rands>            **= <expr>expr +COMMA
<expr>:LitExpr     ::= <NUM>num
<expr>:AddExpr     ::= PLUS <rands>rands
%
% eval Python _run
Program
%%%
def _run(self):
    return [e.eval() for e in self.rands.exprList]
%%%
LitExpr
%%%
def eval(self):
    return int(self.num.lexeme)
%%%
AddExpr
%%%
def eval(self):
    return sum(e.eval() for e in self.rands.exprList)
%%%
```

`AddExpr` uses a nested arbno (`+rands+`), exercising non-separator arbno indirectly
via recursive use of the separator form.

**Acceptance:** `plcc-rep trivial-arbno.plcc`, input `1, 2, 3` → `[1, 2, 3]`.

---

## 9. Testing strategy

### 9.1 Unit tests (TDD, one per component)

- **`plcc-ll1`:** given a grammar with plain and separator arbno, `ll1.json` contains
  a correct `arbno` section; expanded `xxx#` rules do not appear in `parse_table`;
  `is_ll1` remains correct
- **`plcc-parser-table` (via `plcc-tree`):** plain arbno produces a flat list node;
  separator arbno produces a flat list node; zero-item arbno produces `[]`
- **`plcc-model`:** arbno rules produce `is_list: true` fields with correct names and
  types; non-arbno fields are unchanged
- **`plcc-python-emit`:** generated class files have correct constructor signatures
- **`runtime/deserialize.py`:** a tree JSON with a list field deserializes correctly

### 9.2 Integration / e2e tests

New bats test using `trivial-arbno.plcc`:

- `plcc-make trivial-arbno.plcc` succeeds
- Token + tree pipeline produces the expected flat-list tree JSON
- `plcc-rep trivial-arbno.plcc` with input `1, 2, 3` returns `[1, 2, 3]`

### 9.3 Regression

All existing Phase 1 and Phase 2 tests pass. `arith.plcc` REPL is unaffected.

---

## 10. Acceptance Criteria

1. `plcc-ll1` produces a correct `arbno` section for both plain and separator forms
2. `plcc-tree` produces flat list nodes for all arbno nonterminals
3. `plcc-model` emits `is_list: true` fields with correct names and types
4. `plcc-rep trivial-arbno.plcc` works end-to-end
5. All existing tests pass

---

## 11. Out of scope for Part 4

- Java emitter arbno support (Phase 3)
- `!flag=` syntax / CHAR grammar (deferred)
- `languages` test suite integration (Phase 3)
- `plcc-scan` / `plcc-parse` visualizers (Phase 4)
