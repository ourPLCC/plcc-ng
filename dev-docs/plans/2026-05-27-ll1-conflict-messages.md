# LL(1) Conflict Error Messages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace raw-data LL(1) conflict output with human-readable messages that classify the conflict type and give concrete remediation tips.

**Architecture:** `ll1_result_builder.py` gains a `conflict_type` field (`"first_first"` or `"first_follow"`) on each conflict entry in `ll1.json`. A new `format_conflict_message.py` module turns one conflict dict into a multi-line human-readable string. `make.py`'s `_report_ll1_failure` calls the formatter per conflict instead of printing raw data.

**Tech Stack:** Python 3, pytest (via `bin/test/units.bash`), existing Grammar/Rule types from `plcc.spec.syntax.validations.ll1`.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `src/plcc/ll1/ll1_result_builder.py` | Add `conflict_type` classification to each conflict entry |
| Modify | `src/plcc/ll1/ll1_result_builder_test.py` | Tests for `conflict_type` field |
| Create | `src/plcc/ll1/format_conflict_message.py` | Public `format_conflict_message(conflict)` + private helpers |
| Create | `src/plcc/ll1/format_conflict_message_test.py` | Unit tests for the formatter |
| Modify | `src/plcc/cmd/make.py` | Call formatter in `_report_ll1_failure` |
| Modify | `src/plcc/cmd/make_test.py` | Update existing conflict test with realistic data |

---

## Task 1: Add `conflict_type` to conflict entries

**Files:**
- Modify: `src/plcc/ll1/ll1_result_builder.py` (lines 67–82, the conflicts loop)
- Modify: `src/plcc/ll1/ll1_result_builder_test.py`

- [ ] **Step 1: Add the FIRST/FOLLOW test grammar helper and two failing tests**

  Append to `src/plcc/ll1/ll1_result_builder_test.py`:

  ```python
  def _first_follow_conflict_grammar():
      """
      prog → A X
      A → X
      A → (empty)

      FOLLOW(A) = {X} because prog expands to A X.
      On lookahead X: both (A → X) and (A → empty) apply → FIRST/FOLLOW conflict.
      """
      g = Grammar()
      g.addRule("prog", ["A", "X"])
      g.addRule("A", ["X"])
      g.addRule("A", [])
      fm = {
          ("prog", ("A", "X")): Rule(alt=None, fields=[None, None]),
          ("A", ("X",)): Rule(alt=None, fields=[None]),
          ("A", ()): Rule(alt=None, fields=[]),
      }
      return g, fm


  def test_conflict_type_is_first_first():
      g, fm = _conflict_grammar()
      result = build_ll1_result(g, fm)
      c = result["conflicts"][0]
      assert c["conflict_type"] == "first_first"


  def test_conflict_type_is_first_follow():
      g, fm = _first_follow_conflict_grammar()
      result = build_ll1_result(g, fm)
      conflict_on_A = next(c for c in result["conflicts"] if c["nonterminal"] == "A")
      assert conflict_on_A["conflict_type"] == "first_follow"
  ```

- [ ] **Step 2: Run tests to confirm they fail**

  ```
  bin/test/units.bash src/plcc/ll1/ll1_result_builder_test.py
  ```

  Expected: two failures — `KeyError: 'conflict_type'` (or `AssertionError`).

- [ ] **Step 3: Add `conflict_type` classification in `ll1_result_builder.py`**

  In `src/plcc/ll1/ll1_result_builder.py`, replace the body of the conflicts loop (lines 73–82) with:

  ```python
  for (nt, t) in sorted(bad_cells, key=cell_sort_key):
      if nt in internal_nts:
          continue
      prods = table.getCell(nt, t)
      lookahead = tok(t)
      conflict_productions = [
          _prod_entry(nt, p, productions, eps)
          for p in sorted(prods, key=str)
      ]
      has_empty = any(len(cp["production"]) == 0 for cp in conflict_productions)
      conflict_type = "first_follow" if has_empty else "first_first"
      conflicts.append({
          "nonterminal": nt,
          "lookahead": lookahead,
          "conflict_type": conflict_type,
          "productions": conflict_productions,
      })
  ```

- [ ] **Step 4: Run tests to confirm they pass**

  ```
  bin/test/units.bash src/plcc/ll1/ll1_result_builder_test.py
  ```

  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add src/plcc/ll1/ll1_result_builder.py src/plcc/ll1/ll1_result_builder_test.py
  git commit -m "feat(ll1): add conflict_type field to ll1.json conflict entries"
  ```

---

## Task 2: Create `format_conflict_message.py` — skeleton and production rendering

**Files:**
- Create: `src/plcc/ll1/format_conflict_message.py`
- Create: `src/plcc/ll1/format_conflict_message_test.py`

- [ ] **Step 1: Write failing tests for production rendering and the message header**

  Create `src/plcc/ll1/format_conflict_message_test.py`:

  ```python
  import pytest
  from plcc.ll1.format_conflict_message import format_conflict_message, _render_production

  # Shared test fixtures
  FIRST_FIRST_CONFLICT = {
      "nonterminal": "expr",
      "lookahead": "ID",
      "conflict_type": "first_first",
      "productions": [
          {"alt": None, "production": [
              {"symbol": "ID", "field": None},
              {"symbol": "PLUS", "field": None},
              {"symbol": "expr", "field": None},
          ]},
          {"alt": None, "production": [
              {"symbol": "ID", "field": None},
              {"symbol": "MINUS", "field": None},
              {"symbol": "expr", "field": None},
          ]},
      ],
  }

  FIRST_FOLLOW_CONFLICT = {
      "nonterminal": "elsePart",
      "lookahead": "ELSE",
      "conflict_type": "first_follow",
      "productions": [
          {"alt": None, "production": [
              {"symbol": "ELSE", "field": None},
              {"symbol": "stmt", "field": None},
          ]},
          {"alt": None, "production": []},
      ],
  }


  def test_render_production_nonempty():
      entry = {"alt": None, "production": [
          {"symbol": "ELSE", "field": None},
          {"symbol": "stmt", "field": None},
      ]}
      assert _render_production("elsePart", entry) == "<elsePart> ::= ELSE <stmt>"


  def test_render_production_empty():
      entry = {"alt": None, "production": []}
      assert _render_production("elsePart", entry) == "<elsePart> ::=    (empty)"


  def test_render_production_terminal_no_angle_brackets():
      entry = {"alt": None, "production": [{"symbol": "NUM", "field": None}]}
      result = _render_production("expr", entry)
      assert "NUM" in result
      assert "<NUM>" not in result


  def test_render_production_nonterminal_gets_angle_brackets():
      entry = {"alt": None, "production": [{"symbol": "term", "field": None}]}
      result = _render_production("expr", entry)
      assert "<term>" in result


  def test_render_production_field_is_ignored():
      entry = {"alt": "Add", "production": [
          {"symbol": "ID", "field": "name"},
      ]}
      assert _render_production("expr", entry) == "<expr> ::= ID"


  def test_format_includes_header_line():
      msg = format_conflict_message(FIRST_FOLLOW_CONFLICT)
      assert "LL(1) conflict: <elsePart> on lookahead ELSE" in msg


  def test_format_lists_all_productions():
      msg = format_conflict_message(FIRST_FOLLOW_CONFLICT)
      assert "<elsePart> ::= ELSE <stmt>" in msg
      assert "<elsePart> ::=    (empty)" in msg
  ```

- [ ] **Step 2: Run tests to confirm they fail**

  ```
  bin/test/units.bash src/plcc/ll1/format_conflict_message_test.py
  ```

  Expected: `ModuleNotFoundError` — file does not exist yet.

- [ ] **Step 3: Implement the skeleton with production rendering**

  Create `src/plcc/ll1/format_conflict_message.py`:

  ```python
  import re

  _TERMINAL_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')


  def format_conflict_message(conflict: dict) -> str:
      nt = conflict["nonterminal"]
      lookahead = conflict["lookahead"]
      conflict_type = conflict.get("conflict_type", "first_first")
      productions = conflict["productions"]

      lines = [
          f"LL(1) conflict: {_nt(nt)} on lookahead {lookahead}",
          "",
          "  All of these productions apply:",
      ]
      for prod in productions:
          lines.append(f"    {_render_production(nt, prod)}")
      lines.append("")

      if conflict_type == "first_follow":
          lines.extend(_first_follow_lines(nt, lookahead))
      else:
          lines.extend(_first_first_lines(nt, lookahead, productions))

      return "\n".join(lines)


  def _nt(name: str) -> str:
      return f"<{name}>"


  def _render_symbol(sym: str) -> str:
      if _TERMINAL_RE.match(sym):
          return sym
      return _nt(sym)


  def _render_production(nt: str, production_entry: dict) -> str:
      symbols = production_entry["production"]
      lhs = _nt(nt)
      if not symbols:
          return f"{lhs} ::=    (empty)"
      rhs = " ".join(_render_symbol(s["symbol"]) for s in symbols)
      return f"{lhs} ::= {rhs}"


  def _first_follow_lines(nt: str, lookahead: str) -> list[str]:
      # Filled in Task 3
      return []


  def _first_first_lines(nt: str, lookahead: str, productions: list[dict]) -> list[str]:
      # Filled in Tasks 4 and 5
      return []
  ```

- [ ] **Step 4: Run tests to confirm they pass**

  ```
  bin/test/units.bash src/plcc/ll1/format_conflict_message_test.py
  ```

  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add src/plcc/ll1/format_conflict_message.py src/plcc/ll1/format_conflict_message_test.py
  git commit -m "feat(ll1): add format_conflict_message module with production rendering"
  ```

---

## Task 3: FIRST/FOLLOW message body

**Files:**
- Modify: `src/plcc/ll1/format_conflict_message.py`
- Modify: `src/plcc/ll1/format_conflict_message_test.py`

- [ ] **Step 1: Add failing tests for the FIRST/FOLLOW body**

  Append to `src/plcc/ll1/format_conflict_message_test.py`:

  ```python
  def test_first_follow_identifies_conflict_type():
      msg = format_conflict_message(FIRST_FOLLOW_CONFLICT)
      assert "FIRST/FOLLOW" in msg


  def test_first_follow_names_the_lookahead():
      msg = format_conflict_message(FIRST_FOLLOW_CONFLICT)
      # The explanation mentions the lookahead and the nonterminal
      assert "ELSE" in msg
      assert "FOLLOW set of <elsePart>" in msg


  def test_first_follow_includes_tip_to_look_at_context():
      msg = format_conflict_message(FIRST_FOLLOW_CONFLICT)
      assert "look at the rule(s) that use <elsePart>" in msg
  ```

- [ ] **Step 2: Run tests to confirm they fail**

  ```
  bin/test/units.bash src/plcc/ll1/format_conflict_message_test.py
  ```

  Expected: three new failures — the assertions about "FIRST/FOLLOW", "FOLLOW set of", and "look at the rule(s)" all fail because `_first_follow_lines` returns `[]`.

- [ ] **Step 3: Implement `_first_follow_lines`**

  In `src/plcc/ll1/format_conflict_message.py`, replace the `_first_follow_lines` stub with:

  ```python
  def _first_follow_lines(nt: str, lookahead: str) -> list[str]:
      return [
          f"  This is a FIRST/FOLLOW conflict: {lookahead} can start the non-empty production(s)",
          f"  above, but also appears in the FOLLOW set of {_nt(nt)}, making the empty",
          f"  production ambiguous here.",
          "",
          f"  Tip: look at the rule(s) that use {_nt(nt)} — one of them places",
          f"  {lookahead} in a position that follows {_nt(nt)}, creating the ambiguity.",
          f"  This often means the grammar is genuinely ambiguous (e.g., the",
          f"  dangling-else problem) and must be restructured.",
      ]
  ```

- [ ] **Step 4: Run tests to confirm they pass**

  ```
  bin/test/units.bash src/plcc/ll1/format_conflict_message_test.py
  ```

  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add src/plcc/ll1/format_conflict_message.py src/plcc/ll1/format_conflict_message_test.py
  git commit -m "feat(ll1): implement FIRST/FOLLOW conflict message body"
  ```

---

## Task 4: Longest-common-prefix helper

**Files:**
- Modify: `src/plcc/ll1/format_conflict_message.py`
- Modify: `src/plcc/ll1/format_conflict_message_test.py`

- [ ] **Step 1: Add failing tests for `_longest_common_prefix`**

  Append to `src/plcc/ll1/format_conflict_message_test.py`:

  ```python
  from plcc.ll1.format_conflict_message import _longest_common_prefix


  def test_lcp_single_shared_token():
      p1 = [{"symbol": "ID", "field": None}, {"symbol": "PLUS", "field": None}]
      p2 = [{"symbol": "ID", "field": None}, {"symbol": "MINUS", "field": None}]
      lcp = _longest_common_prefix([p1, p2])
      assert [s["symbol"] for s in lcp] == ["ID"]


  def test_lcp_multiple_shared_tokens():
      p1 = [{"symbol": "ID", "field": None}, {"symbol": "DOT", "field": None}, {"symbol": "ID", "field": None}]
      p2 = [{"symbol": "ID", "field": None}, {"symbol": "DOT", "field": None}, {"symbol": "NUM", "field": None}]
      lcp = _longest_common_prefix([p1, p2])
      assert [s["symbol"] for s in lcp] == ["ID", "DOT"]


  def test_lcp_with_three_productions():
      p1 = [{"symbol": "ID", "field": None}, {"symbol": "PLUS", "field": None}]
      p2 = [{"symbol": "ID", "field": None}, {"symbol": "MINUS", "field": None}]
      p3 = [{"symbol": "ID", "field": None}, {"symbol": "TIMES", "field": None}]
      lcp = _longest_common_prefix([p1, p2, p3])
      assert [s["symbol"] for s in lcp] == ["ID"]


  def test_lcp_empty_input():
      assert _longest_common_prefix([]) == []
  ```

- [ ] **Step 2: Run tests to confirm they fail**

  ```
  bin/test/units.bash src/plcc/ll1/format_conflict_message_test.py
  ```

  Expected: four failures — `ImportError` or `NameError` because `_longest_common_prefix` is not yet importable.

- [ ] **Step 3: Implement `_longest_common_prefix`**

  In `src/plcc/ll1/format_conflict_message.py`, add this function (place it before `_first_first_lines`):

  ```python
  def _longest_common_prefix(productions: list[list[dict]]) -> list[dict]:
      if not productions:
          return []
      shortest = min(len(p) for p in productions)
      prefix = []
      for i in range(shortest):
          sym = productions[0][i]["symbol"]
          if all(p[i]["symbol"] == sym for p in productions):
              prefix.append(productions[0][i])
          else:
              break
      return prefix
  ```

- [ ] **Step 4: Run tests to confirm they pass**

  ```
  bin/test/units.bash src/plcc/ll1/format_conflict_message_test.py
  ```

  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add src/plcc/ll1/format_conflict_message.py src/plcc/ll1/format_conflict_message_test.py
  git commit -m "feat(ll1): add _longest_common_prefix helper for left-factoring suggestion"
  ```

---

## Task 5: FIRST/FIRST message body with left-factoring suggestion

**Files:**
- Modify: `src/plcc/ll1/format_conflict_message.py`
- Modify: `src/plcc/ll1/format_conflict_message_test.py`

- [ ] **Step 1: Add failing tests for the FIRST/FIRST body**

  Append to `src/plcc/ll1/format_conflict_message_test.py`:

  ```python
  def test_first_first_identifies_conflict_type():
      msg = format_conflict_message(FIRST_FIRST_CONFLICT)
      assert "FIRST/FIRST" in msg


  def test_first_first_names_the_lookahead():
      msg = format_conflict_message(FIRST_FIRST_CONFLICT)
      assert "ID" in msg
      assert "parser cannot choose" in msg


  def test_first_first_includes_left_factoring_tip():
      msg = format_conflict_message(FIRST_FIRST_CONFLICT)
      assert "left-factor" in msg


  def test_first_first_shows_tail_nonterminal():
      msg = format_conflict_message(FIRST_FIRST_CONFLICT)
      # tail is <exprTail> derived from nonterminal "expr"
      assert "<exprTail>" in msg


  def test_first_first_shows_factored_lhs_rule():
      msg = format_conflict_message(FIRST_FIRST_CONFLICT)
      # The common prefix is ID; factored rule is <expr> ::= ID <exprTail>
      assert "<expr> ::= ID <exprTail>" in msg


  def test_first_first_shows_factored_tail_rules():
      msg = format_conflict_message(FIRST_FIRST_CONFLICT)
      assert "<exprTail> ::= PLUS <expr>" in msg
      assert "<exprTail> ::= MINUS <expr>" in msg
  ```

- [ ] **Step 2: Run tests to confirm they fail**

  ```
  bin/test/units.bash src/plcc/ll1/format_conflict_message_test.py
  ```

  Expected: six new failures — all assertions about FIRST/FIRST content fail because `_first_first_lines` returns `[]`.

- [ ] **Step 3: Implement `_first_first_lines`**

  In `src/plcc/ll1/format_conflict_message.py`, replace the `_first_first_lines` stub with:

  ```python
  def _first_first_lines(nt: str, lookahead: str, productions: list[dict]) -> list[str]:
      non_empty = [p["production"] for p in productions if p["production"]]
      lcp = _longest_common_prefix(non_empty)
      tail_nt = nt + "Tail"

      lines = [
          f"  This is a FIRST/FIRST conflict: all productions start with {lookahead}, so",
          f"  the parser cannot choose between them.",
          "",
          f"  Tip: left-factor the common prefix:",
      ]

      lcp_str = " ".join(_render_symbol(s["symbol"]) for s in lcp)
      lines.append(f"    {_nt(nt)} ::= {lcp_str} {_nt(tail_nt)}")
      for prod_syms in non_empty:
          remainder = prod_syms[len(lcp):]
          if remainder:
              rhs = " ".join(_render_symbol(s["symbol"]) for s in remainder)
              lines.append(f"    {_nt(tail_nt)} ::= {rhs}")
          else:
              lines.append(f"    {_nt(tail_nt)} ::=    (empty)")

      return lines
  ```

- [ ] **Step 4: Run tests to confirm they pass**

  ```
  bin/test/units.bash src/plcc/ll1/format_conflict_message_test.py
  ```

  Expected: all tests pass.

- [ ] **Step 5: Run the full unit suite to confirm nothing is broken**

  ```
  bin/test/units.bash
  ```

  Expected: all tests pass.

- [ ] **Step 6: Commit**

  ```bash
  git add src/plcc/ll1/format_conflict_message.py src/plcc/ll1/format_conflict_message_test.py
  git commit -m "feat(ll1): implement FIRST/FIRST message body with left-factoring suggestion"
  ```

---

## Task 6: Wire up formatter in `make.py`

**Files:**
- Modify: `src/plcc/cmd/make.py`
- Modify: `src/plcc/cmd/make_test.py`

- [ ] **Step 1: Update the existing conflict test in `make_test.py`**

  In `src/plcc/cmd/make_test.py`, replace `test_report_ll1_failure_prints_error_and_conflicts`:

  ```python
  def test_report_ll1_failure_prints_error_and_conflicts(capsys):
      ll1 = {
          "is_ll1": False,
          "conflicts": [
              {
                  "nonterminal": "expr",
                  "lookahead": "ID",
                  "conflict_type": "first_first",
                  "productions": [
                      {"alt": None, "production": [
                          {"symbol": "ID", "field": None},
                          {"symbol": "PLUS", "field": None},
                      ]},
                      {"alt": None, "production": [
                          {"symbol": "ID", "field": None},
                          {"symbol": "MINUS", "field": None},
                      ]},
                  ],
              }
          ],
          "left_recursion": [],
      }
      _report_ll1_failure(ll1, "build/ll1.json")
      _, err = capsys.readouterr()
      assert "plcc-make: error:" in err
      assert "build/ll1.json" in err
      assert "LL(1) conflict: <expr> on lookahead ID" in err
      assert "FIRST/FIRST" in err
  ```

- [ ] **Step 2: Run tests to confirm the test fails**

  ```
  bin/test/units.bash src/plcc/cmd/make_test.py
  ```

  Expected: `test_report_ll1_failure_prints_error_and_conflicts` fails because `_report_ll1_failure` still prints raw data, not the formatted message.

- [ ] **Step 3: Update `_report_ll1_failure` in `make.py`**

  In `src/plcc/cmd/make.py`, add the import at the top of the file alongside the other imports:

  ```python
  from plcc.ll1.format_conflict_message import format_conflict_message
  ```

  Then replace the `_report_ll1_failure` function body:

  ```python
  def _report_ll1_failure(ll1, path):
      print(f"plcc-make: error: grammar is not LL(1); see {path}", file=sys.stderr)
      for conflict in ll1.get("conflicts", []):
          print(format_conflict_message(conflict), file=sys.stderr)
      for entry in ll1.get("left_recursion", []):
          cycle = entry.get("cycle", [])
          print(f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}", file=sys.stderr)
  ```

- [ ] **Step 4: Run tests to confirm they pass**

  ```
  bin/test/units.bash src/plcc/cmd/make_test.py
  ```

  Expected: all tests pass.

- [ ] **Step 5: Run the full unit suite**

  ```
  bin/test/units.bash
  ```

  Expected: all tests pass.

- [ ] **Step 6: Run the functional test suite**

  ```
  bin/test/functional.bash
  ```

  Expected: all tiers pass.

- [ ] **Step 7: Commit**

  ```bash
  git add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
  git commit -m "feat(make): use format_conflict_message for human-readable LL(1) conflict output"
  ```
