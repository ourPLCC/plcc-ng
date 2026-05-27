# Thread altName through LL(1) pipeline (issue 045) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the bug where alternative class names (`<expr>:Add`) are lost in the LL(1) pipeline, causing parse tree nodes to always carry the base nonterminal name instead of the correct class name.

**Architecture:** Introduce a `Rule` dataclass (alt name + field names) in `spec_json_decoder.py` to replace the bare-list `field_map`. Thread it through `ll1_result_builder.py`, changing parse table cells from bare lists to `{"alt": ..., "production": [...]}` dicts. Update `predictive_parser.py` to read `cell["alt"]` when naming tree nodes.

**Tech Stack:** Python 3.14, pytest, `dataclasses` stdlib module. Tests run via `bin/test/units.bash`.

---

## File map

| File | Change |
|------|--------|
| `src/plcc/ll1/spec_json_decoder.py` | Add `Rule` dataclass; read `altName`; build `productions` dict |
| `src/plcc/ll1/spec_json_decoder_test.py` | Assert `Rule` objects; add altName test |
| `src/plcc/ll1/ll1_result_builder.py` | Accept `productions`; `_prod_entry` emits new cell shape |
| `src/plcc/ll1/ll1_result_builder_test.py` | Update fixtures to `Rule`; update cell assertions |
| `src/plcc/ll1/ll1_cli.py` | Rename local `field_map` → `productions` |
| `src/plcc/parser/predictive_parser.py` | Read `cell["alt"]` and `cell["production"]` in `_parse_regular` |
| `src/plcc/parser/predictive_parser_test.py` | Update fixtures to new cell shape; add alt-name tree test |
| `src/plcc/parser/table_cli_test.py` | Update fixtures to new cell shape |

---

## Task 1: Define the `Rule` dataclass

**Files:**
- Modify: `src/plcc/ll1/spec_json_decoder.py`
- Test: `src/plcc/ll1/spec_json_decoder_test.py`

- [ ] **Step 1: Write the failing test**

Add at the top of `src/plcc/ll1/spec_json_decoder_test.py`, after the existing import:

```python
from plcc.ll1.spec_json_decoder import Rule
```

Then add this test at the end of the file:

```python
def test_rule_is_dataclass_with_alt_and_fields():
    r = Rule(alt="Add", fields=["left", None])
    assert r.alt == "Add"
    assert r.fields == ["left", None]


def test_rule_alt_can_be_none():
    r = Rule(alt=None, fields=[])
    assert r.alt is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py -v -k "test_rule"
```

Expected: `ImportError: cannot import name 'Rule'`

- [ ] **Step 3: Add `Rule` to `spec_json_decoder.py`**

Add at the top of `src/plcc/ll1/spec_json_decoder.py`, after the existing import:

```python
from dataclasses import dataclass


@dataclass
class Rule:
    alt: str | None
    fields: list[str | None]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py -v -k "test_rule"
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/ll1/spec_json_decoder.py src/plcc/ll1/spec_json_decoder_test.py
git commit -m "feat: add Rule dataclass to spec_json_decoder"
```

---

## Task 2: Update `decode()` to build `productions` with `Rule` objects

**Files:**
- Modify: `src/plcc/ll1/spec_json_decoder.py`
- Test: `src/plcc/ll1/spec_json_decoder_test.py`

- [ ] **Step 1: Update existing decoder tests to assert `Rule` objects**

In `src/plcc/ll1/spec_json_decoder_test.py`, every call to `decode()` unpacks three values. Change
every assertion that inspects the second return value (currently called `field_map`) to use `Rule`
objects instead of bare lists. Also add a test for `altName` on the LHS.

Replace the entire test file content with:

```python
import pytest
from plcc.ll1.spec_json_decoder import decode, Rule


def _spec(rules):
    return {"lexical": {"ruleList": []}, "syntax": {"rules": rules}, "semantics": []}


def _rule(lhs_name, rhs_syms, alt_name=None):
    return {
        "line": {"string": "", "number": 0, "file": ""},
        "lhs": {"name": lhs_name, "isTerminal": False, "altName": alt_name, "isCapturing": False},
        "rhsSymbolList": rhs_syms,
    }


def _terminal(name, capturing=False, alt_name=None):
    d = {"name": name, "isTerminal": True, "isCapturing": capturing}
    if alt_name is not None:
        d["altName"] = alt_name
    return d


def _nonterminal(name, capturing=False, alt_name=None):
    d = {"name": name, "isTerminal": False, "isCapturing": capturing}
    if alt_name is not None:
        d["altName"] = alt_name
    return d


def test_rule_is_dataclass_with_alt_and_fields():
    r = Rule(alt="Add", fields=["left", None])
    assert r.alt == "Add"
    assert r.fields == ["left", None]


def test_rule_alt_can_be_none():
    r = Rule(alt=None, fields=[])
    assert r.alt is None


def test_empty_grammar():
    grammar, productions, arbno_rules = decode(_spec([]))
    assert grammar.getStartSymbol() is None
    assert productions == {}


def test_single_rule_noncapturing():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("program", [_terminal("NUM")])
    ]))
    assert grammar.getStartSymbol() == "program"
    assert list(grammar.getForms("program")) == [("NUM",)]
    assert productions == {("program", ("NUM",)): Rule(alt=None, fields=[None])}


def test_epsilon_rule():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("empty", [])
    ]))
    assert grammar.getStartSymbol() == "empty"
    assert list(grammar.getForms("empty")) == [()]
    assert productions == {("empty", ()): Rule(alt=None, fields=[])}


def test_capturing_terminal_uses_name_lower():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("E", [_terminal("NUM", capturing=True)])
    ]))
    assert productions == {("E", ("NUM",)): Rule(alt=None, fields=["num"])}


def test_capturing_terminal_uses_alt_name():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("E", [_terminal("NUM", capturing=True, alt_name="value")])
    ]))
    assert productions == {("E", ("NUM",)): Rule(alt=None, fields=["value"])}


def test_capturing_nonterminal_uses_name_lower():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("E", [_nonterminal("Term", capturing=True)])
    ]))
    assert productions == {("E", ("Term",)): Rule(alt=None, fields=["term"])}


def test_multiple_symbols():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("E", [_nonterminal("T", capturing=True), _terminal("PLUS"), _nonterminal("E", capturing=True, alt_name="r")])
    ]))
    assert productions == {("E", ("T", "PLUS", "E")): Rule(alt=None, fields=["t", None, "r"])}


def test_start_symbol_is_first_rule_lhs():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("first", [_terminal("A")]),
        _rule("second", [_terminal("B")]),
    ]))
    assert grammar.getStartSymbol() == "first"


def test_lhs_alt_name_captured_in_rule():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("expr", [_terminal("PLUS"), _nonterminal("expr"), _nonterminal("expr")], alt_name="Add"),
        _rule("expr", [_terminal("NUM")], alt_name="Num"),
    ]))
    assert productions[("expr", ("PLUS", "expr", "expr"))].alt == "Add"
    assert productions[("expr", ("NUM",))].alt == "Num"


def test_lhs_alt_name_none_when_absent():
    grammar, productions, arbno_rules = decode(_spec([
        _rule("program", [_terminal("NUM")])
    ]))
    assert productions[("program", ("NUM",))].alt is None


def _arbno_rule(lhs_name, rhs_syms, separator_name):
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
    grammar, productions, arbno_rules = decode(_spec([]))
    assert isinstance(arbno_rules, dict)


def test_non_arbno_rules_not_in_arbno_rules():
    grammar, productions, arbno_rules = decode(_spec([
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
    grammar, productions, arbno_rules = decode(spec)
    assert "rands" in arbno_rules


def test_separator_arbno_rhs_field_has_list_suffix():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("expr", capturing=True, alt_name="expr")],
                    "COMMA"),
        _rule("expr", [_terminal("NUM")]),
    ])
    grammar, productions, arbno_rules = decode(spec)
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
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["rands"]["separator"] == "COMMA"


def test_plain_arbno_separator_is_none():
    spec = _spec([
        _arbno_rule("cmds",
                    [_nonterminal("cmd", capturing=True, alt_name="cmd")],
                    None),
        _rule("cmd", [_terminal("X")]),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["cmds"]["separator"] is None


def test_arbno_expansion_adds_internal_rules_to_grammar():
    spec = _spec([
        _arbno_rule("rands",
                    [_nonterminal("expr", capturing=True, alt_name="expr")],
                    "COMMA"),
        _rule("expr", [_terminal("NUM")]),
    ])
    grammar, productions, arbno_rules = decode(spec)
    nts = grammar.getNonterminalSet()
    assert "rands" in nts
    assert "rands#" in nts


def test_arbno_terminal_rhs_item():
    spec = _spec([
        _arbno_rule("tokens",
                    [_terminal("NUM", capturing=True, alt_name="num")],
                    None),
    ])
    grammar, productions, arbno_rules = decode(spec)
    assert arbno_rules["tokens"]["rhs"] == [
        {"field": "numList", "symbol": "NUM", "is_terminal": True}
    ]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py -v
```

Expected: multiple failures — `AssertionError` on `productions == {("program", ("NUM",)): [None]}` (bare list vs `Rule`) and `test_lhs_alt_name_captured_in_rule` failing because `altName` isn't read yet.

- [ ] **Step 3: Update `spec_json_decoder.py` implementation**

Replace the full content of `src/plcc/ll1/spec_json_decoder.py`:

```python
from dataclasses import dataclass

from plcc.spec.syntax.validations.ll1.Grammar import Grammar


@dataclass
class Rule:
    alt: str | None
    fields: list[str | None]


def decode(spec_dict: dict) -> tuple:
    """
    Build a Grammar from a spec JSON dict.

    Returns (grammar, productions, arbno_rules) where:
      grammar     — Grammar with both regular and internal arbno expansion rules
      productions — dict[(nt_name, prod_tuple)] -> Rule
      arbno_rules — dict[nt_name] -> {rhs, separator}
    """
    grammar = Grammar()
    productions = {}
    arbno_rules = {}
    for rule in spec_dict.get("syntax", {}).get("rules", []):
        nt = rule["lhs"]["name"]
        alt = rule["lhs"].get("altName")
        rhs = rule.get("rhsSymbolList", [])
        if "separator" in rule:
            _handle_arbno(grammar, arbno_rules, nt, rhs, rule["separator"])
        elif not rhs:
            grammar.addRule(nt, [])
            productions[(nt, ())] = Rule(alt=alt, fields=[])
        else:
            syms = [s["name"] for s in rhs]
            fields = [_field(s) for s in rhs]
            grammar.addRule(nt, syms)
            productions[(nt, tuple(syms))] = Rule(alt=alt, fields=fields)
    return grammar, productions, arbno_rules


def _handle_arbno(grammar, arbno_rules, nt, rhs, separator_entry):
    separator = separator_entry["name"] if separator_entry else None
    cont = nt + "#"
    syms = [s["name"] for s in rhs]

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

```bash
bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/ll1/spec_json_decoder.py src/plcc/ll1/spec_json_decoder_test.py
git commit -m "feat: decode() reads altName into Rule.alt; productions replaces field_map"
```

---

## Task 3: Update `ll1_result_builder.py` to consume `productions` and emit new cell shape

**Files:**
- Modify: `src/plcc/ll1/ll1_result_builder.py`
- Modify: `src/plcc/ll1/ll1_cli.py`
- Test: `src/plcc/ll1/ll1_result_builder_test.py`

- [ ] **Step 1: Update `ll1_result_builder_test.py` fixtures and assertions**

Replace the full content of `src/plcc/ll1/ll1_result_builder_test.py`:

```python
from plcc.spec.syntax.validations.ll1.Grammar import Grammar
from plcc.ll1.spec_json_decoder import Rule
from plcc.ll1.ll1_result_builder import build_ll1_result


def _simple_grammar():
    """program → NUM (not capturing)"""
    g = Grammar()
    g.addRule("program", ["NUM"])
    fm = {("program", ("NUM",)): Rule(alt=None, fields=[None])}
    return g, fm


def _epsilon_grammar():
    """rest →  (epsilon)"""
    g = Grammar()
    g.addRule("rest", [])
    fm = {("rest", ()): Rule(alt=None, fields=[])}
    return g, fm


def _conflict_grammar():
    """A → X | X Y  (two productions with same first token → conflict)"""
    g = Grammar()
    g.addRule("A", ["X"])
    g.addRule("A", ["X", "Y"])
    fm = {
        ("A", ("X",)): Rule(alt=None, fields=[None]),
        ("A", ("X", "Y")): Rule(alt=None, fields=[None, None]),
    }
    return g, fm


def _left_recursive_grammar():
    """A → A B | C  (direct left recursion)"""
    g = Grammar()
    g.addRule("A", ["A", "B"])
    g.addRule("A", ["C"])
    fm = {
        ("A", ("A", "B")): Rule(alt=None, fields=[None, None]),
        ("A", ("C",)): Rule(alt=None, fields=[None]),
    }
    return g, fm


def test_is_ll1_true_for_simple_grammar():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["is_ll1"] is True


def test_start_symbol_present():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["start_symbol"] == "program"


def test_first_sets_correct():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["first_sets"]["program"] == ["NUM"]


def test_follow_sets_contain_dollar():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert "eof" in result["follow_sets"]["program"]


def test_predict_sets_correct():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["predict_sets"]["program"] == [["NUM"]]


def test_parse_table_entry_correct():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["parse_table"]["program"]["NUM"] == {
        "alt": None,
        "production": [{"symbol": "NUM", "field": None}],
    }


def test_conflicts_empty_for_ll1_grammar():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["conflicts"] == []


def test_left_recursion_empty_for_ll1_grammar():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["left_recursion"] == []


def test_epsilon_production_in_parse_table():
    g, fm = _epsilon_grammar()
    result = build_ll1_result(g, fm)
    assert result["parse_table"]["rest"]["eof"] == {"alt": None, "production": []}


def test_epsilon_in_first_sets():
    g, fm = _epsilon_grammar()
    result = build_ll1_result(g, fm)
    assert "" in result["first_sets"]["rest"]


def test_is_ll1_false_for_conflict_grammar():
    g, fm = _conflict_grammar()
    result = build_ll1_result(g, fm)
    assert result["is_ll1"] is False
    assert len(result["conflicts"]) > 0


def test_conflict_cell_omitted_from_parse_table():
    g, fm = _conflict_grammar()
    result = build_ll1_result(g, fm)
    assert "X" not in result["parse_table"].get("A", {})


def test_conflict_entry_has_required_fields():
    g, fm = _conflict_grammar()
    result = build_ll1_result(g, fm)
    c = result["conflicts"][0]
    assert c["nonterminal"] == "A"
    assert c["lookahead"] == "X"
    assert len(c["productions"]) == 2


def test_left_recursion_detected():
    g, fm = _left_recursive_grammar()
    result = build_ll1_result(g, fm)
    assert result["is_ll1"] is False
    assert len(result["left_recursion"]) > 0


def test_left_recursion_cycle_format():
    g, fm = _left_recursive_grammar()
    result = build_ll1_result(g, fm)
    cycle = result["left_recursion"][0]["cycle"]
    assert cycle[0] == cycle[-1]
    assert "A" in cycle


def test_capturing_symbol_field_in_parse_table():
    g = Grammar()
    g.addRule("E", ["NUM"])
    fm = {("E", ("NUM",)): Rule(alt=None, fields=["num"])}
    result = build_ll1_result(g, fm)
    entry = result["parse_table"]["E"]["NUM"]
    assert entry == {"alt": None, "production": [{"symbol": "NUM", "field": "num"}]}


def test_alt_name_appears_in_parse_table_cell():
    g = Grammar()
    g.addRule("expr", ["PLUS", "expr", "expr"])
    g.addRule("expr", ["NUM"])
    fm = {
        ("expr", ("PLUS", "expr", "expr")): Rule(alt="Add", fields=[None, "left", "right"]),
        ("expr", ("NUM",)): Rule(alt="Num", fields=["val"]),
    }
    result = build_ll1_result(g, fm)
    assert result["parse_table"]["expr"]["PLUS"]["alt"] == "Add"
    assert result["parse_table"]["expr"]["NUM"]["alt"] == "Num"


def test_alt_name_null_when_absent():
    g, fm = _simple_grammar()
    result = build_ll1_result(g, fm)
    assert result["parse_table"]["program"]["NUM"]["alt"] is None


def test_conflict_productions_carry_alt_name():
    g = Grammar()
    g.addRule("expr", ["PLUS", "expr", "expr"])
    g.addRule("expr", ["PLUS", "NUM"])
    fm = {
        ("expr", ("PLUS", "expr", "expr")): Rule(alt="Add", fields=[None, "left", "right"]),
        ("expr", ("PLUS", "NUM")): Rule(alt="Neg", fields=[None, "val"]),
    }
    result = build_ll1_result(g, fm)
    assert result["is_ll1"] is False
    alts = {p["alt"] for p in result["conflicts"][0]["productions"]}
    assert alts == {"Add", "Neg"}


def _arbno_grammar_and_rules():
    g = Grammar()
    g.addRule("rands", ["expr", "rands#"])
    g.addRule("rands", [])
    g.addRule("rands#", ["COMMA", "expr", "rands#"])
    g.addRule("rands#", [])
    g.addRule("expr", ["NUM"])
    fm = {
        ("rands",  ("expr", "rands#")): Rule(alt=None, fields=[None, None]),
        ("rands",  ()):                 Rule(alt=None, fields=[]),
        ("rands#", ("COMMA", "expr", "rands#")): Rule(alt=None, fields=[None, None, None]),
        ("rands#", ()):                 Rule(alt=None, fields=[]),
        ("expr",   ("NUM",)):           Rule(alt=None, fields=[None]),
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

```bash
bin/test/units.bash src/plcc/ll1/ll1_result_builder_test.py -v
```

Expected: multiple failures — `ImportError` for `Rule` import, and cell format assertions failing because builder still returns bare lists.

- [ ] **Step 3: Update `ll1_result_builder.py` implementation**

Replace the full content of `src/plcc/ll1/ll1_result_builder.py`:

```python
from plcc.spec.syntax.validations.ll1.Grammar import Grammar
from plcc.spec.syntax.validations.ll1.build_first_sets import build_first_sets
from plcc.spec.syntax.validations.ll1.build_follow_sets import build_follow_sets
from plcc.spec.syntax.validations.ll1.build_parsing_table import build_parsing_table
from plcc.spec.syntax.validations.ll1.check_parsing_table_for_ll1 import check_parsing_table_for_ll1
from plcc.spec.syntax.validations.ll1.check_left_recursion import check_left_recursion


def build_ll1_result(grammar: Grammar, productions: dict, arbno_rules: dict = None) -> dict:
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
            return "eof"
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
        parse_table.setdefault(nt, {})[lookahead] = _prod_entry(nt, prod, productions, eps)

    conflicts = []

    def cell_sort_key(cell):
        nt, t = cell
        return (nt, tok(t))

    for (nt, t) in sorted(bad_cells, key=cell_sort_key):
        if nt in internal_nts:
            continue
        prods = table.getCell(nt, t)
        lookahead = tok(t)
        conflict_productions = [
            _prod_entry(nt, p, productions, eps)
            for p in sorted(prods, key=str)
        ]
        conflicts.append({"nonterminal": nt, "lookahead": lookahead, "productions": conflict_productions})

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


def _prod_entry(nt: str, prod: tuple, productions: dict, eps) -> dict:
    rule = productions.get((nt, prod))
    alt = rule.alt if rule is not None else None
    fields = rule.fields if rule is not None else [None] * len(prod)
    return {
        "alt": alt,
        "production": [
            {"symbol": sym, "field": fld}
            for sym, fld in zip(prod, fields)
            if sym is not eps
        ],
    }
```

- [ ] **Step 4: Update `ll1_cli.py` — rename local variable**

In `src/plcc/ll1/ll1_cli.py`, change line 44:

```python
# Before
grammar, field_map, arbno_rules = decode(spec)
result = build_ll1_result(grammar, field_map, arbno_rules)

# After
grammar, productions, arbno_rules = decode(spec)
result = build_ll1_result(grammar, productions, arbno_rules)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/ll1/ll1_result_builder_test.py src/plcc/ll1/ll1_cli_test.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/ll1/ll1_result_builder.py src/plcc/ll1/ll1_result_builder_test.py src/plcc/ll1/ll1_cli.py
git commit -m "feat: ll1_result_builder emits new cell shape {alt, production}"
```

---

## Task 4: Update `predictive_parser.py` to use the new cell shape

**Files:**
- Modify: `src/plcc/parser/predictive_parser.py`
- Test: `src/plcc/parser/predictive_parser_test.py`

- [ ] **Step 1: Update `predictive_parser_test.py` fixtures and add alt-name test**

Replace the full content of `src/plcc/parser/predictive_parser_test.py`:

```python
import pytest
from plcc.parser.predictive_parser import parse, ParseError


# ll1.json dict for grammar: program → NUM  (NUM is non-capturing, field=null)
_TRIVIAL_LL1 = {
    "is_ll1": True,
    "start_symbol": "program",
    "parse_table": {
        "program": {
            "NUM": {"alt": None, "production": [{"symbol": "NUM", "field": None}]}
        }
    },
}

# ll1.json dict for grammar: E → t:Term; Term → n:NUM
_EXPR_LL1 = {
    "is_ll1": True,
    "start_symbol": "E",
    "parse_table": {
        "E": {
            "NUM": {"alt": None, "production": [{"symbol": "Term", "field": "t"}]}
        },
        "Term": {
            "NUM": {"alt": None, "production": [{"symbol": "NUM", "field": "n"}]}
        },
    },
}

# E → NUM PLUS NUM  (simple, no nesting, both NUMs captured)
_FLAT_EXPR_LL1 = {
    "is_ll1": True,
    "start_symbol": "E",
    "parse_table": {
        "E": {
            "NUM": {"alt": None, "production": [
                {"symbol": "NUM", "field": "left"},
                {"symbol": "PLUS", "field": None},
                {"symbol": "NUM", "field": "right"},
            ]}
        }
    },
}

# prefix expr grammar: <expr>:Add ::= PLUS <expr> <expr> | <expr>:Num ::= NUM
_PREFIX_LL1 = {
    "is_ll1": True,
    "start_symbol": "expr",
    "parse_table": {
        "expr": {
            "PLUS": {"alt": "Add", "production": [
                {"symbol": "PLUS", "field": None},
                {"symbol": "expr", "field": "left"},
                {"symbol": "expr", "field": "right"},
            ]},
            "NUM": {"alt": "Num", "production": [{"symbol": "NUM", "field": "val"}]},
        }
    },
}

def _tok(name, lexeme, line=1, col=1, file="<stdin>"):
    return {"kind": "token", "name": name, "lexeme": lexeme,
            "source": {"file": file, "line": line, "column": col}}


# --- trivial grammar tests ---

def test_trivial_parse_returns_tree_kind():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert tree["kind"] == "tree"


def test_trivial_parse_rule_is_start_symbol():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert tree["rule"] == "program"


def test_trivial_parse_elided_symbol_not_in_children():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert tree["children"] == []


def test_trivial_parse_source_span():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42", line=3, col=5)])
    src = tree["source"]
    assert src["line"] == 3
    assert src["column"] == 5
    assert src["endLine"] == 3
    assert src["endColumn"] == 6


def test_trivial_parse_source_file():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42", file="prog.txt")])
    assert tree["source"]["file"] == "prog.txt"


# --- alt name tests ---

def test_alt_name_used_as_rule_in_tree():
    tree, _ = parse(_PREFIX_LL1, [_tok("PLUS", "+"), _tok("NUM", "2"), _tok("NUM", "3")])
    assert tree["rule"] == "Add"


def test_alt_name_on_leaf_node():
    tree, _ = parse(_PREFIX_LL1, [_tok("NUM", "42")])
    assert tree["rule"] == "Num"


def test_no_alt_name_uses_nonterminal_name():
    tree, _ = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert tree["rule"] == "program"


# --- capturing symbol tests ---

def test_capturing_child_in_children():
    tree, _ = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1", col=1),
        _tok("PLUS", "+", col=2),
        _tok("NUM", "2", col=3),
    ])
    fields = [child[0] for child in tree["children"]]
    assert "left" in fields
    assert "right" in fields


def test_capturing_children_are_token_dicts():
    tree, _ = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1"),
        _tok("PLUS", "+"),
        _tok("NUM", "2"),
    ])
    left = dict(tree["children"])["left"]
    assert left["kind"] == "token"
    assert left["name"] == "NUM"
    assert left["lexeme"] == "1"


def test_elided_plus_not_in_children():
    tree, _ = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1"),
        _tok("PLUS", "+"),
        _tok("NUM", "2"),
    ])
    fields = [child[0] for child in tree["children"]]
    assert "PLUS" not in fields


# --- span across multiple tokens ---

def test_span_covers_all_tokens_including_elided():
    tree, _ = parse(_FLAT_EXPR_LL1, [
        _tok("NUM", "1", col=1),
        _tok("PLUS", "+", col=3),
        _tok("NUM", "2", col=5),
    ])
    src = tree["source"]
    assert src["column"] == 1
    assert src["endColumn"] == 5


# --- nested nonterminal tests ---

def test_nested_nonterminal_child_is_tree():
    tree, _ = parse(_EXPR_LL1, [
        _tok("NUM", "3"),
    ])
    assert tree["rule"] == "E"
    children_dict = dict(tree["children"])
    assert "t" in children_dict
    assert children_dict["t"]["kind"] == "tree"
    assert children_dict["t"]["rule"] == "Term"


# --- error cases ---

def test_wrong_terminal_raises_parse_error():
    with pytest.raises(ParseError):
        parse(_TRIVIAL_LL1, [_tok("IDENTIFIER", "x")])


def test_no_production_for_lookahead_raises_parse_error():
    ll1 = {
        "is_ll1": True,
        "start_symbol": "A",
        "parse_table": {"A": {"X": {"alt": None, "production": [{"symbol": "X", "field": None}]}}},
    }
    with pytest.raises(ParseError):
        parse(ll1, [_tok("Y", "y")])


def test_empty_input_on_nonempty_grammar_raises_parse_error():
    with pytest.raises(ParseError):
        parse(_TRIVIAL_LL1, [])


# ll1 dict for: rands **= expr +COMMA, expr → NUM
_RANDS_LL1 = {
    "is_ll1": True,
    "start_symbol": "rands",
    "parse_table": {
        "expr": {
            "NUM": {"alt": None, "production": [{"symbol": "NUM", "field": "num"}]}
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
            "X": {"alt": None, "production": [{"symbol": "X", "field": "x"}]}
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
    tree, _ = parse(_RANDS_LL1, [
        _tok("NUM", "1"),
        _tok("COMMA", ","),
        _tok("NUM", "2"),
    ])
    children_dict = dict(tree["children"])
    assert "exprList" in children_dict
    assert isinstance(children_dict["exprList"], list)
    assert len(children_dict["exprList"]) == 2


def test_arbno_separator_list_items_are_tree_nodes():
    tree, _ = parse(_RANDS_LL1, [
        _tok("NUM", "1"),
        _tok("COMMA", ","),
        _tok("NUM", "2"),
    ])
    expr_list = dict(tree["children"])["exprList"]
    assert expr_list[0]["kind"] == "tree"
    assert expr_list[0]["rule"] == "expr"
    assert expr_list[1]["kind"] == "tree"


def test_arbno_separator_zero_items_on_no_match():
    tree, _ = parse(_RANDS_LL1, [])
    children_dict = dict(tree["children"])
    assert children_dict["exprList"] == []


def test_arbno_separator_one_item():
    tree, _ = parse(_RANDS_LL1, [_tok("NUM", "42")])
    children_dict = dict(tree["children"])
    assert len(children_dict["exprList"]) == 1


def test_arbno_plain_multiple_items():
    tree, _ = parse(_CMDS_LL1, [
        _tok("X", "a"),
        _tok("X", "b"),
        _tok("X", "c"),
    ])
    children_dict = dict(tree["children"])
    assert len(children_dict["cmdList"]) == 3


def test_arbno_plain_zero_items():
    tree, _ = parse(_CMDS_LL1, [])
    children_dict = dict(tree["children"])
    assert children_dict["cmdList"] == []


def test_arbno_result_is_tree_kind():
    tree, _ = parse(_RANDS_LL1, [_tok("NUM", "1")])
    assert tree["kind"] == "tree"
    assert tree["rule"] == "rands"


_ADDITION_LL1 = {
    "is_ll1": True,
    "start_symbol": "program",
    "parse_table": {
        "program": {
            "NUM": {"alt": None, "production": [
                {"symbol": "NUM", "field": None},
                {"symbol": "PLUS", "field": None},
                {"symbol": "NUM", "field": None},
            ]}
        }
    },
}


def test_incomplete_raises_ParseError():
    with pytest.raises(ParseError):
        parse(_ADDITION_LL1, [_tok("NUM", "1")])


def test_bad_token_raises_ParseError():
    with pytest.raises(ParseError):
        parse(_TRIVIAL_LL1, [_tok("PLUS", "+")])


def test_parse_error_carries_source():
    with pytest.raises(ParseError) as exc_info:
        parse(_TRIVIAL_LL1, [_tok("PLUS", "+", line=3, col=7)])
    assert exc_info.value.source["line"] == 3
    assert exc_info.value.source["column"] == 7


def test_parse_returns_consumed_count():
    _, consumed = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert consumed == 1


def test_parse_stops_at_first_unconsumed_token():
    tree, consumed = parse(_TRIVIAL_LL1, [_tok("NUM", "1"), _tok("NUM", "2")])
    assert consumed == 1
    assert tree["kind"] == "tree"


def test_incomplete_raises_ParseError_not_IncompleteInputError():
    with pytest.raises(ParseError):
        parse(_ADDITION_LL1, [_tok("NUM", "1")])


def test_parse_error_found_is_set_for_wrong_terminal():
    with pytest.raises(ParseError) as exc_info:
        parse(_TRIVIAL_LL1, [_tok("PLUS", "+")])
    assert exc_info.value.found == "PLUS"


def test_parse_error_found_is_eof_for_premature_end_of_input():
    with pytest.raises(ParseError) as exc_info:
        parse(_ADDITION_LL1, [_tok("NUM", "1")])
    assert exc_info.value.found == "eof"


def test_parse_error_found_is_none_by_default():
    e = ParseError("something went wrong")
    assert e.found is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/units.bash src/plcc/parser/predictive_parser_test.py -v
```

Expected: `TypeError: string indices must be integers` on most tests (iterating the dict `{"alt": ..., "production": [...]}` yields string keys `"alt"` and `"production"`, and `entry["symbol"]` on a string fails); plus wrong `rule` value on the new alt-name tests.

- [ ] **Step 3: Update `predictive_parser.py`**

In `src/plcc/parser/predictive_parser.py`, change the two marked lines inside `_parse_regular`:

```python
    def _parse_regular(sym):
        lookahead = current()["name"]
        nt_table = parse_table.get(sym)
        if nt_table is None:
            raise ParseError(
                f"no parse table entry for nonterminal {sym!r}",
                source=current()["source"],
            )
        production = nt_table.get(lookahead)
        if production is None:
            raise ParseError(
                f"unexpected {lookahead!r}, no production for {sym!r}",
                source=current()["source"],
                found=lookahead,
            )
        builder = NodeBuilder(production.get("alt") or sym)
        for entry in production["production"]:
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/parser/predictive_parser_test.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/parser/predictive_parser.py src/plcc/parser/predictive_parser_test.py
git commit -m "feat: predictive_parser uses cell alt name for tree node rule"
```

---

## Task 5: Update `table_cli_test.py` fixtures

**Files:**
- Test: `src/plcc/parser/table_cli_test.py`

- [ ] **Step 1: Update all inline fixtures to new cell shape**

Replace the five inline ll1 fixture dicts at the top of `src/plcc/parser/table_cli_test.py`. No test logic changes — only the cell values inside `parse_table`.

```python
_TRIVIAL_LL1 = {
    "is_ll1": True,
    "start_symbol": "program",
    "parse_table": {
        "program": {
            "NUM": {"alt": None, "production": [{"symbol": "NUM", "field": None}]}
        }
    },
}

_NON_LL1 = {
    "is_ll1": False,
    "start_symbol": "program",
    "parse_table": {},
    "conflicts": [{"nonterminal": "program", "lookahead": "NUM", "productions": []}],
    "left_recursion": [],
}

_CAPTURING_LL1 = {
    "is_ll1": True,
    "start_symbol": "E",
    "parse_table": {
        "E": {"NUM": {"alt": None, "production": [{"symbol": "NUM", "field": "num"}]}}
    },
}

_ADDITION_LL1 = {
    "is_ll1": True,
    "start_symbol": "program",
    "parse_table": {
        "program": {
            "NUM": {"alt": None, "production": [
                {"symbol": "NUM", "field": None},
                {"symbol": "PLUS", "field": None},
                {"symbol": "NUM", "field": None},
            ]}
        }
    },
}

_EXP_LL1 = {
    "is_ll1": True,
    "start_symbol": "exp",
    "parse_table": {
        "exp": {
            "NUM": {"alt": None, "production": [
                {"symbol": "NUM", "field": None},
                {"symbol": "exp2", "field": None},
            ]}
        },
        "exp2": {
            "OP": {"alt": None, "production": [
                {"symbol": "OP", "field": None},
                {"symbol": "exp", "field": None},
            ]},
            "eof": {"alt": None, "production": []},
        },
    },
}
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
bin/test/units.bash src/plcc/parser/table_cli_test.py -v
```

Expected: all pass.

- [ ] **Step 3: Run the full unit suite to verify nothing is broken**

```bash
bin/test/units.bash
```

Expected: 810+ passed, 0 failed.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/parser/table_cli_test.py
git commit -m "test: update table_cli fixtures to new cell shape {alt, production}"
```
