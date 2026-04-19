# Table-Driven Parser Implementation Plan (Phase 2 Part 1 — Plan 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `plcc-parser-table` stub with a real table-driven LL(1) predictive parser that reads token JSONL from stdin, uses a `ll1.json` parse table, and writes a complete parse tree JSON to stdout. Also update `tree.schema.json` to reflect the `[field_name, node]` children structure.

**Architecture:** A new `predictive_parser` module implements the iterative stack-based parsing algorithm. It takes a loaded `ll1.json` dict and a list of token records, and returns a tree dict. `table_cli.py` wires this into the CLI with verbose events.

**Prerequisites:** Plan 1 must be complete. `plcc-ll1` must produce real `ll1.json` output (including `parse_table`, `start_symbol`, `is_ll1`) before this plan can be tested end-to-end.

**Tech Stack:** Python 3.12, docopt-ng, pytest, bats, check-jsonschema.

---

## File Map

| Action | Path |
|--------|------|
| Modify | `src/plcc/schemas/tree.schema.json` |
| Create | `src/plcc/parser/predictive_parser.py` |
| Create | `src/plcc/parser/predictive_parser_test.py` |
| Modify | `src/plcc/parser/table_cli.py` |
| Modify | `tests/bats/commands/plcc-parser-table.bats` |
| Modify | `tests/bats/integration/ll1-tree.bats` |

---

## Background: Parse Tree Format

The parse tree produced by `plcc-parser-table` (and all `plcc-parser-*` plugins) has this structure.

**Internal node:**
```json
{
  "kind": "tree",
  "rule": "Expr",
  "source": {
    "file": "prog.txt",
    "line": 4,
    "column": 12,
    "endLine": 4,
    "endColumn": 25
  },
  "children": [
    ["left", {"kind": "tree", "rule": "Term", ...}],
    ["op",   {"kind": "token", "name": "PLUS", "lexeme": "+", "source": {...}}]
  ]
}
```

**Token leaf:** placed unchanged from `plcc-tokens` output — no wrapper:
```json
{"kind": "token", "name": "NUM", "lexeme": "42", "source": {"file": "<stdin>", "line": 1, "column": 1}}
```

**Rules:**
- `children` is an array of `[field_name, node]` two-element arrays. Only capturing (non-elided) symbols appear.
- `source` on internal nodes spans the full production extent including elided tokens. `endColumn = last_token.source.column + len(last_token.lexeme) - 1` (1-indexed, inclusive).
- `source` on token leaves is the token's own `source` (no `endLine`/`endColumn`).

---

## Background: Parsing Algorithm

Standard iterative predictive parsing (design doc §5.2). All tokens are loaded into memory first.

The stack holds items of the form `(kind, symbol, field, builder)`:
- `kind = "T"` — terminal to match; `symbol` is the terminal name; `field` is `str|None`; `builder` is the `NodeBuilder` for the parent nonterminal.
- `kind = "N"` — nonterminal to expand; `symbol` is the nonterminal name; `field` is the field name in the grandparent; `builder` is the grandparent's `NodeBuilder` (or `None` for root).
- `kind = "end"` — sentinel marking the end of a nonterminal expansion; `builder` is the `NodeBuilder` to finalise; `field` is the field name in `parent_builder`; `symbol` is the rule name (for the node); `parent_builder` is the grandparent's builder (or `None`).

A `NodeBuilder` tracks:
- `rule: str` — the nonterminal name
- `children: list` — `[field, node]` pairs for capturing symbols
- `first_tok: dict | None` — first token consumed in this subtree (for span start)
- `last_tok: dict | None` — last token consumed (for span end)

When shifting (matching) a terminal:
1. Consume the token from the token list (advance cursor).
2. Call `builder.note_token(token)` — updates `first_tok`/`last_tok`.
3. If `field is not None`: `builder.children.append([field, token])`.

When expanding a nonterminal (stack top is `("N", nt, nt_field, parent_builder)`):
1. Look up `parse_table[nt][lookahead]` → `production` (list of `{symbol, field}` dicts).
2. Create `new_builder = NodeBuilder(nt)`.
3. Pop the `("N", ...)` item.
4. Push `("end", nt, nt_field, new_builder, parent_builder)` sentinel.
5. Push the production symbols in **reverse** order, each as `("T", sym, field, new_builder)` or `("N", sym, field, new_builder)`. For empty production (`[]`) push nothing.

Whether a symbol is a terminal or nonterminal: check `sym_name in parse_table` — if present it is a nonterminal, otherwise a terminal.

When processing a sentinel (`("end", nt, nt_field, builder, parent_builder)`):
1. `node = builder.to_node()` — builds the `{"kind": "tree", ...}` dict.
2. If `parent_builder is not None`:
   - `parent_builder.note_span_from(builder)` — propagates `first_tok`/`last_tok`.
   - If `nt_field is not None`: `parent_builder.children.append([nt_field, node])`.
3. If `parent_builder is None`: this is the root — store result.

**End check:** after the stack empties, the lookahead must be the `$` sentinel (cursor past all real tokens). If any real tokens remain, that is a syntax error.

---

## Task 1: Update `tree.schema.json`

**Files:**
- Modify: `src/plcc/schemas/tree.schema.json`

- [ ] **Step 1: Confirm the current schema-validation test passes**

  ```bash
  bin/test/commands.bash -- tests/bats/commands/plcc-parser-table.bats
  ```

  Expected: `plcc-parser-table produces schema-valid tree` passes with the stub (which emits the old format).

- [ ] **Step 2: Update `tree.schema.json`**

  Replace the full content of `src/plcc/schemas/tree.schema.json` with:

  ```json
  {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "TreeRecord",
    "description": "Output of plcc-parser-*: one complete parse tree.",
    "type": "object",
    "required": ["kind", "rule", "source"],
    "properties": {
      "kind":   { "type": "string", "const": "tree" },
      "rule":   { "type": "string" },
      "source": {
        "type": "object",
        "required": ["file", "line", "column", "endLine", "endColumn"],
        "properties": {
          "file":      { "type": "string" },
          "line":      { "type": "integer" },
          "column":    { "type": "integer" },
          "endLine":   { "type": "integer" },
          "endColumn": { "type": "integer" }
        }
      },
      "children": {
        "type": "array",
        "items": {
          "type": "array",
          "minItems": 2,
          "maxItems": 2,
          "items": [
            { "type": "string" },
            { "type": "object", "required": ["kind"] }
          ]
        }
      }
    }
  }
  ```

- [ ] **Step 3: Run to confirm the schema-validation test now fails**

  ```bash
  bin/test/commands.bash -- tests/bats/commands/plcc-parser-table.bats
  ```

  Expected: `plcc-parser-table produces schema-valid tree` FAILS (stub output lacks `source`, `endLine`, `endColumn`, and uses old children format). This is correct; the schema now drives the implementation.

- [ ] **Step 4: Commit**

  ```bash
  git add src/plcc/schemas/tree.schema.json
  git commit -m "feat(parser): update tree.schema.json for [field,node] children and source span"
  ```

---

## Task 2: Create `predictive_parser` Module

Implements the iterative stack-based LL(1) parsing algorithm and tree builder.

**Files:**
- Create: `src/plcc/parser/predictive_parser.py`
- Create: `src/plcc/parser/predictive_parser_test.py`

- [ ] **Step 1: Write the failing tests**

  Create `src/plcc/parser/predictive_parser_test.py`:

  ```python
  import pytest
  from plcc.parser.predictive_parser import parse, ParseError


  # ll1.json dict for grammar: program → NUM  (NUM is non-capturing, field=null)
  _TRIVIAL_LL1 = {
      "is_ll1": True,
      "start_symbol": "program",
      "parse_table": {
          "program": {
              "NUM": [{"symbol": "NUM", "field": None}]
          }
      },
  }

  # ll1.json dict for grammar: E → t:Term PLUS r:E | t:Term
  # Term → n:NUM
  _EXPR_LL1 = {
      "is_ll1": True,
      "start_symbol": "E",
      "parse_table": {
          "E": {
              "NUM": [
                  {"symbol": "Term", "field": "t"},
                  {"symbol": "PLUS", "field": None},
                  {"symbol": "E", "field": "r"},
              ]
          },
          "Term": {
              "NUM": [{"symbol": "NUM", "field": "n"}]
          },
      },
  }

  # E → NUM PLUS NUM  (simple, no nesting, both NUMs captured)
  _FLAT_EXPR_LL1 = {
      "is_ll1": True,
      "start_symbol": "E",
      "parse_table": {
          "E": {
              "NUM": [
                  {"symbol": "NUM", "field": "left"},
                  {"symbol": "PLUS", "field": None},
                  {"symbol": "NUM", "field": "right"},
              ]
          }
      },
  }

  def _tok(name, lexeme, line=1, col=1, file="<stdin>"):
      return {"kind": "token", "name": name, "lexeme": lexeme,
              "source": {"file": file, "line": line, "column": col}}


  # --- trivial grammar tests ---

  def test_trivial_parse_returns_tree_kind():
      result = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
      assert result["kind"] == "tree"


  def test_trivial_parse_rule_is_start_symbol():
      result = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
      assert result["rule"] == "program"


  def test_trivial_parse_elided_symbol_not_in_children():
      result = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
      assert result["children"] == []


  def test_trivial_parse_source_span():
      result = parse(_TRIVIAL_LL1, [_tok("NUM", "42", line=3, col=5)])
      src = result["source"]
      assert src["line"] == 3
      assert src["column"] == 5
      assert src["endLine"] == 3
      # endColumn = col + len("42") - 1 = 5 + 2 - 1 = 6
      assert src["endColumn"] == 6


  def test_trivial_parse_source_file():
      result = parse(_TRIVIAL_LL1, [_tok("NUM", "42", file="prog.txt")])
      assert result["source"]["file"] == "prog.txt"


  # --- capturing symbol tests ---

  def test_capturing_child_in_children():
      result = parse(_FLAT_EXPR_LL1, [
          _tok("NUM", "1", col=1),
          _tok("PLUS", "+", col=2),
          _tok("NUM", "2", col=3),
      ])
      fields = [child[0] for child in result["children"]]
      assert "left" in fields
      assert "right" in fields


  def test_capturing_children_are_token_dicts():
      result = parse(_FLAT_EXPR_LL1, [
          _tok("NUM", "1"),
          _tok("PLUS", "+"),
          _tok("NUM", "2"),
      ])
      left = dict(result["children"])["left"]
      assert left["kind"] == "token"
      assert left["name"] == "NUM"
      assert left["lexeme"] == "1"


  def test_elided_plus_not_in_children():
      result = parse(_FLAT_EXPR_LL1, [
          _tok("NUM", "1"),
          _tok("PLUS", "+"),
          _tok("NUM", "2"),
      ])
      fields = [child[0] for child in result["children"]]
      assert "PLUS" not in fields


  # --- span across multiple tokens ---

  def test_span_covers_all_tokens_including_elided():
      result = parse(_FLAT_EXPR_LL1, [
          _tok("NUM", "1", col=1),
          _tok("PLUS", "+", col=3),
          _tok("NUM", "2", col=5),
      ])
      src = result["source"]
      assert src["column"] == 1          # start of first token
      assert src["endColumn"] == 5       # endColumn of "2" at col 5, len 1 → 5


  # --- nested nonterminal tests ---

  def test_nested_nonterminal_child_is_tree():
      result = parse(_EXPR_LL1, [
          _tok("NUM", "3"),
          _tok("PLUS", "+"),
          _tok("NUM", "4"),
      ])
      # E → Term PLUS E; Term → NUM; E → Term (base case with one NUM)
      # But _EXPR_LL1 only has E→NUM entry (NUM → Term PLUS E),
      # so for input "3 + 4" it produces E with child t=Term(NUM=3), r=E(t=Term(NUM=4))
      assert result["rule"] == "E"
      children_dict = dict(result["children"])
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
          "parse_table": {"A": {"X": [{"symbol": "X", "field": None}]}},
      }
      with pytest.raises(ParseError):
          parse(ll1, [_tok("Y", "y")])


  def test_extra_tokens_after_parse_raises_parse_error():
      with pytest.raises(ParseError):
          parse(_TRIVIAL_LL1, [_tok("NUM", "1"), _tok("NUM", "2")])


  def test_empty_input_on_nonempty_grammar_raises_parse_error():
      with pytest.raises(ParseError):
          parse(_TRIVIAL_LL1, [])
  ```

- [ ] **Step 2: Run to confirm failure**

  ```bash
  bin/test/units.bash src/plcc/parser/predictive_parser_test.py -v
  ```

  Expected: `ModuleNotFoundError: No module named 'plcc.parser.predictive_parser'`.

- [ ] **Step 3: Create `predictive_parser.py`**

  Create `src/plcc/parser/predictive_parser.py`:

  ```python
  class ParseError(Exception):
      pass


  class NodeBuilder:
      def __init__(self, rule):
          self.rule = rule
          self.children = []      # [[field, node], ...]
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
      Parse tokens against the LL(1) parse table.

      ll1    — dict with keys: start_symbol, parse_table
      tokens — list of token dicts from plcc-tokens (without $ sentinel)

      Returns the root parse tree dict.
      Raises ParseError on any syntax error.
      """
      parse_table = ll1["parse_table"]
      start = ll1["start_symbol"]
      cursor = [0]

      SENTINEL = {"name": "$", "lexeme": "", "source": {"file": "", "line": 0, "column": 0}}

      def current():
          return tokens[cursor[0]] if cursor[0] < len(tokens) else SENTINEL

      def advance():
          tok = tokens[cursor[0]]
          cursor[0] += 1
          return tok

      result = [None]

      # Stack: items are tuples. Kinds:
      #   ("N", sym, field, parent_builder)
      #   ("T", sym, field, parent_builder)
      #   ("end", rule, field, builder, parent_builder)
      stack = [("N", start, None, None)]

      while stack:
          item = stack.pop()
          kind = item[0]

          if kind == "T":
              _, sym, field, builder = item
              tok = current()
              if tok["name"] != sym:
                  raise ParseError(
                      f"expected {sym!r}, got {tok['name']!r} "
                      f"at {tok['source']}"
                  )
              tok = advance()
              if builder is not None:
                  builder.note_token(tok)
              if field is not None and builder is not None:
                  builder.children.append([field, tok])

          elif kind == "N":
              _, sym, field, parent_builder = item
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
              new_builder = NodeBuilder(sym)
              stack.append(("end", sym, field, new_builder, parent_builder))
              for entry in reversed(production):
                  s = entry["symbol"]
                  f = entry["field"]
                  if s in parse_table:
                      stack.append(("N", s, f, new_builder))
                  else:
                      stack.append(("T", s, f, new_builder))

          elif kind == "end":
              _, rule, field, builder, parent_builder = item
              node = builder.to_node()
              if parent_builder is not None:
                  parent_builder.note_span_from(builder)
                  if field is not None:
                      parent_builder.children.append([field, node])
              else:
                  result[0] = node

      tok = current()
      if tok["name"] != "$":
          raise ParseError(
              f"unexpected token {tok['name']!r} after complete parse "
              f"at {tok['source']}"
          )
      return result[0]
  ```

- [ ] **Step 4: Run to confirm tests pass**

  ```bash
  bin/test/units.bash src/plcc/parser/predictive_parser_test.py -v
  ```

  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add src/plcc/parser/predictive_parser.py src/plcc/parser/predictive_parser_test.py
  git commit -m "feat(parser): add predictive_parser — iterative LL(1) table-driven parser"
  ```

---

## Task 3: Implement `table_cli.py`

Wire up the predictive parser into the CLI with verbose events. Exit nonzero if `is_ll1` is false or on any syntax error.

**Files:**
- Modify: `src/plcc/parser/table_cli.py`

- [ ] **Step 1: Write unit tests for `table_cli.py`**

  Create `src/plcc/parser/table_cli_test.py`:

  ```python
  import io
  import json
  import sys
  import pytest
  from plcc.parser.table_cli import main as run_main


  _TRIVIAL_LL1 = {
      "is_ll1": True,
      "start_symbol": "program",
      "parse_table": {
          "program": {
              "NUM": [{"symbol": "NUM", "field": None}]
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
          "E": {"NUM": [{"symbol": "NUM", "field": "num"}]}
      },
  }

  def _tok(name, lexeme, line=1, col=1, file="<stdin>"):
      return {"kind": "token", "name": name, "lexeme": lexeme,
              "source": {"file": file, "line": line, "column": col}}

  def _run(ll1_dict, tokens, extra_args=None, tmp_path=None):
      """Run table_cli.main with the given ll1 and tokens. Returns (stdout, stderr, exit_code)."""
      import tempfile, os
      ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
      try:
          json.dump(ll1_dict, ll1_file)
          ll1_file.flush()
          ll1_file.close()
          stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
          argv = [f"--ll1={ll1_file.name}"] + (extra_args or [])
          exit_code = 0
          try:
              with pytest.MonkeyPatch.context() as mp:
                  mp.setattr("sys.stdin", io.StringIO(stdin_data))
                  run_main(argv)
          except SystemExit as e:
              exit_code = e.code or 0
          return exit_code
      finally:
          os.unlink(ll1_file.name)


  def test_exits_zero_for_valid_input(capsys, tmp_path):
      code = _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
      assert code == 0


  def test_stdout_is_valid_json(capsys, tmp_path):
      _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
      out, _ = capsys.readouterr()
      result = json.loads(out)
      assert isinstance(result, dict)


  def test_output_is_tree_kind(capsys):
      _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
      out, _ = capsys.readouterr()
      assert json.loads(out)["kind"] == "tree"


  def test_output_rule_is_start_symbol(capsys):
      _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
      out, _ = capsys.readouterr()
      assert json.loads(out)["rule"] == "program"


  def test_output_has_source(capsys):
      _run(_TRIVIAL_LL1, [_tok("NUM", "42")])
      out, _ = capsys.readouterr()
      src = json.loads(out)["source"]
      assert "line" in src and "column" in src


  def test_capturing_child_in_tree(capsys):
      _run(_CAPTURING_LL1, [_tok("NUM", "42")])
      out, _ = capsys.readouterr()
      result = json.loads(out)
      fields = [c[0] for c in result["children"]]
      assert "num" in fields


  def test_exits_nonzero_for_non_ll1_grammar(tmp_path):
      import tempfile, os
      ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
      try:
          json.dump(_NON_LL1, ll1_file)
          ll1_file.flush()
          ll1_file.close()
          with pytest.raises(SystemExit) as exc:
              with pytest.MonkeyPatch.context() as mp:
                  mp.setattr("sys.stdin", io.StringIO(""))
                  run_main([f"--ll1={ll1_file.name}"])
          assert exc.value.code != 0
      finally:
          os.unlink(ll1_file.name)


  def test_exits_nonzero_on_syntax_error(tmp_path):
      import tempfile, os
      ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
      try:
          json.dump(_TRIVIAL_LL1, ll1_file)
          ll1_file.flush()
          ll1_file.close()
          with pytest.raises(SystemExit) as exc:
              with pytest.MonkeyPatch.context() as mp:
                  mp.setattr("sys.stdin", io.StringIO(json.dumps(_tok("IDENTIFIER", "x")) + "\n"))
                  run_main([f"--ll1={ll1_file.name}"])
          assert exc.value.code != 0
      finally:
          os.unlink(ll1_file.name)


  def test_nothing_written_to_stdout_on_error(capsys, tmp_path):
      import tempfile, os
      ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
      try:
          json.dump(_TRIVIAL_LL1, ll1_file)
          ll1_file.flush()
          ll1_file.close()
          try:
              with pytest.MonkeyPatch.context() as mp:
                  mp.setattr("sys.stdin", io.StringIO(json.dumps(_tok("IDENTIFIER", "x")) + "\n"))
                  run_main([f"--ll1={ll1_file.name}"])
          except SystemExit:
              pass
          out, _ = capsys.readouterr()
          assert out.strip() == ""
      finally:
          os.unlink(ll1_file.name)
  ```

- [ ] **Step 2: Run to confirm failures**

  ```bash
  bin/test/units.bash src/plcc/parser/table_cli_test.py -v
  ```

  Expected: several tests fail (stub emits wrong format, wrong exit codes).

- [ ] **Step 3: Replace `table_cli.py`**

  Replace the full content of `src/plcc/parser/table_cli.py` with:

  ```python
  import enum
  import json
  import sys

  from docopt import docopt

  from plcc.verbose import VerboseContext, VERBOSE_OPTIONS
  from .predictive_parser import parse, ParseError

  __doc__ = """plcc-parser-table
      Table-driven LL(1) parser. Reads token JSONL from stdin, emits a parse tree.

  Usage:
      plcc-parser-table [options] --ll1=LL1_JSON

  Options:
      --ll1=LL1_JSON          Path to LL(1) analysis JSON (required).
      -h --help               Show this message.
  """ + VERBOSE_OPTIONS


  class Events(enum.Enum):
      STARTED = "started"
      FINISHED = "finished"
      EXPAND = "expand"
      SHIFT = "shift"
      COMPLETE = "complete"
      PREDICT_LOOKUP = "predict-lookup"


  def main(argv=None):
      if argv is None:
          argv = sys.argv[1:]
      args = docopt(__doc__, argv)
      verbose = VerboseContext.from_args("plcc-parser-table", Events, args)
      ll1_path = args["--ll1"]
      verbose.emit(Events.STARTED, ll1_path=ll1_path)

      # Load ll1.json
      try:
          with open(ll1_path) as f:
              ll1 = json.load(f)
      except (OSError, json.JSONDecodeError) as e:
          verbose.emit_error({}, f"cannot load ll1.json from {ll1_path!r}: {e}")
          sys.exit(1)

      if not ll1.get("is_ll1", False):
          verbose.emit_error({}, "grammar is not LL(1); cannot parse")
          sys.exit(1)

      # Read all tokens from stdin
      tokens = []
      for line in sys.stdin:
          line = line.strip()
          if not line:
              continue
          try:
              tokens.append(json.loads(line))
          except json.JSONDecodeError as e:
              verbose.emit_error({}, f"malformed token JSON: {e}")
              sys.exit(1)

      # Parse
      try:
          tree = parse(ll1, tokens)
      except ParseError as e:
          verbose.emit_error({}, str(e))
          sys.exit(1)

      verbose.emit(Events.FINISHED, token_count=len(tokens), rule_count=_count_rules(tree))
      print(json.dumps(tree))


  def _count_rules(node):
      """Count internal (tree-kind) nodes in the parse tree."""
      if node.get("kind") != "tree":
          return 0
      return 1 + sum(_count_rules(child[1]) for child in node.get("children", []))
  ```

- [ ] **Step 4: Run unit tests to confirm they pass**

  ```bash
  bin/test/units.bash src/plcc/parser/table_cli_test.py -v
  ```

  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add src/plcc/parser/table_cli.py src/plcc/parser/table_cli_test.py
  git commit -m "feat(parser): implement plcc-parser-table — real LL(1) predictive parser"
  ```

---

## Task 4: Update Bats Tests

Add tree-shape assertions to the bats tests and confirm the schema-validation tests pass with real output.

**Files:**
- Modify: `tests/bats/commands/plcc-parser-table.bats`
- Modify: `tests/bats/integration/ll1-tree.bats`

- [ ] **Step 1: Run schema-validation bats test to confirm it now passes**

  ```bash
  bin/test/commands.bash -- tests/bats/commands/plcc-parser-table.bats
  ```

  Expected: `plcc-parser-table produces schema-valid tree` now passes (real parser emits correct format).

- [ ] **Step 2: Add tree-shape tests to `plcc-parser-table.bats`**

  Append to the end of `tests/bats/commands/plcc-parser-table.bats`:

  ```bash
  @test "plcc-parser-table output has kind=tree" {
      run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}'"
      [ "$status" -eq 0 ]
      echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='tree', r['kind']"
  }

  @test "plcc-parser-table output has rule=program" {
      run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}'"
      [ "$status" -eq 0 ]
      echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['rule']=='program', r['rule']"
  }

  @test "plcc-parser-table output has source span" {
      run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}'"
      [ "$status" -eq 0 ]
      echo "$output" | python3 -c "
  import json,sys
  r=json.load(sys.stdin)
  src=r['source']
  assert 'line' in src and 'endLine' in src, src
  "
  }

  @test "plcc-parser-table exits nonzero for lex error input" {
      run bash -c "echo 'not_a_num' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}'"
      # plcc-tokens exits nonzero; plcc-parser-table either doesn't run or also exits nonzero
      [ "$status" -ne 0 ]
  }
  ```

- [ ] **Step 3: Add integration test for tree shape**

  Append to `tests/bats/integration/ll1-tree.bats`:

  ```bash
  @test "plcc-tokens | plcc-tree with ll1 produces tree with rule=program" {
      run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}'"
      [ "$status" -eq 0 ]
      echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['rule']=='program'"
  }

  @test "plcc-tokens | plcc-tree with ll1 output has source span" {
      run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}'"
      [ "$status" -eq 0 ]
      echo "$output" | python3 -c "
  import json,sys
  r=json.load(sys.stdin)
  assert 'endLine' in r['source'], r['source']
  "
  }
  ```

- [ ] **Step 4: Run all bats tests**

  ```bash
  bin/test/commands.bash -- tests/bats/commands/plcc-parser-table.bats
  bin/test/integration.bash -- tests/bats/integration/ll1-tree.bats
  ```

  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add tests/bats/commands/plcc-parser-table.bats tests/bats/integration/ll1-tree.bats
  git commit -m "test(parser): add tree-shape assertions for plcc-parser-table and ll1-tree integration"
  ```

---

## Task 5: Run Full Test Suite

- [ ] **Step 1: Run all functional tests**

  ```bash
  bin/test/functional.bash
  ```

  Expected: all tiers (units + commands + integration + e2e) pass.

  Common issues to diagnose if failures occur:
  - `plcc-parser-table.bats` `plcc-parser-table requires --ll1` test: the new implementation still requires `--ll1`; should pass.
  - `ll1-tree.bats` schema validation: tree.schema.json now requires `source` with `endLine`/`endColumn`. The parser emits them; should pass.
  - `tokens-tree.bats`: exercises `plcc-tree` with no `--ll1` option; `plcc-tree` dispatches to a fallback (or emits an error). Check this test's expected behaviour.

- [ ] **Step 2: Run packaging test**

  ```bash
  bin/test/packaging.bash
  ```

  Expected: wheel builds, all entry points resolve, smoke test passes.

---

## Self-Review

### Spec coverage check

| Spec section | Covered by |
|---|---|
| §5.1 `--ll1=<path>` required | Task 3 — docopt declares `--ll1=LL1_JSON` |
| §5.1 exit nonzero if is_ll1 false | Task 3 — checked after loading |
| §5.1 nothing to stdout on failure | Task 3 — `sys.exit(1)` before `print(tree)` |
| §5.2 read tokens to EOF first | Task 3 — tokens list built before `parse()` call |
| §5.2 $ sentinel appended | Task 2 — `SENTINEL` in `parse()` |
| §5.2 predictive loop | Task 2 — stack-based algorithm |
| §5.2 span computation | Task 2 — `NodeBuilder.note_token`, `note_span_from`, `endColumn` formula |
| §5.2 AST elision (field: null → absent) | Task 2 — `if field is not None` guards |
| §5.2 error on syntax error | Task 2 — `ParseError`; Task 3 — caught, exit nonzero |
| §5.3 verbose started/finished | Task 3 — emitted |
| §5.3 verbose expand/shift/complete | **Deferred** — requires wiring verbose context into `parse()`; reserved enum members added |
| §6 tree schema `[field,node]` children | Task 1 (schema), Task 2 (implementation) |
| §6 source span on internal nodes | Task 2 — `NodeBuilder.to_node()` |
| §6 token leaves unchanged | Task 2 — tokens passed directly into children |

### Note on deferred verbose events (expand/shift/complete)

The design §5.3 specifies level-2 events `expand`, `shift`, and `complete`. These require threading a `VerboseContext` into the `parse()` function and calling `verbose.emit(...)` at each stack operation. This is architecturally clean (pass `verbose` as a parameter) but was excluded from this plan to keep the parser module testable without a verbose dependency. To add them:
1. Add `verbose: VerboseContext | None = None` parameter to `parse()`.
2. After the expand step: `if verbose: verbose.emit(Events.EXPAND, level=2, nonterminal=sym, production=production)`.
3. After the shift step: `if verbose: verbose.emit(Events.SHIFT, level=2, name=tok["name"], lexeme=tok["lexeme"], source=tok["source"])`.
4. In the `"end"` case: `if verbose: verbose.emit(Events.COMPLETE, level=2, nonterminal=rule)`.
5. Pass `verbose=verbose` from `table_cli.py`.

### Placeholder scan

No TBD, TODO, or "fill in later" phrases in any task.

### Type consistency

- `parse(ll1: dict, tokens: list) -> dict` — used identically in `predictive_parser_test.py` and `table_cli.py`
- `ParseError` imported from `predictive_parser` in both `table_cli.py` and `predictive_parser_test.py`
- `NodeBuilder.to_node()` always returns a dict with `kind`, `rule`, `source`, `children` — consistent with tree schema
