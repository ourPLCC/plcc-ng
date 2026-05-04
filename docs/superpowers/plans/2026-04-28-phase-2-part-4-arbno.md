# Phase 2 Part 4: Arbno Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add end-to-end arbno (`**=`) rule support so that `plcc-rep trivial-arbno.plcc` with input `1, 2, 3` produces `[1, 2, 3]`.

**Architecture:** `plcc-ll1` expands arbno rules into internal right-recursive rules for LL(1) analysis and emits an `arbno` section (separate from `parse_table`); `plcc-parser-table` loops over the arbno section instead of recursing; `plcc-model` marks arbno fields with `is_list: true`; the Python runtime deserializer dispatches on JSON arrays.

**Tech Stack:** Python 3.11+, pytest, bats, existing plcc pipeline tools

---

## File Map

| File | Change |
|---|---|
| `tests/fixtures/trivial-arbno.plcc` | **Create** — test fixture |
| `src/plcc/ll1/spec_json_decoder.py` | **Modify** — expand arbno rules, return 3-tuple |
| `src/plcc/ll1/spec_json_decoder_test.py` | **Modify** — add arbno expansion tests |
| `src/plcc/ll1/ll1_result_builder.py` | **Modify** — add arbno section, filter internal nts |
| `src/plcc/ll1/ll1_result_builder_test.py` | **Modify** — add arbno section tests |
| `src/plcc/ll1/ll1_cli.py` | **Modify** — unpack 3-tuple from decode() |
| `src/plcc/parser/predictive_parser.py` | **Rewrite** — recursive descent + arbno loop |
| `src/plcc/parser/predictive_parser_test.py` | **Modify** — add arbno parse tests |
| `src/plcc/model/build_model.py` | **Modify** — detect arbno, emit is_list fields |
| `src/plcc/model/build_model_test.py` | **Modify** — add arbno model tests |
| `src/plcc/lang/ext/python/runtime/deserialize.py` | **Modify** — handle list values |
| `src/plcc/lang/ext/python/runtime/deserialize_test.py` | **Modify** — add list field tests |
| `tests/bats/e2e/plcc-rep.bats` | **Modify** — add trivial-arbno e2e test |

---

## Task 1: Add `trivial-arbno.plcc` fixture

**Files:**
- Create: `tests/fixtures/trivial-arbno.plcc`

This fixture exercises separator arbno. It is the acceptance target for the whole part.

- [ ] **Step 1: Create the fixture**

```
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

- [ ] **Step 2: Verify plcc-spec parses it without error**

Run: `plcc-spec tests/fixtures/trivial-arbno.plcc | python3 -m json.tool > /dev/null`
Expected: exit 0, no errors.

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/trivial-arbno.plcc
git commit -m "test(arbno): add trivial-arbno.plcc fixture"
```

---

## Task 2: `spec_json_decoder.py` — arbno expansion, 3-tuple return

**Files:**
- Modify: `src/plcc/ll1/spec_json_decoder.py`
- Modify: `src/plcc/ll1/spec_json_decoder_test.py`

`decode()` currently returns a 2-tuple `(grammar, field_map)`. After this task it returns `(grammar, field_map, arbno_rules)`. For each arbno rule (detected by the presence of a `"separator"` key in the spec rule dict), it adds right-recursive internal rules to `grammar` for LL(1) analysis and records the arbno metadata in `arbno_rules`.

The expansion for separator arbno `<rands> **= <expr>expr +COMMA`:
- `rands → expr rands# | ε`
- `rands# → COMMA expr rands# | ε`

The expansion for plain arbno `<cmds> **= <cmd>`:
- `cmds → cmd cmds# | ε`
- `cmds# → cmd cmds# | ε`

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/ll1/spec_json_decoder_test.py`:

```python
def _arbno_rule(lhs_name, rhs_syms, separator_name):
    """Build an arbno rule dict. separator_name=None for plain arbno."""
    sep = None if separator_name is None else {
        "name": separator_name, "isTerminal": True, "isCapturing": False
    }
    return {
        "line": {"string": "", "number": 0, "file": ""},
        "lhs": {"name": lhs_name, "isTerminal": False, "altName": None, "isCapturing": False},
        "rhsSymbolList": rhs_syms,
        "separator": sep,
    }


def test_decode_returns_3_tuple():
    grammar, field_map, arbno_rules = decode(_spec([]))
    assert isinstance(arbno_rules, dict)


def test_non_arbno_rules_not_in_arbno_rules():
    grammar, field_map, arbno_rules = decode(_spec([
        _rule("program", [_terminal("NUM")])
    ]))
    assert arbno_rules == {}


def test_separator_arbno_in_arbno_rules():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("expr", capturing=True, alt_name="expr")],
                    "COMMA"),
        _rule("expr", [_terminal("NUM")]),
    ])
    grammar, field_map, arbno_rules = decode(spec)
    assert "rands" in arbno_rules


def test_separator_arbno_rhs_field_has_list_suffix():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("expr", capturing=True, alt_name="expr")],
                    "COMMA"),
        _rule("expr", [_terminal("NUM")]),
    ])
    grammar, field_map, arbno_rules = decode(spec)
    assert arbno_rules["rands"]["rhs"] == [
        {"field": "exprList", "symbol": "expr", "is_terminal": False}
    ]


def test_separator_arbno_separator_field():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("expr", capturing=True, alt_name="expr")],
                    "COMMA"),
        _rule("expr", [_terminal("NUM")]),
    ])
    grammar, field_map, arbno_rules = decode(spec)
    assert arbno_rules["rands"]["separator"] == "COMMA"


def test_plain_arbno_separator_is_none():
    spec = _spec([
        _arbno_rule("cmds",
                    [_nonterminal("cmd", capturing=True, alt_name="cmd")],
                    None),
        _rule("cmd", [_terminal("X")]),
    ])
    grammar, field_map, arbno_rules = decode(spec)
    assert arbno_rules["cmds"]["separator"] is None


def test_arbno_expansion_adds_internal_rules_to_grammar():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("expr", capturing=True, alt_name="expr")],
                    "COMMA"),
        _rule("expr", [_terminal("NUM")]),
    ])
    grammar, field_map, arbno_rules = decode(spec)
    nts = grammar.getNonterminalSet()
    assert "rands" in nts
    assert "rands#" in nts


def test_arbno_terminal_rhs_item():
    spec = _spec([
        _arbno_rule("tokens",
                    [_terminal("NUM", capturing=True, alt_name="num")],
                    None),
    ])
    grammar, field_map, arbno_rules = decode(spec)
    assert arbno_rules["tokens"]["rhs"] == [
        {"field": "numList", "symbol": "NUM", "is_terminal": True}
    ]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py -v`
Expected: multiple FAILs — `decode` still returns 2-tuple, no `arbno_rules`.

- [ ] **Step 3: Implement the changes**

Replace `src/plcc/ll1/spec_json_decoder.py` with:

```python
from plcc.spec.syntax.validations.ll1.Grammar import Grammar


def decode(spec_dict: dict) -> tuple:
    """
    Build a Grammar from a spec JSON dict.

    Returns (grammar, field_map, arbno_rules) where:
      grammar      — Grammar with both regular and internal arbno expansion rules
      field_map    — dict[(nt_name, prod_tuple)] -> list[str|None]
      arbno_rules  — dict[nt_name] -> {rhs, separator}
    """
    grammar = Grammar()
    field_map = {}
    arbno_rules = {}
    for rule in spec_dict.get("syntax", {}).get("rules", []):
        nt = rule["lhs"]["name"]
        rhs = rule.get("rhsSymbolList", [])
        if "separator" in rule:
            _handle_arbno(grammar, field_map, arbno_rules, nt, rhs, rule["separator"])
        elif not rhs:
            grammar.addRule(nt, [])
            field_map[(nt, ())] = []
        else:
            syms = [s["name"] for s in rhs]
            fields = [_field(s) for s in rhs]
            grammar.addRule(nt, syms)
            field_map[(nt, tuple(syms))] = fields
    return grammar, field_map, arbno_rules


def _handle_arbno(grammar, field_map, arbno_rules, nt, rhs, separator_entry):
    separator = separator_entry["name"] if separator_entry else None
    cont = nt + "#"
    syms = [s["name"] for s in rhs]

    # Expand into right-recursive internal rules for LL(1) analysis only.
    grammar.addRule(nt, syms + [cont])
    grammar.addRule(nt, [])
    if separator:
        grammar.addRule(cont, [separator] + syms + [cont])
    else:
        grammar.addRule(cont, syms + [cont])
    grammar.addRule(cont, [])

    arbno_rhs = [
        {
            "field": _arbno_field(s),
            "symbol": s["name"],
            "is_terminal": bool(s.get("isTerminal", False)),
        }
        for s in rhs
        if s.get("isCapturing", False)
    ]
    arbno_rules[nt] = {"rhs": arbno_rhs, "separator": separator}


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

- [ ] **Step 4: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/ll1/spec_json_decoder.py src/plcc/ll1/spec_json_decoder_test.py
git commit -m "feat(ll1): decode() expands arbno rules, returns 3-tuple with arbno_rules"
```

---

## Task 3: `ll1_result_builder.py` + `ll1_cli.py` — `arbno` section in ll1.json

**Files:**
- Modify: `src/plcc/ll1/ll1_result_builder.py`
- Modify: `src/plcc/ll1/ll1_result_builder_test.py`
- Modify: `src/plcc/ll1/ll1_cli.py`

`build_ll1_result` gains a third `arbno_rules` parameter (default `{}`). It filters arbno nonterminals (and their `nt#` continuations) from `first_sets`, `follow_sets`, `predict_sets`, `parse_table`, and `conflicts`. It computes the lookahead set for each arbno nt (FIRST of the first RHS item, minus ε and $), and emits them in a new `"arbno"` key.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/ll1/ll1_result_builder_test.py`:

```python
def _arbno_grammar_and_rules():
    """
    Mimics <rands> **= <expr>expr +COMMA  with <expr> ::= NUM.
    Grammar is expanded: rands→expr rands#|ε, rands#→COMMA expr rands#|ε, expr→NUM.
    """
    g = Grammar()
    g.addRule("rands", ["expr", "rands#"])
    g.addRule("rands", [])
    g.addRule("rands#", ["COMMA", "expr", "rands#"])
    g.addRule("rands#", [])
    g.addRule("expr", ["NUM"])
    fm = {
        ("rands",  ("expr", "rands#")): [None, None],
        ("rands",  ()):                 [],
        ("rands#", ("COMMA", "expr", "rands#")): [None, None, None],
        ("rands#", ()):                 [],
        ("expr",   ("NUM",)):           [None],
    }
    arbno = {
        "rands": {
            "rhs": [{"field": "exprList", "symbol": "expr", "is_terminal": False}],
            "separator": "COMMA",
        }
    }
    return g, fm, arbno


def test_arbno_section_present_in_result():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert "arbno" in result


def test_arbno_nt_in_arbno_not_parse_table():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert "rands" in result["arbno"]
    assert "rands" not in result["parse_table"]


def test_arbno_internal_cont_not_in_parse_table():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert "rands#" not in result["parse_table"]


def test_arbno_internal_nts_not_in_first_sets():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert "rands" not in result["first_sets"]
    assert "rands#" not in result["first_sets"]


def test_arbno_lookahead_computed_from_first_of_first_item():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert result["arbno"]["rands"]["lookahead"] == ["NUM"]


def test_arbno_separator_preserved():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert result["arbno"]["rands"]["separator"] == "COMMA"


def test_arbno_rhs_preserved():
    g, fm, arbno = _arbno_grammar_and_rules()
    result = build_ll1_result(g, fm, arbno)
    assert result["arbno"]["rands"]["rhs"] == [
        {"field": "exprList", "symbol": "expr", "is_terminal": False}
    ]


def test_existing_grammar_unaffected_when_no_arbno():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["is_ll1"] is True
    assert result["arbno"] == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bin/test/units.bash src/plcc/ll1/ll1_result_builder_test.py -v`
Expected: tests referencing `arbno` FAIL; existing tests still PASS.

- [ ] **Step 3: Implement the changes to `ll1_result_builder.py`**

Replace `src/plcc/ll1/ll1_result_builder.py` with:

```python
from plcc.spec.syntax.validations.ll1.Grammar import Grammar
from plcc.spec.syntax.validations.ll1.build_first_sets import build_first_sets
from plcc.spec.syntax.validations.ll1.build_follow_sets import build_follow_sets
from plcc.spec.syntax.validations.ll1.build_parsing_table import build_parsing_table
from plcc.spec.syntax.validations.ll1.check_parsing_table_for_ll1 import check_parsing_table_for_ll1
from plcc.spec.syntax.validations.ll1.check_left_recursion import check_left_recursion


def build_ll1_result(grammar: Grammar, field_map: dict, arbno_rules: dict = None) -> dict:
    if arbno_rules is None:
        arbno_rules = {}
    eps = grammar.getEpsilon()
    eof = grammar.getEof()

    internal_nts = set(arbno_rules) | {nt + "#" for nt in arbno_rules}

    try:
        lr_cycles = check_left_recursion(grammar)
    except (IndexError, TypeError):
        lr_cycles = []
    firsts = build_first_sets(grammar)
    follows = build_follow_sets(grammar, firsts)
    table = build_parsing_table(firsts, follows, grammar)
    conflict_errors = check_parsing_table_for_ll1(table)

    def tok(t):
        if t is eps:
            return ""
        if t is eof:
            return "$"
        return t

    nts = sorted(
        nt for nt in grammar.getNonterminalSet()
        if nt not in internal_nts
    )

    first_sets = {nt: sorted(tok(t) for t in firsts[nt]) for nt in nts}
    follow_sets = {nt: sorted(tok(t) for t in follows[nt]) for nt in nts}

    predict_sets = {}
    for nt in nts:
        nt_preds = []
        for prod in grammar.getForms(nt):
            prod_first = firsts.get(prod, set())
            pset = {tok(t) for t in prod_first if t is not eps}
            if eps in prod_first:
                pset.update(tok(t) for t in follows[nt])
            nt_preds.append(sorted(pset))
        predict_sets[nt] = nt_preds

    bad_cells = {(e.cell[0], e.cell[1]) for e in conflict_errors}

    parse_table = {}
    for (nt, t) in table.getKeys():
        if nt in internal_nts:
            continue
        if (nt, t) in bad_cells:
            continue
        cell = table.getCell(nt, t)
        if len(cell) != 1:
            continue
        prod = next(iter(cell))
        lookahead = tok(t)
        parse_table.setdefault(nt, {})[lookahead] = _prod_entry(nt, prod, field_map, eps)

    conflicts = []

    def cell_sort_key(cell):
        nt, t = cell
        return (nt, tok(t))

    for (nt, t) in sorted(bad_cells, key=cell_sort_key):
        if nt in internal_nts:
            continue
        prods = table.getCell(nt, t)
        lookahead = tok(t)
        productions = [
            _prod_entry(nt, p, field_map, eps)
            for p in sorted(prods, key=str)
        ]
        conflicts.append({"nonterminal": nt, "lookahead": lookahead, "productions": productions})

    left_recursion = []
    for offending in lr_cycles:
        cycle = [rule[0] for rule in offending] + [offending[-1][1][0]]
        left_recursion.append({"cycle": cycle})

    arbno_out = {}
    for nt, entry in arbno_rules.items():
        if entry["rhs"]:
            first_item = entry["rhs"][0]
            first_sym = first_item["symbol"]
            if first_item["is_terminal"]:
                lookahead = [first_sym]
            else:
                fset = firsts.get(first_sym, set())
                lookahead = sorted(t for t in fset if t is not eps and t is not eof)
        else:
            lookahead = []
        arbno_out[nt] = {**entry, "lookahead": lookahead}

    return {
        "is_ll1": not (conflicts or left_recursion),
        "start_symbol": grammar.getStartSymbol(),
        "first_sets": first_sets,
        "follow_sets": follow_sets,
        "predict_sets": predict_sets,
        "parse_table": parse_table,
        "conflicts": conflicts,
        "left_recursion": left_recursion,
        "arbno": arbno_out,
    }


def _prod_entry(nt: str, prod: tuple, field_map: dict, eps) -> list:
    fields = field_map.get((nt, prod), [None] * len(prod))
    return [
        {"symbol": sym, "field": fld}
        for sym, fld in zip(prod, fields)
        if sym is not eps
    ]
```

- [ ] **Step 4: Update `ll1_cli.py` to unpack 3-tuple**

In `src/plcc/ll1/ll1_cli.py`, change line 44–45:

Old:
```python
    grammar, field_map = decode(spec)
    result = build_ll1_result(grammar, field_map)
```

New:
```python
    grammar, field_map, arbno_rules = decode(spec)
    result = build_ll1_result(grammar, field_map, arbno_rules)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/ll1/ -v`
Expected: all PASS.

- [ ] **Step 6: Verify plcc-ll1 CLI produces arbno section**

Run: `plcc-spec tests/fixtures/trivial-arbno.plcc | plcc-ll1 | python3 -c "import json,sys; d=json.load(sys.stdin); print(list(d['arbno'].keys()))"`
Expected: `['rands']`

- [ ] **Step 7: Commit**

```bash
git add src/plcc/ll1/ll1_result_builder.py src/plcc/ll1/ll1_result_builder_test.py src/plcc/ll1/ll1_cli.py
git commit -m "feat(ll1): emit arbno section in ll1.json, filter internal expansion nts"
```

---

## Task 4: `predictive_parser.py` — recursive descent + arbno loop

**Files:**
- Modify (rewrite): `src/plcc/parser/predictive_parser.py`
- Modify: `src/plcc/parser/predictive_parser_test.py`

The current stack-based parser cannot handle the arbno loop. This task rewrites it as a recursive descent parser that checks `arbno` before `parse_table`. The external interface (`parse(ll1, tokens) -> dict`) and the `ParseError` / `NodeBuilder` classes are unchanged. All existing tests must pass.

The key design: `parse_nt(sym)` dispatches to `_parse_regular(sym)` or `_parse_arbno(sym)`. Both return a `NodeBuilder` (not yet `to_node()`). Only `parse()` calls `to_node()` on the root builder.

For arbno, the `children` list holds `[field, list_of_values]` pairs where each value is a token dict or tree dict.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/parser/predictive_parser_test.py`:

```python
# ll1 dict for: rands **= expr +COMMA, expr → NUM
_RANDS_LL1 = {
    "is_ll1": True,
    "start_symbol": "rands",
    "parse_table": {
        "expr": {
            "NUM": [{"symbol": "NUM", "field": "num"}]
        }
    },
    "arbno": {
        "rands": {
            "rhs": [{"field": "exprList", "symbol": "expr", "is_terminal": False}],
            "separator": "COMMA",
            "lookahead": ["NUM"],
        }
    }
}

# ll1 dict for: cmds **= cmd (no separator), cmd → X
_CMDS_LL1 = {
    "is_ll1": True,
    "start_symbol": "cmds",
    "parse_table": {
        "cmd": {
            "X": [{"symbol": "X", "field": "x"}]
        }
    },
    "arbno": {
        "cmds": {
            "rhs": [{"field": "cmdList", "symbol": "cmd", "is_terminal": False}],
            "separator": None,
            "lookahead": ["X"],
        }
    }
}


def test_arbno_separator_two_items_produces_list():
    result = parse(_RANDS_LL1, [
        _tok("NUM", "1"),
        _tok("COMMA", ","),
        _tok("NUM", "2"),
    ])
    children_dict = dict(result["children"])
    assert "exprList" in children_dict
    assert isinstance(children_dict["exprList"], list)
    assert len(children_dict["exprList"]) == 2


def test_arbno_separator_list_items_are_tree_nodes():
    result = parse(_RANDS_LL1, [
        _tok("NUM", "1"),
        _tok("COMMA", ","),
        _tok("NUM", "2"),
    ])
    expr_list = dict(result["children"])["exprList"]
    assert expr_list[0]["kind"] == "tree"
    assert expr_list[0]["rule"] == "expr"
    assert expr_list[1]["kind"] == "tree"


def test_arbno_separator_zero_items_on_no_match():
    result = parse(_RANDS_LL1, [])
    children_dict = dict(result["children"])
    assert children_dict["exprList"] == []


def test_arbno_separator_one_item():
    result = parse(_RANDS_LL1, [_tok("NUM", "42")])
    children_dict = dict(result["children"])
    assert len(children_dict["exprList"]) == 1


def test_arbno_plain_multiple_items():
    result = parse(_CMDS_LL1, [
        _tok("X", "a"),
        _tok("X", "b"),
        _tok("X", "c"),
    ])
    children_dict = dict(result["children"])
    assert len(children_dict["cmdList"]) == 3


def test_arbno_plain_zero_items():
    result = parse(_CMDS_LL1, [])
    children_dict = dict(result["children"])
    assert children_dict["cmdList"] == []


def test_arbno_result_is_tree_kind():
    result = parse(_RANDS_LL1, [_tok("NUM", "1")])
    assert result["kind"] == "tree"
    assert result["rule"] == "rands"
```

- [ ] **Step 2: Run tests to verify new tests fail, old tests pass**

Run: `bin/test/units.bash src/plcc/parser/predictive_parser_test.py -v`
Expected: the 7 new arbno tests FAIL with ParseError or KeyError; all prior tests PASS.

- [ ] **Step 3: Rewrite `predictive_parser.py`**

Replace `src/plcc/parser/predictive_parser.py` with:

```python
class ParseError(Exception):
    pass


class NodeBuilder:
    def __init__(self, rule):
        self.rule = rule
        self.children = []      # [[field, node_or_list], ...]
        self.first_tok = None
        self.last_tok = None

    def note_token(self, tok):
        if self.first_tok is None:
            self.first_tok = tok
        self.last_tok = tok

    def note_span_from(self, child_builder):
        if child_builder.first_tok is not None:
            if self.first_tok is None:
                self.first_tok = child_builder.first_tok
            self.last_tok = child_builder.last_tok

    def to_node(self):
        source = {}
        if self.first_tok is not None and self.last_tok is not None:
            fs = self.first_tok["source"]
            ls = self.last_tok["source"]
            source = {
                "file": fs.get("file", ""),
                "line": fs["line"],
                "column": fs["column"],
                "endLine": ls["line"],
                "endColumn": ls["column"] + len(self.last_tok["lexeme"]) - 1,
            }
        return {
            "kind": "tree",
            "rule": self.rule,
            "source": source,
            "children": self.children,
        }


def parse(ll1: dict, tokens: list) -> dict:
    """
    Parse tokens against the LL(1) parse table and arbno section.

    ll1    — dict with keys: start_symbol, parse_table, arbno (optional)
    tokens — list of token dicts from plcc-tokens (without $ sentinel)

    Returns the root parse tree dict.
    Raises ParseError on any syntax error.
    """
    parse_table = ll1["parse_table"]
    arbno = ll1.get("arbno", {})
    start = ll1["start_symbol"]
    cursor = [0]

    SENTINEL = {"name": "$", "lexeme": "", "source": {"file": "", "line": 0, "column": 0}}

    def current():
        return tokens[cursor[0]] if cursor[0] < len(tokens) else SENTINEL

    def advance():
        tok = tokens[cursor[0]]
        cursor[0] += 1
        return tok

    def expect(sym):
        tok = current()
        if tok["name"] != sym:
            raise ParseError(
                f"expected {sym!r}, got {tok['name']!r} "
                f"at {tok['source']}"
            )
        return advance()

    def is_nonterminal(sym):
        return sym in parse_table or sym in arbno

    def parse_nt(sym):
        if sym in arbno:
            return _parse_arbno(sym)
        return _parse_regular(sym)

    def _parse_regular(sym):
        lookahead = current()["name"]
        nt_table = parse_table.get(sym)
        if nt_table is None:
            raise ParseError(f"no parse table entry for nonterminal {sym!r}")
        production = nt_table.get(lookahead)
        if production is None:
            raise ParseError(
                f"unexpected {lookahead!r}, no production for {sym!r} "
                f"at {current()['source']}"
            )
        builder = NodeBuilder(sym)
        for entry in production:
            s, f = entry["symbol"], entry["field"]
            if is_nonterminal(s):
                child_builder = parse_nt(s)
                builder.note_span_from(child_builder)
                if f is not None:
                    builder.children.append([f, child_builder.to_node()])
            else:
                tok = expect(s)
                builder.note_token(tok)
                if f is not None:
                    builder.children.append([f, tok])
        return builder

    def _parse_arbno(sym):
        entry = arbno[sym]
        lookahead_set = set(entry["lookahead"])
        separator = entry["separator"]
        rhs = entry["rhs"]
        builder = NodeBuilder(sym)
        list_fields = {item["field"]: [] for item in rhs}

        def parse_iteration():
            for item in rhs:
                if item["is_terminal"]:
                    tok = expect(item["symbol"])
                    builder.note_token(tok)
                    list_fields[item["field"]].append(tok)
                else:
                    child_builder = parse_nt(item["symbol"])
                    builder.note_span_from(child_builder)
                    list_fields[item["field"]].append(child_builder.to_node())

        if current()["name"] in lookahead_set:
            parse_iteration()
            if separator:
                while current()["name"] == separator:
                    expect(separator)
                    parse_iteration()
            else:
                while current()["name"] in lookahead_set:
                    parse_iteration()

        for field, values in list_fields.items():
            builder.children.append([field, values])

        return builder

    root_builder = parse_nt(start)
    tok = current()
    if tok["name"] != "$":
        raise ParseError(
            f"unexpected token {tok['name']!r} after complete parse "
            f"at {tok['source']}"
        )
    return root_builder.to_node()
```

- [ ] **Step 4: Run all parser tests to verify they pass**

Run: `bin/test/units.bash src/plcc/parser/predictive_parser_test.py -v`
Expected: all tests PASS (both existing and new).

- [ ] **Step 5: Commit**

```bash
git add src/plcc/parser/predictive_parser.py src/plcc/parser/predictive_parser_test.py
git commit -m "feat(parser): rewrite predictive_parser as recursive descent with arbno loop support"
```

---

## Task 5: `build_model.py` — arbno field detection, `is_list` flag

**Files:**
- Modify: `src/plcc/model/build_model.py`
- Modify: `src/plcc/model/build_model_test.py`

Arbno rules are detected by the presence of `"separator"` in the rule dict (same key that `spec_json_decoder.py` uses). For arbno rules, capturing fields get `is_list: true` and the name is `(altName or name).lower() + "List"`. For non-arbno fields, `is_list: false` is added.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/model/build_model_test.py`:

```python
_ARBNO_SPEC = {
    "lexical": {"ruleList": []},
    "syntax": {
        "rules": [
            {
                "lhs": {"name": "program", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "rands", "isTerminal": False, "isCapturing": True, "altName": "rands"}
                ]
            },
            {
                "lhs": {"name": "rands", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "expr", "isTerminal": False, "isCapturing": True, "altName": "expr"}
                ],
                "separator": {"name": "COMMA", "isTerminal": True, "isCapturing": False}
            },
            {
                "lhs": {"name": "expr", "altName": None, "isTerminal": False, "isCapturing": False},
                "rhsSymbolList": [
                    {"name": "NUM", "isTerminal": True, "isCapturing": True, "altName": "num"}
                ]
            }
        ]
    },
    "semantics": []
}


def test_arbno_class_field_has_is_list_true():
    model = build_model(_ARBNO_SPEC)
    rands = next(c for c in model['classes'] if c['name'] == 'Rands')
    assert rands['fields'][0]['is_list'] is True


def test_arbno_field_name_has_list_suffix():
    model = build_model(_ARBNO_SPEC)
    rands = next(c for c in model['classes'] if c['name'] == 'Rands')
    assert rands['fields'][0]['name'] == 'exprList'


def test_arbno_field_type_is_base_element_type():
    model = build_model(_ARBNO_SPEC)
    rands = next(c for c in model['classes'] if c['name'] == 'Rands')
    assert rands['fields'][0]['type'] == 'Expr'


def test_non_arbno_field_has_is_list_false():
    model = build_model(_TRIVIAL_SPEC)
    field = model['classes'][0]['fields'][0]
    assert field['is_list'] is False


def test_arbno_token_field_has_correct_type():
    spec = {
        "lexical": {"ruleList": []},
        "syntax": {
            "rules": [
                {
                    "lhs": {"name": "items", "altName": None, "isTerminal": False, "isCapturing": False},
                    "rhsSymbolList": [
                        {"name": "NUM", "isTerminal": True, "isCapturing": True, "altName": "num"}
                    ],
                    "separator": None
                }
            ]
        },
        "semantics": []
    }
    model = build_model(spec)
    items = next(c for c in model['classes'] if c['name'] == 'Items')
    assert items['fields'][0]['name'] == 'numList'
    assert items['fields'][0]['type'] == 'Token'
    assert items['fields'][0]['is_list'] is True
```

- [ ] **Step 2: Run tests to verify new tests fail**

Run: `bin/test/units.bash src/plcc/model/build_model_test.py -v`
Expected: `test_non_arbno_field_has_is_list_false` and the arbno tests FAIL; existing tests PASS.

- [ ] **Step 3: Implement the changes**

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
                'rule_name': nt_name,
            })
            for rule in nt_rules:
                alt_name = rule['lhs']['altName']
                fields = _extract_fields_for_rule(rule)
                classes.append({
                    'name': alt_name,
                    'abstract': False,
                    'extends': class_name,
                    'fields': fields,
                    'rule_name': nt_name,
                })
        else:
            rule = nt_rules[0]
            fields = _extract_fields_for_rule(rule)
            classes.append({
                'name': class_name,
                'abstract': False,
                'extends': None,
                'fields': fields,
                'rule_name': nt_name,
            })

    return classes


def _extract_fields_for_rule(rule):
    rhs = rule.get('rhsSymbolList', [])
    if 'separator' in rule:
        return _extract_arbno_fields(rhs)
    return _extract_fields(rhs)


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
            field_type = n[:1].upper() + n[1:]
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
            field_type = name[:1].upper() + name[1:]
        fields.append({'name': field_name, 'type': field_type, 'is_list': False})
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
            'entry_point': s.get('entry_point'),
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/model/build_model_test.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/model/build_model.py src/plcc/model/build_model_test.py
git commit -m "feat(model): detect arbno rules, emit is_list fields with List-suffix names"
```

---

## Task 6: `deserialize.py` — handle list values

**Files:**
- Modify: `src/plcc/lang/ext/python/runtime/deserialize.py`
- Modify: `src/plcc/lang/ext/python/runtime/deserialize_test.py`

The deserializer currently expects every child value to be a dict (token or tree node). After this task, it handles JSON arrays (list values) by recursively deserializing each element. Dispatch is purely type-driven — no field metadata needed.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/lang/ext/python/runtime/deserialize_test.py`:

```python
class FakeRands(Node):
    _rule_name = 'rands'
    _fields = ['exprList']

    def __init__(self, exprList):
        self.exprList = exprList


def test_deserialize_list_field_of_tokens():
    tree = {
        "kind": "tree",
        "rule": "rands",
        "children": [
            ["exprList", [
                {"kind": "token", "name": "NUM", "lexeme": "1"},
                {"kind": "token", "name": "NUM", "lexeme": "2"},
            ]]
        ]
    }
    reg = Registry()
    reg.register(FakeRands)
    result = deserialize(tree, reg)
    assert isinstance(result, FakeRands)
    assert len(result.exprList) == 2
    assert isinstance(result.exprList[0], Token)
    assert result.exprList[0].lexeme == '1'
    assert result.exprList[1].lexeme == '2'


def test_deserialize_empty_list_field():
    tree = {
        "kind": "tree",
        "rule": "rands",
        "children": [["exprList", []]]
    }
    reg = Registry()
    reg.register(FakeRands)
    result = deserialize(tree, reg)
    assert result.exprList == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bin/test/units.bash src/plcc/lang/ext/python/runtime/deserialize_test.py -v`
Expected: 2 new tests FAIL with TypeError or AttributeError; existing tests PASS.

- [ ] **Step 3: Implement the changes**

Replace `src/plcc/lang/ext/python/runtime/deserialize.py` with:

```python
from .base import Token


def deserialize(tree, registry):
    if tree['kind'] == 'token':
        return Token(kind=tree['name'], lexeme=tree['lexeme'])

    children = tree.get('children', [])
    field_names = [pair[0] for pair in children]
    cls = registry.lookup(tree['rule'], field_names)
    kwargs = {name: _deserialize_value(val, registry) for name, val in children}
    return cls(**kwargs)


def _deserialize_value(val, registry):
    if isinstance(val, list):
        return [_deserialize_value(item, registry) for item in val]
    if isinstance(val, dict) and val.get('kind') == 'token':
        return Token(kind=val['name'], lexeme=val['lexeme'])
    if isinstance(val, dict):
        return deserialize(val, registry)
    return val
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bin/test/units.bash src/plcc/lang/ext/python/runtime/deserialize_test.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/lang/ext/python/runtime/deserialize.py src/plcc/lang/ext/python/runtime/deserialize_test.py
git commit -m "feat(runtime): deserialize list values for arbno fields"
```

---

## Task 7: Integration bats test + regression check

**Files:**
- Modify: `tests/bats/e2e/plcc-rep.bats`

Verify the full pipeline works end-to-end with `trivial-arbno.plcc`, and that the existing `arith.plcc` REPL is unaffected.

- [ ] **Step 1: Write the failing bats tests**

Add to the end of `tests/bats/e2e/plcc-rep.bats`:

```bash
@test "trivial-arbno: plcc-rep evaluates 1, 2, 3 to [1, 2, 3]" {
    run bash -c "echo '1, 2, 3' | plcc-rep --tool=eval '${FIXTURES}/trivial-arbno.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == "[1, 2, 3]" ]]
}

@test "trivial-arbno: plcc-rep evaluates empty input to []" {
    run bash -c "echo '' | plcc-rep --tool=eval '${FIXTURES}/trivial-arbno.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == "[]" ]]
}

@test "trivial-arbno: plcc-rep evaluates single item 42 to [42]" {
    run bash -c "echo '42' | plcc-rep --tool=eval '${FIXTURES}/trivial-arbno.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == "[42]" ]]
}
```

- [ ] **Step 2: Run the new bats tests to verify they fail**

Run: `bin/test/e2e.bash`
Expected: the 3 new trivial-arbno tests FAIL; existing tests PASS.

- [ ] **Step 3: Run all unit tests to ensure nothing is broken**

Run: `bin/test/units.bash`
Expected: all PASS.

- [ ] **Step 4: Run commands-tier bats tests**

Run: `bin/test/commands.bash`
Expected: all PASS (including plcc-ll1, plcc-tree, plcc-model, plcc-rep commands).

- [ ] **Step 5: Run the full functional suite**

Run: `bin/test/functional.bash`
Expected: all PASS. If the arbno bats tests still fail, diagnose by running the pipeline manually:

```bash
# Manual pipeline trace
plcc-spec tests/fixtures/trivial-arbno.plcc > /tmp/spec.json
plcc-ll1 < /tmp/spec.json > /tmp/ll1.json
cat /tmp/ll1.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(list(d['arbno'].keys()))"
echo "1, 2, 3" | plcc-tokens /tmp/spec.json | plcc-tree --ll1=/tmp/ll1.json
```

- [ ] **Step 6: Commit**

```bash
git add tests/bats/e2e/plcc-rep.bats
git commit -m "test(e2e): add trivial-arbno.plcc end-to-end tests for plcc-rep"
```

---

## Acceptance Criteria Checklist

After all 7 tasks complete:

- [ ] `plcc-ll1` produces a correct `arbno` section for both plain and separator forms
- [ ] `plcc-tree` produces flat list nodes for all arbno nonterminals
- [ ] `plcc-model` emits `is_list: true` fields with correct names and types
- [ ] `plcc-rep --tool=eval tests/fixtures/trivial-arbno.plcc` with input `1, 2, 3` outputs `[1, 2, 3]`
- [ ] All existing tests pass (arith.plcc REPL unaffected)
