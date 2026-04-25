# LL(1) Analysis Implementation Plan (Phase 2 Part 1 — Plan 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `plcc-ll1` stub with a real LL(1) analysis implementation that computes FIRST/FOLLOW sets, predict sets, a parse table, conflict list, and left-recursion cycles, writing a complete `ll1.json` to stdout. Also updates the ll1.json schema, verifies `plcc-spec` separation, and adds verbose support to `plcc-parser-list`.

**Architecture:** `plcc-ll1` reads spec JSON from stdin, builds a `Grammar` (base class, string-keyed) using a new `spec_json_decoder` module, then calls the existing LL(1) computation functions unchanged and serialises results via a new `ll1_result_builder` module. `plcc-make` is updated to pass spec JSON via stdin. Bats tests are updated to drop the file-path argument.

**Tech Stack:** Python 3.12, docopt-ng, pytest, bats, check-jsonschema. All new LL(1) computation is done by the existing code under `src/plcc/spec/syntax/validations/ll1/`.

---

## File Map

| Action | Path |
|--------|------|
| Modify | `src/plcc/schemas/ll1.schema.json` |
| Modify | `src/plcc/spec/plcc_spec_cli.py` |
| Modify | `src/plcc/parser/list_cli.py` |
| Create | `src/plcc/ll1/spec_json_decoder.py` |
| Create | `src/plcc/ll1/spec_json_decoder_test.py` |
| Create | `src/plcc/ll1/ll1_result_builder.py` |
| Create | `src/plcc/ll1/ll1_result_builder_test.py` |
| Modify | `src/plcc/ll1/ll1_cli.py` |
| Modify | `src/plcc/ll1/ll1_cli_test.py` |
| Modify | `src/plcc/cmd/make.py` |
| Modify | `tests/bats/commands/plcc-ll1.bats` |
| Modify | `tests/bats/commands/plcc-parser-list.bats` |
| Modify | `tests/bats/commands/plcc-parser-table.bats` |
| Modify | `tests/bats/integration/ll1-tree.bats` |
| Modify | `tests/bats/e2e/error-propagation.bats` |

---

## Context for Every Task

The existing LL(1) computation lives in `src/plcc/spec/syntax/validations/ll1/`. **Never delete or rewrite that code.** It is well-tested student work. The plan builds a thin adapter layer on top.

Key existing functions (all take / return the base `Grammar` class with string-or-object symbol keys):
- `build_first_sets(grammar)` → `defaultdict(set)` — keys are symbol strings + production tuples; values are sets of symbol strings + epsilon sentinel object
- `build_follow_sets(grammar, firsts)` → `defaultdict(set)` — keys are nonterminal strings; values are sets of terminal strings + eof sentinel object
- `build_parsing_table(firsts, follows, grammar)` → `Table` — `getKeys()` yields `(nt_str, terminal_str_or_eof)`; `getCell(nt, t)` returns `set[tuple[str|eof]]`
- `check_parsing_table_for_ll1(table)` → `list[LL1Error]` — `error.cell = (nt_str, terminal_str_or_eof)`, `error.production = set[tuple]`
- `check_left_recursion(grammar)` → `list[list[(lhs_str, rhs_tuple)]]` — each inner list is one cycle

**Important:** `Grammar` (base class) uses string symbols throughout. `grammar.getEpsilon()` returns a unique `object()` instance (not a string). `grammar.getEof()` returns another unique `object()` instance. These are compared by identity (`is`), not by value. The `SpecGrammar` subclass is NOT compatible with these algorithms (its `getForms()` delegates to a different store); always use the base `Grammar` class.

**Epsilon in JSON:** `""` (empty string). **EOF in JSON:** `"$"`.

**Key spec JSON structure** (output of `plcc-spec`):
```json
{
  "lexical": {"ruleList": [...]},
  "syntax": {"rules": [
    {
      "line": {"string": "<program> ::= NUM", "number": 3, "file": "tests/fixtures/trivial.plcc"},
      "lhs": {"name": "program", "isTerminal": false, "altName": null, "isCapturing": false},
      "rhsSymbolList": [
        {"name": "NUM", "isTerminal": true, "isCapturing": false}
      ]
    }
  ]},
  "semantics": [...]
}
```

**Field name rule for capturing symbols:** if `altName` is non-null use `altName.lower()`, else use `name.lower()`. Non-capturing symbols get `field: null`.

---

## Task 1: Update `ll1.schema.json`

**Files:**
- Modify: `src/plcc/schemas/ll1.schema.json`

- [ ] **Step 1: Write the failing test (bats — run manually to confirm)**

  Current schema does not require `start_symbol`. After this task the schema will require it. Run the existing schema-validation test to confirm it currently passes (green baseline):

  ```bash
  bin/test/commands.bash -- tests/bats/commands/plcc-ll1.bats
  ```

  Expected: passes (stub output matches old schema).

- [ ] **Step 2: Update the schema**

  Replace the entire content of `src/plcc/schemas/ll1.schema.json` with:

  ```json
  {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "LL1Analysis",
    "description": "Output of plcc-ll1: LL(1) analysis of a grammar.",
    "type": "object",
    "required": ["is_ll1", "start_symbol", "first_sets", "follow_sets", "predict_sets", "parse_table", "conflicts", "left_recursion"],
    "properties": {
      "is_ll1":         { "type": "boolean" },
      "start_symbol":   { "type": "string" },
      "first_sets":     {
        "type": "object",
        "additionalProperties": { "type": "array", "items": { "type": "string" } }
      },
      "follow_sets":    {
        "type": "object",
        "additionalProperties": { "type": "array", "items": { "type": "string" } }
      },
      "predict_sets":   {
        "type": "object",
        "additionalProperties": {
          "type": "array",
          "items": { "type": "array", "items": { "type": "string" } }
        }
      },
      "parse_table":    {
        "type": "object",
        "additionalProperties": {
          "type": "object",
          "additionalProperties": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["symbol", "field"],
              "properties": {
                "symbol": { "type": "string" },
                "field":  { "type": ["string", "null"] }
              }
            }
          }
        }
      },
      "conflicts": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["nonterminal", "lookahead", "productions"],
          "properties": {
            "nonterminal": { "type": "string" },
            "lookahead":   { "type": "string" },
            "productions": { "type": "array" }
          }
        }
      },
      "left_recursion": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["cycle"],
          "properties": {
            "cycle": { "type": "array", "items": { "type": "string" } }
          }
        }
      }
    }
  }
  ```

- [ ] **Step 3: Run the commands test to see it fail**

  ```bash
  bin/test/commands.bash -- tests/bats/commands/plcc-ll1.bats
  ```

  Expected: the `plcc-ll1 produces schema-valid output` test FAILS because the stub output lacks `start_symbol`.
  This is correct — the schema is now the specification that drives the implementation.

- [ ] **Step 4: Commit**

  ```bash
  git add src/plcc/schemas/ll1.schema.json
  git commit -m "feat(ll1): add start_symbol to ll1.schema.json and tighten types"
  ```

---

## Task 2: Confirm `plcc-spec` LL(1) Separation

**Files:**
- Modify: `src/plcc/spec/plcc_spec_cli.py`

- [ ] **Step 1: Search for LL(1) call sites in plcc-spec**

  ```bash
  grep -rn "ll1\|FIRST\|FOLLOW\|predict\|parse_table\|left_recursion" \
      src/plcc/spec/plcc_spec_cli.py \
      src/plcc/spec/parseSpec.py
  ```

  Expected: no output (no LL(1) call sites found).

- [ ] **Step 2: Add separation comment to `plcc_spec_cli.py`**

  In `src/plcc/spec/plcc_spec_cli.py`, add a comment after the imports:

  ```python
  # No LL(1) analysis here; see plcc-ll1.
  ```

  Add it on the line immediately before `__doc__ = ...`.

- [ ] **Step 3: Run unit tests to confirm no regression**

  ```bash
  bin/test/units.bash
  ```

  Expected: all pass.

- [ ] **Step 4: Commit**

  ```bash
  git add src/plcc/spec/plcc_spec_cli.py
  git commit -m "chore(spec): confirm LL(1) separation with comment"
  ```

---

## Task 3: Add Verbose Support to `plcc-parser-list`

**Files:**
- Modify: `src/plcc/parser/list_cli.py`
- Modify: `tests/bats/commands/plcc-parser-list.bats`

- [ ] **Step 1: Write the failing bats tests**

  Add to the end of `tests/bats/commands/plcc-parser-list.bats`:

  ```bash
  @test "plcc-parser-list accepts --verbose" {
      run plcc-parser-list --verbose=1
      [ "$status" -eq 0 ]
  }

  @test "plcc-parser-list accepts --verbose-format" {
      run plcc-parser-list --verbose=1 --verbose-format=json
      [ "$status" -eq 0 ]
  }
  ```

- [ ] **Step 2: Run to confirm tests fail**

  ```bash
  bin/test/commands.bash -- tests/bats/commands/plcc-parser-list.bats
  ```

  Expected: the two new tests FAIL (`docopt` rejects unknown options).

- [ ] **Step 3: Update `list_cli.py`**

  Replace the entire content of `src/plcc/parser/list_cli.py` with:

  ```python
  import enum
  import os
  import re
  import sys

  from docopt import docopt

  from plcc.verbose import VerboseContext, VERBOSE_OPTIONS

  _PARSER_PATTERN = re.compile(r"^plcc-parser-(.+)$")

  __doc__ = """plcc-parser-list
      List installed parser plugins.

  Usage:
      plcc-parser-list [options]

  Options:
      -h --help   Show this message.
  """ + VERBOSE_OPTIONS


  class Events(enum.Enum):
      STARTED = "started"
      FINISHED = "finished"


  def main(argv=None):
      if argv is None:
          argv = sys.argv[1:]
      args = docopt(__doc__, argv)
      VerboseContext.from_args("plcc-parser-list", Events, args)
      for kind in sorted(find_parsers()):
          print(kind)


  def find_parsers():
      """Scan PATH for plcc-parser-* commands; return list of parser kinds."""
      parsers = []
      seen = set()
      for directory in _path_dirs():
          try:
              for entry in os.scandir(directory):
                  name = _extract_parser_kind(entry.name)
                  if name and name not in seen and _is_executable(entry):
                      parsers.append(name)
                      seen.add(name)
          except (PermissionError, FileNotFoundError):
              continue
      return parsers


  def _extract_parser_kind(command_name):
      m = _PARSER_PATTERN.match(command_name)
      if m:
          kind = m.group(1)
          if kind != "list":
              return kind
      return None


  def _path_dirs():
      return os.environ.get("PATH", "").split(os.pathsep)


  def _is_executable(entry):
      return entry.is_file() and os.access(entry.path, os.X_OK)
  ```

- [ ] **Step 4: Run to confirm tests pass**

  ```bash
  bin/test/commands.bash -- tests/bats/commands/plcc-parser-list.bats
  ```

  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add src/plcc/parser/list_cli.py tests/bats/commands/plcc-parser-list.bats
  git commit -m "feat(parser): add verbose support to plcc-parser-list"
  ```

---

## Task 4: Create `spec_json_decoder` Module

Converts a spec JSON dict into a `Grammar` (base class with string keys, compatible with all LL(1) algorithms) plus a `field_map` that records per-production field names.

**Files:**
- Create: `src/plcc/ll1/spec_json_decoder.py`
- Create: `src/plcc/ll1/spec_json_decoder_test.py`

- [ ] **Step 1: Write the failing tests**

  Create `src/plcc/ll1/spec_json_decoder_test.py`:

  ```python
  import pytest
  from plcc.ll1.spec_json_decoder import decode


  def _spec(rules):
      return {"lexical": {"ruleList": []}, "syntax": {"rules": rules}, "semantics": []}


  def _rule(lhs_name, rhs_syms):
      return {
          "line": {"string": "", "number": 0, "file": ""},
          "lhs": {"name": lhs_name, "isTerminal": False, "altName": None, "isCapturing": False},
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


  def test_empty_grammar():
      grammar, field_map = decode(_spec([]))
      assert grammar.getStartSymbol() is None
      assert field_map == {}


  def test_single_rule_noncapturing():
      grammar, field_map = decode(_spec([
          _rule("program", [_terminal("NUM")])
      ]))
      assert grammar.getStartSymbol() == "program"
      assert list(grammar.getForms("program")) == [("NUM",)]
      assert field_map == {("program", ("NUM",)): [None]}


  def test_epsilon_rule():
      grammar, field_map = decode(_spec([
          _rule("empty", [])
      ]))
      assert grammar.getStartSymbol() == "empty"
      assert list(grammar.getForms("empty")) == [()]
      assert field_map == {("empty", ()): []}


  def test_capturing_terminal_uses_name_lower():
      grammar, field_map = decode(_spec([
          _rule("E", [_terminal("NUM", capturing=True)])
      ]))
      assert field_map == {("E", ("NUM",)): ["num"]}


  def test_capturing_terminal_uses_alt_name():
      grammar, field_map = decode(_spec([
          _rule("E", [_terminal("NUM", capturing=True, alt_name="value")])
      ]))
      assert field_map == {("E", ("NUM",)): ["value"]}


  def test_capturing_nonterminal_uses_name_lower():
      grammar, field_map = decode(_spec([
          _rule("E", [_nonterminal("Term", capturing=True)])
      ]))
      assert field_map == {("E", ("Term",)): ["term"]}


  def test_multiple_symbols():
      grammar, field_map = decode(_spec([
          _rule("E", [_nonterminal("T", capturing=True), _terminal("PLUS"), _nonterminal("E", capturing=True, alt_name="r")])
      ]))
      assert field_map == {("E", ("T", "PLUS", "E")): ["t", None, "r"]}


  def test_start_symbol_is_first_rule_lhs():
      grammar, field_map = decode(_spec([
          _rule("first", [_terminal("A")]),
          _rule("second", [_terminal("B")]),
      ]))
      assert grammar.getStartSymbol() == "first"
  ```

- [ ] **Step 2: Run to confirm failure**

  ```bash
  bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py -v
  ```

  Expected: `ModuleNotFoundError: No module named 'plcc.ll1.spec_json_decoder'`.

- [ ] **Step 3: Create `spec_json_decoder.py`**

  Create `src/plcc/ll1/spec_json_decoder.py`:

  ```python
  from plcc.spec.syntax.validations.ll1.Grammar import Grammar


  def decode(spec_dict: dict) -> tuple:
      """
      Build a Grammar from a spec JSON dict.

      Returns (grammar, field_map) where:
        grammar   — base Grammar with string symbol keys, compatible with all
                    LL(1) algorithms (build_first_sets, build_follow_sets, etc.)
        field_map — dict[(nt_name, prod_tuple)] -> list[str|None]
                    Maps each production to its per-symbol field names.
                    None means the symbol is elided from the parse tree.
      """
      grammar = Grammar()
      field_map = {}
      for rule in spec_dict.get("syntax", {}).get("rules", []):
          nt = rule["lhs"]["name"]
          rhs = rule.get("rhsSymbolList", [])
          if not rhs:
              grammar.addRule(nt, [])
              field_map[(nt, ())] = []
          else:
              syms = [s["name"] for s in rhs]
              fields = [_field(s) for s in rhs]
              grammar.addRule(nt, syms)
              field_map[(nt, tuple(syms))] = fields
      return grammar, field_map


  def _field(sym: dict) -> str | None:
      """Return the field name for a symbol dict, or None if elided."""
      if not sym.get("isCapturing", False):
          return None
      alt = sym.get("altName")
      name = sym["name"]
      return (alt if alt else name).lower()
  ```

- [ ] **Step 4: Run to confirm tests pass**

  ```bash
  bin/test/units.bash src/plcc/ll1/spec_json_decoder_test.py -v
  ```

  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add src/plcc/ll1/spec_json_decoder.py src/plcc/ll1/spec_json_decoder_test.py
  git commit -m "feat(ll1): add spec_json_decoder — build Grammar from spec JSON"
  ```

---

## Task 5: Create `ll1_result_builder` Module

Runs the existing LL(1) algorithms on a Grammar and produces the `ll1.json` dict.

**Files:**
- Create: `src/plcc/ll1/ll1_result_builder.py`
- Create: `src/plcc/ll1/ll1_result_builder_test.py`

- [ ] **Step 1: Write the failing tests**

  Create `src/plcc/ll1/ll1_result_builder_test.py`:

  ```python
  from plcc.spec.syntax.validations.ll1.Grammar import Grammar
  from plcc.ll1.ll1_result_builder import build_ll1_result


  def _simple_grammar():
      """program → NUM (not capturing)"""
      g = Grammar()
      g.addRule("program", ["NUM"])
      fm = {("program", ("NUM",)): [None]}
      return g, fm


  def _epsilon_grammar():
      """rest →  (epsilon)"""
      g = Grammar()
      g.addRule("rest", [])
      fm = {("rest", ()): []}
      return g, fm


  def _conflict_grammar():
      """A → X | X Y  (two productions with same first token → conflict)"""
      g = Grammar()
      g.addRule("A", ["X"])
      g.addRule("A", ["X", "Y"])
      fm = {("A", ("X",)): [None], ("A", ("X", "Y")): [None, None]}
      return g, fm


  def _left_recursive_grammar():
      """A → A B | C  (direct left recursion)"""
      g = Grammar()
      g.addRule("A", ["A", "B"])
      g.addRule("A", ["C"])
      fm = {("A", ("A", "B")): [None, None], ("A", ("C",)): [None]}
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
      assert "$" in result["follow_sets"]["program"]


  def test_predict_sets_correct():
      g, fm = _simple_grammar()
      result = build_ll1_result(g, fm)
      assert result["predict_sets"]["program"] == [["NUM"]]


  def test_parse_table_entry_correct():
      g, fm = _simple_grammar()
      result = build_ll1_result(g, fm)
      assert result["parse_table"]["program"]["NUM"] == [{"symbol": "NUM", "field": None}]


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
      # epsilon rule: predict set contains $; parse table entry under $ is []
      assert result["parse_table"]["rest"]["$"] == []


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
      # Conflicting cell A/X must be absent from parse_table
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
      # Direct self-loop: ["A", "A"] — first and last element are the same
      assert cycle[0] == cycle[-1]
      assert "A" in cycle


  def test_capturing_symbol_field_in_parse_table():
      g = Grammar()
      g.addRule("E", ["NUM"])
      fm = {("E", ("NUM",)): ["num"]}  # NUM is capturing with field "num"
      result = build_ll1_result(g, fm)
      entry = result["parse_table"]["E"]["NUM"]
      assert entry == [{"symbol": "NUM", "field": "num"}]
  ```

- [ ] **Step 2: Run to confirm failure**

  ```bash
  bin/test/units.bash src/plcc/ll1/ll1_result_builder_test.py -v
  ```

  Expected: `ModuleNotFoundError: No module named 'plcc.ll1.ll1_result_builder'`.

- [ ] **Step 3: Create `ll1_result_builder.py`**

  Create `src/plcc/ll1/ll1_result_builder.py`:

  ```python
  from plcc.spec.syntax.validations.ll1.Grammar import Grammar
  from plcc.spec.syntax.validations.ll1.build_first_sets import build_first_sets
  from plcc.spec.syntax.validations.ll1.build_follow_sets import build_follow_sets
  from plcc.spec.syntax.validations.ll1.build_parsing_table import build_parsing_table
  from plcc.spec.syntax.validations.ll1.check_parsing_table_for_ll1 import check_parsing_table_for_ll1
  from plcc.spec.syntax.validations.ll1.check_left_recursion import check_left_recursion


  def build_ll1_result(grammar: Grammar, field_map: dict) -> dict:
      """
      Run LL(1) analysis on grammar and return a ll1.json-compatible dict.

      grammar   — base Grammar with string symbol keys
      field_map — dict[(nt_name, prod_tuple)] -> list[str|None]
      """
      eps = grammar.getEpsilon()
      eof = grammar.getEof()

      lr_cycles = check_left_recursion(grammar)
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

      nts = sorted(grammar.getNonterminalSet())

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
          if (nt, t) in bad_cells:
              continue
          prod = next(iter(table.getCell(nt, t)))
          lookahead = tok(t)
          parse_table.setdefault(nt, {})[lookahead] = _prod_entry(nt, prod, field_map, eps)

      conflicts = []
      for (nt, t) in sorted(bad_cells):
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

      return {
          "is_ll1": not (conflicts or left_recursion),
          "start_symbol": grammar.getStartSymbol(),
          "first_sets": first_sets,
          "follow_sets": follow_sets,
          "predict_sets": predict_sets,
          "parse_table": parse_table,
          "conflicts": conflicts,
          "left_recursion": left_recursion,
      }


  def _prod_entry(nt: str, prod: tuple, field_map: dict, eps) -> list:
      """Build the [{symbol, field}, ...] list for one production."""
      fields = field_map.get((nt, prod), [None] * len(prod))
      return [
          {"symbol": sym, "field": fld}
          for sym, fld in zip(prod, fields)
          if sym is not eps
      ]
  ```

- [ ] **Step 4: Run to confirm tests pass**

  ```bash
  bin/test/units.bash src/plcc/ll1/ll1_result_builder_test.py -v
  ```

  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add src/plcc/ll1/ll1_result_builder.py src/plcc/ll1/ll1_result_builder_test.py
  git commit -m "feat(ll1): add ll1_result_builder — compute ll1.json dict from Grammar"
  ```

---

## Task 6: Implement `plcc-ll1` CLI

Replace the stub with the real implementation. Remove the `[SPEC_JSON]` positional argument (stdin only). Add all verbose events through level 2. Update all files that reference the file-path argument.

**Files:**
- Modify: `src/plcc/ll1/ll1_cli.py`
- Modify: `src/plcc/ll1/ll1_cli_test.py`
- Modify: `tests/bats/commands/plcc-ll1.bats`
- Modify: `tests/bats/commands/plcc-parser-table.bats`
- Modify: `tests/bats/integration/ll1-tree.bats`
- Modify: `tests/bats/e2e/error-propagation.bats`

- [ ] **Step 1: Write failing unit tests in `ll1_cli_test.py`**

  Replace the full content of `src/plcc/ll1/ll1_cli_test.py` with:

  ```python
  import io
  import json
  import pytest

  from plcc.ll1.ll1_cli import main as run_main


  def _trivial_spec():
      return {
          "lexical": {"ruleList": []},
          "syntax": {"rules": [
              {
                  "line": {"string": "<program> ::= NUM", "number": 3, "file": ""},
                  "lhs": {"name": "program", "isTerminal": False, "altName": None, "isCapturing": False},
                  "rhsSymbolList": [{"name": "NUM", "isTerminal": True, "isCapturing": False}],
              }
          ]},
          "semantics": [],
      }


  def _empty_spec():
      return {"lexical": {"ruleList": []}, "syntax": {"rules": []}, "semantics": []}


  def test_exits_zero_and_emits_json(capsys, monkeypatch):
      monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
      run_main([])
      out, _ = capsys.readouterr()
      result = json.loads(out)
      assert isinstance(result, dict)


  def test_emits_start_symbol(capsys, monkeypatch):
      monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
      run_main([])
      out, _ = capsys.readouterr()
      assert json.loads(out)["start_symbol"] == "program"


  def test_is_ll1_true_for_trivial_grammar(capsys, monkeypatch):
      monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
      run_main([])
      out, _ = capsys.readouterr()
      assert json.loads(out)["is_ll1"] is True


  def test_first_sets_populated(capsys, monkeypatch):
      monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
      run_main([])
      out, _ = capsys.readouterr()
      result = json.loads(out)
      assert result["first_sets"]["program"] == ["NUM"]


  def test_empty_spec_is_ll1_true(capsys, monkeypatch):
      monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_empty_spec())))
      run_main([])
      out, _ = capsys.readouterr()
      result = json.loads(out)
      assert result["is_ll1"] is True
      assert result["start_symbol"] is None


  def test_malformed_json_exits_nonzero(monkeypatch):
      monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
      with pytest.raises(SystemExit) as exc:
          run_main([])
      assert exc.value.code != 0


  def test_verbose_started_emitted(capsys, monkeypatch):
      monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
      run_main(["--verbose=1", "--verbose-format=json"])
      _, err = capsys.readouterr()
      events = [json.loads(line) for line in err.strip().splitlines() if line]
      assert any(e["event"] == "started" for e in events)


  def test_verbose_finished_emitted(capsys, monkeypatch):
      monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
      run_main(["--verbose=1", "--verbose-format=json"])
      _, err = capsys.readouterr()
      events = [json.loads(line) for line in err.strip().splitlines() if line]
      assert any(e["event"] == "finished" for e in events)


  def test_verbose_level2_first_set_events(capsys, monkeypatch):
      monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_trivial_spec())))
      run_main(["--verbose=2", "--verbose-format=json"])
      _, err = capsys.readouterr()
      events = [json.loads(line) for line in err.strip().splitlines() if line]
      assert any(e["event"] == "first-set" for e in events)
  ```

- [ ] **Step 2: Run to confirm failures**

  ```bash
  bin/test/units.bash src/plcc/ll1/ll1_cli_test.py -v
  ```

  Expected: most tests fail (stub has wrong interface and output).

- [ ] **Step 3: Replace `ll1_cli.py`**

  Replace the full content of `src/plcc/ll1/ll1_cli.py` with:

  ```python
  import enum
  import json
  import sys

  from docopt import docopt

  from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
  from .spec_json_decoder import decode
  from .ll1_result_builder import build_ll1_result

  __doc__ = """plcc-ll1
      Perform LL(1) analysis on a grammar spec.

  Usage:
      plcc-ll1 [options]

  Options:
      -h --help       Show this message.
  """ + VERBOSE_OPTIONS


  class Events(enum.Enum):
      STARTED = "started"
      FINISHED = "finished"
      FIRST_SET = "first-set"
      FOLLOW_SET = "follow-set"
      PREDICT_SET = "predict-set"
      CONFLICT = "conflict"
      LEFT_RECURSION = "left-recursion"
      FIXPOINT_STEP = "fixpoint-step"  # reserved; not emitted in this implementation


  def main(argv=None):
      if argv is None:
          argv = sys.argv[1:]
      args = docopt(__doc__, argv)
      verbose = VerboseContext.from_args("plcc-ll1", Events, args)
      verbose.emit(Events.STARTED)
      try:
          spec = json.load(sys.stdin)
      except (json.JSONDecodeError, ValueError) as e:
          verbose.emit_error({}, f"malformed spec JSON: {e}")
          sys.exit(1)
      grammar, field_map = decode(spec)
      result = build_ll1_result(grammar, field_map)
      for nt, terminals in result["first_sets"].items():
          verbose.emit(Events.FIRST_SET, level=2, nonterminal=nt, first=terminals)
      for nt, terminals in result["follow_sets"].items():
          verbose.emit(Events.FOLLOW_SET, level=2, nonterminal=nt, follow=terminals)
      for nt, predicts in result["predict_sets"].items():
          verbose.emit(Events.PREDICT_SET, level=2, nonterminal=nt, predict=predicts)
      for conflict in result["conflicts"]:
          verbose.emit(Events.CONFLICT, level=2, **conflict)
      for lr in result["left_recursion"]:
          verbose.emit(Events.LEFT_RECURSION, level=2, **lr)
      n_c = len(result["conflicts"])
      n_lr = len(result["left_recursion"])
      summary = (
          "is_ll1: true"
          if result["is_ll1"]
          else f"{n_c} conflicts, {n_lr} left-recursion cycles"
      )
      verbose.emit(Events.FINISHED, message=summary)
      print(json.dumps(result, indent=2))
  ```

- [ ] **Step 4: Run unit tests to confirm they pass**

  ```bash
  bin/test/units.bash src/plcc/ll1/ll1_cli_test.py -v
  ```

  Expected: all pass.

- [ ] **Step 5: Update `tests/bats/commands/plcc-ll1.bats`**

  Replace the full content of `tests/bats/commands/plcc-ll1.bats` with:

  ```bash
  #!/usr/bin/env bats

  bats_require_minimum_version 1.5.0

  setup() {
      FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
      SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/ll1.schema.json"
      SPEC_JSON="$(mktemp)"
      plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
  }

  teardown() { rm -f "${SPEC_JSON}"; }

  @test "plcc-ll1 is on PATH" { command -v plcc-ll1; }

  @test "plcc-ll1 --help exits 0" {
      run plcc-ll1 --help
      [ "$status" -eq 0 ]
  }

  @test "plcc-ll1 produces schema-valid output" {
      run bash -c "plcc-ll1 < '${SPEC_JSON}'"
      [ "$status" -eq 0 ]
      echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
  }

  @test "plcc-ll1 reads from stdin via pipe" {
      run bash -c "cat '${SPEC_JSON}' | plcc-ll1"
      [ "$status" -eq 0 ]
      echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
  }

  @test "plcc-ll1 accepts --verbose without error" {
      run bash -c "plcc-ll1 --verbose=1 < '${SPEC_JSON}'"
      [ "$status" -eq 0 ]
  }

  @test "plcc-ll1 accepts --verbose-format without error" {
      run bash -c "plcc-ll1 --verbose=1 --verbose-format=json < '${SPEC_JSON}'"
      [ "$status" -eq 0 ]
  }

  @test "plcc-ll1: is_ll1 is true for empty spec" {
      run bash -c "echo '{\"lexical\":{\"ruleList\":[]},\"syntax\":{\"rules\":[]},\"semantics\":[]}' | plcc-ll1"
      [ "$status" -eq 0 ]
      echo "$output" | grep -q '"is_ll1"'
  }

  @test "plcc-ll1 emits start_symbol for trivial grammar" {
      run bash -c "plcc-ll1 < '${SPEC_JSON}'"
      [ "$status" -eq 0 ]
      echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['start_symbol'] == 'program', r['start_symbol']"
  }

  @test "plcc-ll1 populates first_sets for trivial grammar" {
      run bash -c "plcc-ll1 < '${SPEC_JSON}'"
      [ "$status" -eq 0 ]
      echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['first_sets']['program'] == ['NUM'], r['first_sets']"
  }
  ```

- [ ] **Step 6: Update `tests/bats/commands/plcc-parser-table.bats` setup**

  In `tests/bats/commands/plcc-parser-table.bats`, change line:
  ```bash
  plcc-ll1 "${SPEC_JSON}" > "${LL1_JSON}"
  ```
  to:
  ```bash
  plcc-ll1 < "${SPEC_JSON}" > "${LL1_JSON}"
  ```

- [ ] **Step 7: Update `tests/bats/integration/ll1-tree.bats` setup**

  In `tests/bats/integration/ll1-tree.bats`, change line:
  ```bash
  plcc-ll1 "${SPEC_JSON}" > "${LL1_JSON}"
  ```
  to:
  ```bash
  plcc-ll1 < "${SPEC_JSON}" > "${LL1_JSON}"
  ```

- [ ] **Step 8: Update `tests/bats/e2e/error-propagation.bats` setup**

  In `tests/bats/e2e/error-propagation.bats`, change line:
  ```bash
  plcc-ll1 "${SPEC_JSON}" > "${LL1_JSON}"
  ```
  to:
  ```bash
  plcc-ll1 < "${SPEC_JSON}" > "${LL1_JSON}"
  ```

- [ ] **Step 9: Run all command and integration tests**

  ```bash
  bin/test/commands.bash -- tests/bats/commands/plcc-ll1.bats
  bin/test/commands.bash -- tests/bats/commands/plcc-parser-table.bats
  bin/test/integration.bash -- tests/bats/integration/ll1-tree.bats
  bin/test/integration.bash -- tests/bats/integration/spec-ll1.bats
  bin/test/e2e.bash -- tests/bats/e2e/error-propagation.bats
  ```

  Expected: all pass.

- [ ] **Step 10: Commit**

  ```bash
  git add \
      src/plcc/ll1/ll1_cli.py \
      src/plcc/ll1/ll1_cli_test.py \
      tests/bats/commands/plcc-ll1.bats \
      tests/bats/commands/plcc-parser-table.bats \
      tests/bats/integration/ll1-tree.bats \
      tests/bats/e2e/error-propagation.bats
  git commit -m "feat(ll1): implement plcc-ll1 with real LL(1) analysis; stdin only"
  ```

---

## Task 7: Update `plcc-make`

`plcc-make` currently calls `plcc-ll1 <path>` (file argument). It must switch to stdin redirection. It also has a bug in how it reports `left_recursion` cycles (iterates over dict keys instead of the `cycle` list).

**Files:**
- Modify: `src/plcc/cmd/make.py`

- [ ] **Step 1: Confirm the current call site**

  In `src/plcc/cmd/make.py` around line 61:
  ```python
  _run_or_die(['plcc-ll1', spec_json] + child_flags, stdout_file=ll1_json, verbose=verbose)
  ```

  And around line 122:
  ```python
  for cycle in ll1.get("left_recursion", []):
      print(
          f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}",
  ```

  The `cycle` here is a `{"cycle": [...]}` dict — `' -> '.join(cycle)` would join the dict's keys ("cycle"), not the actual nonterminal names.

- [ ] **Step 2: Write a unit test for `_report_ll1_failure`**

  Add to `src/plcc/cmd/make.py`'s test file (create `make_test.py` next to make.py if it doesn't exist):

  Actually, `_report_ll1_failure` writes to stderr directly. Test it by capturing stderr output. Add a test file `src/plcc/cmd/make_test.py`:

  ```python
  import io
  import sys
  import pytest
  from plcc.cmd.make import _report_ll1_failure
  from plcc.verbose import VerboseContext

  class FakeEvents:
      pass

  def test_report_left_recursion_cycle(capsys):
      ll1 = {
          "conflicts": [],
          "left_recursion": [{"cycle": ["A", "B", "A"]}],
      }
      _report_ll1_failure(ll1, "build/ll1.json", None)
      _, err = capsys.readouterr()
      assert "A -> B -> A" in err

  def test_report_conflict(capsys):
      ll1 = {
          "conflicts": [{"nonterminal": "E", "lookahead": "PLUS", "productions": []}],
          "left_recursion": [],
      }
      _report_ll1_failure(ll1, "build/ll1.json", None)
      _, err = capsys.readouterr()
      assert "E" in err
      assert "PLUS" in err
  ```

- [ ] **Step 3: Run to confirm failure**

  ```bash
  bin/test/units.bash src/plcc/cmd/make_test.py -v
  ```

  Expected: `test_report_left_recursion_cycle` FAILS (`"A -> B -> A"` not found because `' -> '.join({"cycle": [...]})` = `"cycle"` not the nonterminals).

- [ ] **Step 4: Fix `make.py`**

  In `src/plcc/cmd/make.py`, change the `plcc-ll1` call (line ~61):

  ```python
  # Before:
  _run_or_die(['plcc-ll1', spec_json] + child_flags, stdout_file=ll1_json, verbose=verbose)
  # After:
  _run_or_die(['plcc-ll1'] + child_flags, stdin_file=spec_json, stdout_file=ll1_json, verbose=verbose)
  ```

  And fix `_report_ll1_failure` (lines ~109–126):

  ```python
  def _report_ll1_failure(ll1, path, verbose):
      print(
          f"plcc-make: error: grammar is not LL(1); see {path}",
          file=sys.stderr,
      )
      for conflict in ll1.get("conflicts", []):
          print(
              f"plcc-make: error: conflict at "
              f"{conflict.get('nonterminal', '?')} on "
              f"{conflict.get('lookahead', '?')}: "
              f"{conflict.get('productions', [])}",
              file=sys.stderr,
          )
      for entry in ll1.get("left_recursion", []):
          cycle = entry.get("cycle", [])
          print(
              f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}",
              file=sys.stderr,
          )
  ```

- [ ] **Step 5: Run tests to confirm pass**

  ```bash
  bin/test/units.bash src/plcc/cmd/make_test.py -v
  ```

  Expected: all pass.

- [ ] **Step 6: Run e2e tests to confirm plcc-make still works**

  ```bash
  bin/test/e2e.bash
  ```

  Expected: all pass.

- [ ] **Step 7: Commit**

  ```bash
  git add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
  git commit -m "fix(make): pass spec JSON to plcc-ll1 via stdin; fix left-recursion cycle reporting"
  ```

---

## Task 8: Run Full Test Suite

Verify all tiers are green before declaring Plan 1 complete.

- [ ] **Step 1: Run all functional tests**

  ```bash
  bin/test/functional.bash
  ```

  Expected: all tiers (units + commands + integration + e2e) pass.

  If any test fails, investigate and fix before proceeding. Common issues:
  - A bats test still uses `plcc-ll1 "${SPEC_JSON}"` with a file path → fix to `plcc-ll1 < "${SPEC_JSON}"`
  - A unit test imports from the old stub interface → update to new stdin-only interface
  - A schema check fails → verify the `start_symbol` field is present in all `plcc-ll1` outputs

- [ ] **Step 2: Run packaging test**

  ```bash
  bin/test/packaging.bash
  ```

  Expected: wheel builds, all entry points resolve, smoke test passes.

- [ ] **Step 3: Tag completion**

  ```bash
  git log --oneline -8
  ```

  Confirm the last 8 commits correspond to the plan tasks above. Plan 1 is complete.

---

## Self-Review

### Spec coverage check

| Spec section | Covered by |
|---|---|
| §3.1 stdin only, no file arg | Task 6 — `ll1_cli.py` docstring, removed `[SPEC_JSON]` |
| §3.1 exit 0 for non-LL(1) | Task 5 — `build_ll1_result` always returns; Task 6 — no sys.exit on analysis results |
| §3.1 exit nonzero for malformed stdin | Task 6 — `except json.JSONDecodeError` |
| §3.2 wire up existing code | Tasks 4, 5 — `spec_json_decoder`, `ll1_result_builder` |
| §3.3 level 0 silent | Task 6 — VerboseContext.emit defaults to level=1 |
| §3.3 level 1 started/finished | Task 6 — emitted |
| §3.3 level 2 per-nonterminal events | Task 6 — first-set, follow-set, predict-set, conflict, left-recursion |
| §3.3 level 3 fixpoint-step | **Deferred** — requires instrumenting `build_first_sets`/`build_follow_sets` without rewriting them; reserved enum member `FIXPOINT_STEP` added |
| §4 ll1.json schema — start_symbol | Task 1 (schema), Task 5 (implementation) |
| §4 ll1.json all fields | Task 5 — all fields present |
| §7 plcc-spec no LL(1) sites | Task 2 |
| §8 plcc-parser-list verbose | Task 3 |
| plcc-make stdin | Task 7 |

### Placeholder scan

No TBD, TODO, or "fill in later" phrases in any task.

### Type consistency

- `decode()` returns `(Grammar, dict)` — used identically in Task 5 tests and Task 6 `ll1_cli.py`
- `build_ll1_result(grammar, field_map)` signature used consistently in all callers
- `field_map` keys are `(str, tuple[str])` throughout
