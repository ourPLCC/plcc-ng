# plcc-trees Error Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `plcc-parse` work like `plcc-scan` — errors and trees are a uniform JSONL stream, with skip-and-retry error recovery and an explicit `$` EOF sentinel.

**Architecture:** `plcc-tokens` gains a `$` sentinel token at EOF; `plcc-parser-table` runs a skip-and-retry loop emitting trees and errors inline; `plcc-parse` iterates records uniformly; `SourceRunner` gains an explicit `SubmitOn` enum replacing the implicit feed-return-value contract; `plcc-tree` is renamed `plcc-trees`.

**Tech Stack:** Python, pytest, bats, docopt, subprocess JSONL pipeline.

**Spec:** `dev-docs/specs/2026-05-15-plcc-trees-error-handling-design.md`

**Run tests with:** `bin/test-unit` (Python unit tests), `bin/test-integration` (bats integration tests).

---

### Task 1: Refactor `predictive_parser.py` — new exception and return type

`ParseError` gains a `source` field; `IncompleteInputError` is removed (becomes a regular `ParseError`); `parse()` returns `(tree, consumed_count)` and no longer raises on trailing tokens.

**Files:**
- Modify: `src/plcc/parser/predictive_parser.py`
- Modify: `src/plcc/parser/predictive_parser_test.py`

- [ ] **Step 1: Write failing tests for new `ParseError` and `parse()` return type**

Add to the bottom of `src/plcc/parser/predictive_parser_test.py` (keep all existing tests — they will be updated in later steps):

```python
def test_parse_error_carries_source():
    with pytest.raises(ParseError) as exc_info:
        parse(_TRIVIAL_LL1, [_tok("PLUS", "+", line=3, col=7)])
    assert exc_info.value.source == {"file": "<stdin>", "line": 3, "column": 7}


def test_parse_returns_consumed_count():
    _, consumed = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert consumed == 1


def test_parse_stops_at_first_unconsumed_token():
    # Extra token after a complete parse: no exception, consumed=1
    tree, consumed = parse(_TRIVIAL_LL1, [_tok("NUM", "1"), _tok("NUM", "2")])
    assert consumed == 1
    assert tree["kind"] == "tree"


def test_incomplete_raises_ParseError_not_IncompleteInputError():
    # Grammar: program → NUM PLUS NUM; tokens: [NUM] — hits EOF before PLUS
    with pytest.raises(ParseError):
        parse(_ADDITION_LL1, [_tok("NUM", "1")])
```

- [ ] **Step 2: Run the new tests to verify they fail**

```
cd /workspaces/plcc-ng && python -m pytest src/plcc/parser/predictive_parser_test.py::test_parse_error_carries_source src/plcc/parser/predictive_parser_test.py::test_parse_returns_consumed_count src/plcc/parser/predictive_parser_test.py::test_parse_stops_at_first_unconsumed_token src/plcc/parser/predictive_parser_test.py::test_incomplete_raises_ParseError_not_IncompleteInputError -v
```

Expected: all FAIL.

- [ ] **Step 3: Implement changes to `predictive_parser.py`**

Replace the entire contents of `src/plcc/parser/predictive_parser.py` with:

```python
class ParseError(Exception):
    def __init__(self, message, source=None):
        super().__init__(message)
        self.source = source or {}


class NodeBuilder:
    def __init__(self, rule):
        self.rule = rule
        self.children = []
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


def parse(ll1: dict, tokens: list) -> tuple:
    """
    Parse tokens against the LL(1) parse table.

    ll1    — dict with keys: start_symbol, parse_table, arbno (optional)
    tokens — list of token dicts (may include a trailing '$' sentinel)

    Returns (tree_dict, consumed_count).
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
            if tok["name"] == "$":
                raise ParseError(
                    f"unexpected end of input: expected {sym!r}",
                    source=tok["source"],
                )
            raise ParseError(
                f"expected {sym!r}, got {tok['name']!r}",
                source=tok["source"],
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
            raise ParseError(
                f"no parse table entry for nonterminal {sym!r}",
                source=current()["source"],
            )
        production = nt_table.get(lookahead)
        if production is None:
            if lookahead == "$":
                raise ParseError(
                    f"unexpected end of input while parsing {sym!r}",
                    source=current()["source"],
                )
            raise ParseError(
                f"unexpected {lookahead!r}, no production for {sym!r}",
                source=current()["source"],
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
    return root_builder.to_node(), cursor[0]
```

- [ ] **Step 4: Update existing tests in `predictive_parser_test.py` for the new `(tree, consumed)` return**

Replace all calls of the form `result = parse(...)` / `parse(...)` in the non-error tests with `tree, consumed = parse(...)` and use `tree` where `result` was used. Also:

- Remove the import of `IncompleteInputError` at line 266.
- Replace `test_extra_tokens_after_parse_raises_parse_error` with:

```python
def test_parse_stops_at_first_unconsumed_token_existing():
    tree, consumed = parse(_TRIVIAL_LL1, [_tok("NUM", "1"), _tok("NUM", "2")])
    assert consumed == 1
    assert tree["kind"] == "tree"
```

- Replace `test_empty_input_on_nonempty_grammar_raises_parse_error` — it still raises ParseError (internal sentinel kicks in), no change needed except unpacking doesn't apply since it raises.

- Replace `test_incomplete_raises_IncompleteInputError_when_table_misses_sentinel` with:

```python
def test_incomplete_raises_ParseError():
    with pytest.raises(ParseError):
        parse(_ADDITION_LL1, [_tok("NUM", "1")])
```

- Replace `test_bad_token_raises_ParseError_not_IncompleteInputError` with:

```python
def test_bad_token_raises_ParseError():
    with pytest.raises(ParseError):
        parse(_TRIVIAL_LL1, [_tok("PLUS", "+")])
```

- For every test that calls `parse()` and assigns the result (e.g., `result = parse(...)`), change to `tree, _ = parse(...)` and use `tree` in place of `result`. Tests that only call `pytest.raises` need no change.

The full list of test functions that assign the result:
`test_trivial_parse_returns_tree_kind`, `test_trivial_parse_rule_is_start_symbol`, `test_trivial_parse_elided_symbol_not_in_children`, `test_trivial_parse_source_span`, `test_trivial_parse_source_file`, `test_capturing_child_in_children`, `test_capturing_children_are_token_dicts`, `test_elided_plus_not_in_children`, `test_span_covers_all_tokens_including_elided`, `test_nested_nonterminal_child_is_tree`, `test_arbno_separator_two_items_produces_list`, `test_arbno_separator_list_items_are_tree_nodes`, `test_arbno_separator_zero_items_on_no_match`, `test_arbno_separator_one_item`, `test_arbno_plain_multiple_items`, `test_arbno_plain_zero_items`, `test_arbno_result_is_tree_kind`.

- [ ] **Step 5: Run all predictive_parser tests**

```
cd /workspaces/plcc-ng && python -m pytest src/plcc/parser/predictive_parser_test.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/parser/predictive_parser.py src/plcc/parser/predictive_parser_test.py
git commit -m "refactor(parser): ParseError carries source, parse() returns (tree, consumed), remove IncompleteInputError"
```

---

### Task 2: `plcc-tokens` emits `$` sentinel at EOF

**Files:**
- Modify: `src/plcc/tokens/tokens_cli.py`

- [ ] **Step 1: Write a failing integration test**

Create `src/plcc/tokens/tokens_cli_sentinel_test.py`:

```python
import io
import json
import sys
from types import SimpleNamespace
import pytest
from plcc.tokens.tokens_cli import main as run_main


_TRIVIAL_SPEC = {
    "lexical": [
        {"name": "NUM", "regex": "[0-9]+", "skip": False}
    ]
}


def _run_tokens(spec_path, input_text):
    """Run tokens_cli.main with the given spec and input. Returns list of records."""
    import tempfile, os
    spec_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_SPEC, spec_file)
        spec_file.flush()
        spec_file.close()
        captured = []
        old_stdout = sys.stdout

        class Capture:
            def write(self, s):
                if s.strip():
                    try:
                        captured.append(json.loads(s.strip()))
                    except Exception:
                        pass
            def flush(self): pass

        sys.stdout = Capture()
        try:
            import plcc.tokens.tokens_cli as m
            old_stdin = sys.stdin
            sys.stdin = SimpleNamespace(
                isatty=lambda: False,
                buffer=io.BytesIO(input_text.encode())
            )
            try:
                run_main([spec_file.name, "-"])
            except SystemExit:
                pass
            finally:
                sys.stdin = old_stdin
        finally:
            sys.stdout = old_stdout
        return captured
    finally:
        os.unlink(spec_file.name)
```

Add a simpler test using `capsys` and subprocess:

```python
import subprocess
import json
import tempfile
import os
import pytest


_TRIVIAL_SPEC_JSON = json.dumps({
    "lexical": [{"name": "NUM", "regex": "[0-9]+", "skip": False}]
})


@pytest.fixture()
def spec_file(tmp_path):
    f = tmp_path / "spec.json"
    f.write_text(_TRIVIAL_SPEC_JSON)
    return str(f)


def test_tokens_emits_dollar_sentinel_at_eof(spec_file):
    result = subprocess.run(
        ["plcc-tokens", spec_file, "-"],
        input=b"42",
        capture_output=True,
    )
    records = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    last = records[-1]
    assert last["kind"] == "token"
    assert last["name"] == "$"
    assert last["lexeme"] == ""


def test_tokens_dollar_sentinel_has_source(spec_file):
    result = subprocess.run(
        ["plcc-tokens", spec_file, "-"],
        input=b"42",
        capture_output=True,
    )
    records = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    last = records[-1]
    assert "source" in last


def test_tokens_dollar_sentinel_on_empty_input(spec_file):
    result = subprocess.run(
        ["plcc-tokens", spec_file, "-"],
        input=b"",
        capture_output=True,
    )
    records = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert len(records) == 1
    assert records[0]["name"] == "$"
```

- [ ] **Step 2: Run new tests to verify they fail**

```
cd /workspaces/plcc-ng && python -m pytest src/plcc/tokens/tokens_cli_sentinel_test.py -v
```

Expected: FAIL (`$` not yet emitted).

- [ ] **Step 3: Implement `$` sentinel emission in `tokens_cli.py`**

In `src/plcc/tokens/tokens_cli.py`, locate the scan loop in `main()`:

```python
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            if trace:
                print(format_record(obj, show_all=True), flush=True)
            continue
        if isinstance(obj, LexError):
            print(format_error_record(obj), flush=True)
            continue
        print(format_record(obj, show_all=trace), flush=True)
    verbose.emit(Events.FINISHED, message="done")
```

Replace with:

```python
    last_source = {}
    for obj in scanner.scan(lines):
        if isinstance(obj, Skip):
            if trace:
                rec = json.loads(format_record(obj, show_all=True))
                last_source = rec.get("source", last_source)
                print(format_record(obj, show_all=True), flush=True)
            continue
        if isinstance(obj, LexError):
            print(format_error_record(obj), flush=True)
            continue
        rec_str = format_record(obj, show_all=trace)
        rec = json.loads(rec_str)
        last_source = rec.get("source", last_source)
        print(rec_str, flush=True)
    print(json.dumps({"kind": "token", "name": "$", "lexeme": "", "source": last_source}), flush=True)
    verbose.emit(Events.FINISHED, message="done")
```

Also add `import json` at the top if not already present.

- [ ] **Step 4: Run sentinel tests**

```
cd /workspaces/plcc-ng && python -m pytest src/plcc/tokens/tokens_cli_sentinel_test.py -v
```

Expected: all PASS.

- [ ] **Step 5: Run full unit test suite to check for regressions**

```
cd /workspaces/plcc-ng && bin/test-unit
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/tokens/tokens_cli.py src/plcc/tokens/tokens_cli_sentinel_test.py
git commit -m "feat(tokens): emit \$ sentinel token at EOF"
```

---

### Task 3: `plcc-parser-table` — skip-and-retry loop, JSONL stream, exit 0

**Files:**
- Modify: `src/plcc/parser/table_cli.py`
- Modify: `src/plcc/parser/table_cli_test.py`

- [ ] **Step 1: Write failing tests for new behavior**

Add to `src/plcc/parser/table_cli_test.py`:

```python
def _sentinel(line=1, col=1, file="-"):
    return {"kind": "token", "name": "$", "lexeme": "",
            "source": {"file": file, "line": line, "column": col}}


def test_exits_zero_on_syntax_error(monkeypatch):
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        bad = [_tok("PLUS", "+"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in bad) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        exit_code = 0
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit as e:
            exit_code = e.code or 0
        assert exit_code == 0
    finally:
        os.unlink(ll1_file.name)


def test_syntax_error_emits_error_record_with_source(capsys, monkeypatch):
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        bad = [_tok("PLUS", "+", line=2, col=5), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in bad) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        err_records = [r for r in records if r.get("kind") == "error"]
        assert len(err_records) >= 1
        assert err_records[0].get("source", {}).get("line") == 2
        assert err_records[0].get("source", {}).get("column") == 5
    finally:
        os.unlink(ll1_file.name)


def test_skip_and_retry_emits_error_then_tree(capsys, monkeypatch):
    # Grammar: program → NUM; tokens: [PLUS, NUM, $]
    # First parse fails at PLUS, skip; second parse succeeds at NUM.
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("PLUS", "+"), _tok("NUM", "42"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        kinds = [r["kind"] for r in records]
        assert "error" in kinds
        assert "tree" in kinds
        assert kinds.index("error") < kinds.index("tree")
    finally:
        os.unlink(ll1_file.name)


def test_two_programs_in_one_input_emits_two_trees(capsys, monkeypatch):
    # Grammar: program → NUM; tokens: [NUM, NUM, $] → two trees
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("NUM", "1"), _tok("NUM", "2"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        trees = [r for r in records if r.get("kind") == "tree"]
        assert len(trees) == 2


def test_incomplete_input_emits_error_record(capsys, monkeypatch):
    # Grammar: program → NUM PLUS NUM; tokens: [NUM, $] — incomplete
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_ADDITION_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        tokens = [_tok("NUM", "1"), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        assert any(r.get("kind") == "error" for r in records)
    finally:
        os.unlink(ll1_file.name)
```

- [ ] **Step 2: Run new tests to verify they fail**

```
cd /workspaces/plcc-ng && python -m pytest src/plcc/parser/table_cli_test.py::test_exits_zero_on_syntax_error src/plcc/parser/table_cli_test.py::test_syntax_error_emits_error_record_with_source src/plcc/parser/table_cli_test.py::test_skip_and_retry_emits_error_then_tree src/plcc/parser/table_cli_test.py::test_two_programs_in_one_input_emits_two_trees src/plcc/parser/table_cli_test.py::test_incomplete_input_emits_error_record -v
```

Expected: FAIL.

- [ ] **Step 3: Rewrite the parse loop in `table_cli.py`**

In `src/plcc/parser/table_cli.py`, replace the imports line for `IncompleteInputError`:

```python
from .predictive_parser import parse, ParseError
```

(Remove `IncompleteInputError` from the import.)

Replace the entire section from `# Parse` through `sys.exit(result.returncode)` (the parse block and exit at the bottom of `main()`) with:

```python
    # Run skip-and-retry loop
    cursor = 0
    while cursor < len(tokens) and tokens[cursor]["name"] != "$":
        try:
            tree, consumed = parse(ll1, tokens[cursor:])
            verbose.emit(Events.COMPLETE, token_count=consumed, rule_count=_count_rules(tree))
            print(json.dumps(tree), flush=True)
            cursor += consumed
        except ParseError as e:
            record = {
                "kind": "error",
                "message": str(e),
                "stage": "plcc-parser-table",
                "source": e.source,
            }
            verbose.emit_error(e.source, str(e))
            print(json.dumps(record), flush=True)
            cursor += 1

    verbose.emit(Events.FINISHED, token_count=len(tokens))
```

Also find the `try: ... except IncompleteInputError:` block (old code) and remove it entirely — the new loop above replaces it. And replace `sys.exit(1)` at the end with nothing (just fall through and exit 0).

The full updated `main()` body after reading ll1, checking `is_ll1`, and reading stdin tokens is:

```python
    if error_record is not None:
        print(json.dumps(error_record))
        return

    cursor = 0
    while cursor < len(tokens) and tokens[cursor]["name"] != "$":
        try:
            tree, consumed = parse(ll1, tokens[cursor:])
            verbose.emit(Events.COMPLETE, token_count=consumed, rule_count=_count_rules(tree))
            print(json.dumps(tree), flush=True)
            cursor += consumed
        except ParseError as e:
            record = {
                "kind": "error",
                "message": str(e),
                "stage": "plcc-parser-table",
                "source": e.source,
            }
            verbose.emit_error(e.source, str(e))
            print(json.dumps(record), flush=True)
            cursor += 1

    verbose.emit(Events.FINISHED, token_count=len(tokens))
```

(Using `return` instead of `sys.exit(0)` so the function exits cleanly; callers that catch `SystemExit` still work; `sys.exit` is only called for fatal errors like non-LL1 grammar or bad JSON.)

- [ ] **Step 4: Update existing tests that test old behavior**

In `table_cli_test.py`:

1. `test_stdout_is_valid_json`, `test_output_is_tree_kind`, `test_output_rule_is_start_symbol`, `test_output_has_source`, `test_capturing_child_in_tree` — these do `json.loads(out)` on the full output. Change to parse the first line: `json.loads(out.strip().splitlines()[0])`.

2. `test_exits_nonzero_on_syntax_error` — rename to `test_exits_zero_for_parse_error_but_emits_record` and assert `exit_code == 0`:

```python
def test_exits_zero_for_parse_error_but_emits_record(monkeypatch, capsys):
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_TRIVIAL_LL1, ll1_file)
        ll1_file.flush()
        ll1_file.close()
        monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_tok("IDENTIFIER", "x")) + "\n"))
        exit_code = 0
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit as e:
            exit_code = e.code or 0
        assert exit_code == 0
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        assert any(r.get("kind") == "error" for r in records)
    finally:
        os.unlink(ll1_file.name)
```

3. `test_incomplete_input_produces_no_stdout` — replace with `test_incomplete_input_emits_error_record` (already written above in new tests; remove the old test).

- [ ] **Step 5: Run all `table_cli` tests**

```
cd /workspaces/plcc-ng && python -m pytest src/plcc/parser/table_cli_test.py -v
```

Expected: all PASS.

- [ ] **Step 6: Run full unit test suite**

```
cd /workspaces/plcc-ng && bin/test-unit
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/parser/table_cli.py src/plcc/parser/table_cli_test.py
git commit -m "feat(parser-table): skip-and-retry loop, JSONL stream output, exit 0 always"
```

---

### Task 4: `SourceRunner` — `SubmitOn` enum and EOF accumulation mode

**Files:**
- Modify: `src/plcc/cmd/source_runner.py`
- Modify: `src/plcc/cmd/source_runner_test.py`

- [ ] **Step 1: Write failing tests for new `SubmitOn` enum and EOF mode**

Add to `src/plcc/cmd/source_runner_test.py`:

```python
from .source_runner import SourceRunner, SubmitOn, _InteractiveState


def _eof_runner():
    return SourceRunner(submit_on=SubmitOn.EOF)


def test_submit_on_required():
    with pytest.raises(TypeError):
        SourceRunner()


def test_eol_mode_submits_after_each_line(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b""]))
    handler = RecordingHandler(results=[True])
    SourceRunner(submit_on=SubmitOn.EOL).run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"line1\n"


def test_eof_mode_regular_line_accumulates_without_feed(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler()
    _eof_runner().run(["-"], handler)
    # ^D on empty buffer exits without calling feed
    assert handler.calls == []


def test_eof_mode_ctrl_d_with_buffer_calls_feed(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world\n", b""]))
    handler = RecordingHandler()
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\nworld\n"


def test_eof_mode_blank_line_accumulates_without_feed(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"\n", b""]))
    handler = RecordingHandler()
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\n\n"


def test_eof_mode_continuation_prompt_shown_after_first_line(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b""]))
    handler = RecordingHandler()
    _eof_runner().run(["-"], handler)
    _, err = capsys.readouterr()
    assert "... " in err


def test_eof_mode_partial_eof_submits_partial_line(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world", b""]))
    handler = RecordingHandler()
    _eof_runner().run(["-"], handler)
    assert len(handler.calls) == 1
    assert handler.calls[0][0] == b"hello\nworld"
```

- [ ] **Step 2: Update the `runner` fixture in `source_runner_test.py`**

Change:

```python
@pytest.fixture()
def runner():
    return SourceRunner()
```

to:

```python
@pytest.fixture()
def runner():
    return SourceRunner(submit_on=SubmitOn.EOL)
```

And update the import at the top:

```python
from .source_runner import SourceRunner, SubmitOn, _InteractiveState
```

- [ ] **Step 3: Run tests to verify they fail**

```
cd /workspaces/plcc-ng && python -m pytest src/plcc/cmd/source_runner_test.py::test_submit_on_required src/plcc/cmd/source_runner_test.py::test_eof_mode_regular_line_accumulates_without_feed src/plcc/cmd/source_runner_test.py::test_eof_mode_ctrl_d_with_buffer_calls_feed -v
```

Expected: FAIL.

- [ ] **Step 4: Implement `SubmitOn` and EOF mode in `source_runner.py`**

Replace the contents of `src/plcc/cmd/source_runner.py` with:

```python
import enum
import sys
from dataclasses import dataclass

HINT = "Enter input. Press ^D (EOF) when done."
PROMPT = ">>> "
CONTINUATION = "... "


class SubmitOn(enum.Enum):
    EOL = "eol"   # each newline submits — plcc-scan
    EOF = "eof"   # ^D submits — plcc-parse


@dataclass
class _InteractiveState:
    buffer: bytes
    prompt: str
    done: bool = False


class SourceRunner:
    def __init__(self, submit_on, hint=HINT, prompt=PROMPT, continuation=CONTINUATION):
        self._submit_on = submit_on
        self._hint = hint
        self._prompt = prompt
        self._continuation = continuation

    def run(self, sources, handler):
        """Run handler over sources. Returns False if any non-interactive feed
        signalled incomplete input (handler returned False); True otherwise."""
        effective = sources if sources else ["-"]
        completed = True
        for source in effective:
            if source == "-":
                if sys.stdin.isatty():
                    self._run_interactive(handler)
                else:
                    content = sys.stdin.buffer.read()
                    if handler.feed(content, "-") is False:
                        completed = False
            else:
                with open(source, "rb") as f:
                    content = f.read()
                if handler.feed(content, source) is False:
                    completed = False
        return completed

    def _run_interactive(self, handler):
        self._print_hint()
        state = _InteractiveState(buffer=b"", prompt=self._prompt)
        while not state.done:
            line = self._read_line(state.prompt)
            state = self._process_line(handler, line, state)

    def _print_hint(self):
        print(self._hint, file=sys.stderr)

    def _read_line(self, prompt):
        try:
            print(prompt, end="", flush=True, file=sys.stderr)
            return sys.stdin.buffer.readline()
        except KeyboardInterrupt:
            return None

    def _process_line(self, handler, line, state):
        if self._is_interrupted(line):
            return self._clear_buffer_or_exit(state)
        if self._is_eof(line):
            return self._exit_or_submit_accumulated_buffer(handler, state)
        if self._is_partial_eof(line):
            return self._force_submit_including_partial_line(handler, line, state)
        if self._submit_on == SubmitOn.EOF:
            return self._accumulate_only(line, state)
        # SubmitOn.EOL
        if self._is_blank(line):
            return self._force_submit_accumulated_buffer(handler, line, state)
        return self._accumulate_and_evaluate(handler, line, state)

    def _is_interrupted(self, line):
        return line is None

    def _is_eof(self, line):
        return not line

    def _is_partial_eof(self, line):
        return not line.endswith(b"\n")

    def _is_blank(self, line):
        return not line.strip()

    def _accumulate_only(self, line, state):
        buffer = state.buffer + line
        if not buffer.strip():
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        return _InteractiveState(buffer=buffer, prompt=self._continuation)

    def _clear_buffer_or_exit(self, state):
        print(file=sys.stderr)
        if state.buffer:
            print("KeyboardInterrupt", file=sys.stderr)
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        sys.exit(130)

    def _exit_or_submit_accumulated_buffer(self, handler, state):
        print(file=sys.stderr)
        if state.buffer:
            self._evaluate(handler, state.buffer, eof=True)
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        return _InteractiveState(buffer=b"", prompt=self._prompt, done=True)

    def _force_submit_including_partial_line(self, handler, line, state):
        print(file=sys.stderr)
        self._evaluate(handler, state.buffer + line, eof=True)
        return _InteractiveState(buffer=b"", prompt=self._prompt)

    def _force_submit_accumulated_buffer(self, handler, line, state):
        if state.buffer:
            self._evaluate(handler, state.buffer + line, eof=True)
        return _InteractiveState(buffer=b"", prompt=self._prompt)

    def _accumulate_and_evaluate(self, handler, line, state):
        buffer = state.buffer + line
        if self._evaluate(handler, buffer):
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        return _InteractiveState(buffer=buffer, prompt=self._continuation)

    def _evaluate(self, handler, content, eof=False):
        try:
            result = handler.feed(content, "-")
        except KeyboardInterrupt:
            print(file=sys.stderr)
            sys.exit(130)
        if eof and result is False:
            print("PLCC internal error: forced submission was not accepted by the handler.", file=sys.stderr)
            sys.exit(1)
        return result
```

- [ ] **Step 5: Run all `source_runner` tests**

```
cd /workspaces/plcc-ng && python -m pytest src/plcc/cmd/source_runner_test.py -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "feat(source-runner): add SubmitOn enum, required submit_on param, EOF accumulation mode"
```

---

### Task 5: `plcc-parse` — uniform record iteration; `plcc-scan` — pass `SubmitOn.EOL`

**Files:**
- Modify: `src/plcc/cmd/parse.py`
- Modify: `src/plcc/cmd/parse_test.py`
- Modify: `src/plcc/cmd/scan.py`

- [ ] **Step 1: Write failing tests for new `ParseHandler.feed()` behavior**

Add to `src/plcc/cmd/parse_test.py`:

```python
def _error_record_with_source(msg="syntax error", stage="plcc-parser-table",
                               file="-", line=2, col=5):
    return json.dumps({
        "kind": "error", "message": msg, "stage": stage,
        "source": {"file": file, "line": line, "column": col},
    }).encode() + b"\n"


def test_feed_error_renders_file_line_col(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad", file="foo.txt", line=3, col=7))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    _, err = capsys.readouterr()
    assert "foo.txt:3:7" in err
    assert "bad" in err


def test_feed_mixed_tree_and_error_renders_both(monkeypatch, handler, capsys):
    combined = _tree_record() + _error_record_with_source("trailing")
    procs = iter([_proc(), _proc(stdout=combined)])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"input\n", "-")
    out, err = capsys.readouterr()
    assert "program" in out
    assert "trailing" in err
    assert handler.had_error is True
```

- [ ] **Step 2: Update existing test for error format**

`test_feed_error_includes_stage_in_stderr` currently checks `"plcc-tokens" in err`. The new format is `loc: error: message` — no stage. Replace this test:

```python
def test_feed_error_shows_location_in_stderr(monkeypatch, handler, capsys):
    procs = iter([_proc(), _proc(stdout=_error_record_with_source("bad char", file="-", line=1, col=1))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"@\n", "-")
    _, err = capsys.readouterr()
    assert "-:1:1" in err
```

- [ ] **Step 3: Run new and updated tests to verify they fail**

```
cd /workspaces/plcc-ng && python -m pytest src/plcc/cmd/parse_test.py::test_feed_error_renders_file_line_col src/plcc/cmd/parse_test.py::test_feed_mixed_tree_and_error_renders_both src/plcc/cmd/parse_test.py::test_feed_error_shows_location_in_stderr -v
```

Expected: FAIL.

- [ ] **Step 4: Rewrite `ParseHandler.feed()` in `parse.py`**

Replace the `ParseHandler` class and the `_location_str` function in `src/plcc/cmd/parse.py`:

```python
def _location_str(source):
    file = source.get("file", "-")
    line = source.get("line", "?")
    col = source.get("column", "?")
    if file and file not in ("-", "<stdin>", ""):
        return f"{file}:{line}:{col}"
    return f"-:{line}:{col}"


class ParseHandler:
    def __init__(self, spec_path, ll1_path, child_flags):
        self._spec_path = spec_path
        self._ll1_path = ll1_path
        self._child_flags = child_flags
        self.had_error = False

    def feed(self, content, source):
        tokens_proc = subprocess.Popen(
            ["plcc-tokens", self._spec_path, "-"] + self._child_flags,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
        )
        tree_proc = subprocess.Popen(
            ["plcc-trees", f"--ll1={self._ll1_path}"] + self._child_flags,
            stdin=tokens_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=None,
        )
        tokens_proc.stdout.close()
        tokens_proc.stdin.write(content)
        tokens_proc.stdin.close()
        tree_out, _ = tree_proc.communicate()
        tokens_proc.wait()

        had_output = False
        for raw in tree_out.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            record = json.loads(raw)
            had_output = True
            if record.get("kind") == "error":
                loc = _location_str(record.get("source", {}))
                message = record.get("message", "error")
                print(f"{loc}: error: {message}", file=sys.stderr)
                self.had_error = True
            elif record.get("kind") == "tree":
                _print_tree(record, indent=0)
        return had_output
```

Also update `main()` in `parse.py` to use `SubmitOn.EOF`:

```python
from .source_runner import SourceRunner, SubmitOn
...
    handler = ParseHandler(spec_path=spec_path, ll1_path=ll1_path,
                           child_flags=child_flags)
    runner = SourceRunner(submit_on=SubmitOn.EOF)
    completed = runner.run(sources, handler)
```

- [ ] **Step 5: Update `scan.py` to pass `submit_on=SubmitOn.EOL`**

In `src/plcc/cmd/scan.py`, update the import and the `SourceRunner` construction:

```python
from .source_runner import SourceRunner, SubmitOn
...
    handler = ScanHandler(spec_path=spec_path, tokens_flags=tokens_flags)
    runner = SourceRunner(submit_on=SubmitOn.EOL)
    runner.run(sources, handler)
```

- [ ] **Step 6: Run all parse and scan tests**

```
cd /workspaces/plcc-ng && python -m pytest src/plcc/cmd/parse_test.py src/plcc/cmd/scan_test.py -v
```

Expected: all PASS.

- [ ] **Step 7: Run full unit test suite**

```
cd /workspaces/plcc-ng && bin/test-unit
```

Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add src/plcc/cmd/parse.py src/plcc/cmd/parse_test.py src/plcc/cmd/scan.py
git commit -m "feat(parse): uniform record iteration; scan: pass SubmitOn.EOL"
```

---

### Task 6: Rename `plcc-tree` → `plcc-trees`

**Files:**
- Modify: `src/plcc/tree/tree_cli.py`
- Modify: `pyproject.toml`
- Rename/modify: `tests/bats/commands/plcc-tree.bats` → `plcc-trees.bats`
- Modify: `tests/bats/integration/ll1-tree.bats`
- Modify: `tests/bats/integration/tokens-tree.bats`
- Modify: `tests/bats/integration/java-emit.bats`
- Modify: `tests/bats/integration/python-emit.bats`
- Modify: `tests/bats/integration/plcc-parse-errors.bats`

- [ ] **Step 1: Update `tree_cli.py` docstring**

In `src/plcc/tree/tree_cli.py`, change every occurrence of `plcc-tree` to `plcc-trees` in `__doc__`:

```python
__doc__ = """plcc-trees
    Dispatch to a parser plugin. Reads token JSONL, emits a parse tree.

Usage:
    plcc-trees [-v ...] [options] --ll1=LL1_JSON
...
"""
```

Also update the `print(...)` error message:

```python
        print(
            f"plcc-trees: parser plugin '{cmd}' not found on PATH.\n"
            f"Run plcc-parser-list to see what is available.",
            file=sys.stderr,
        )
```

- [ ] **Step 2: Update `pyproject.toml` entry point**

In `pyproject.toml`, change:

```toml
plcc-tree = "plcc.tree.tree_cli:main"
```

to:

```toml
plcc-trees = "plcc.tree.tree_cli:main"
```

- [ ] **Step 3: Reinstall the package so the new entry point is on PATH**

```
cd /workspaces/plcc-ng && pip install -e . -q
```

Verify:

```
command -v plcc-trees && echo "OK"
```

Expected: prints the path and "OK". Verify old name is gone:

```
command -v plcc-tree 2>&1 || echo "gone"
```

Expected: "gone".

- [ ] **Step 4: Rename bats test file and update references**

```bash
cd /workspaces/plcc-ng
git mv tests/bats/commands/plcc-tree.bats tests/bats/commands/plcc-trees.bats
```

In `tests/bats/commands/plcc-trees.bats`, replace all occurrences of `plcc-tree` with `plcc-trees`.

- [ ] **Step 5: Update integration bats files**

In each of the following files, replace all occurrences of `plcc-tree` with `plcc-trees`:

- `tests/bats/integration/ll1-tree.bats`
- `tests/bats/integration/tokens-tree.bats`
- `tests/bats/integration/java-emit.bats`
- `tests/bats/integration/python-emit.bats`
- `tests/bats/integration/plcc-parse-errors.bats`

For `plcc-parse-errors.bats` specifically, the comment and assertion check for `"plcc-tree:"` — update to `"plcc-trees:"`.

- [ ] **Step 6: Run bats tests**

```
cd /workspaces/plcc-ng && bin/test-integration
```

Expected: all PASS (or at least no failures related to the rename).

- [ ] **Step 7: Run full test suite**

```
cd /workspaces/plcc-ng && bin/test-unit && bin/test-integration
```

Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add src/plcc/tree/tree_cli.py pyproject.toml \
    tests/bats/commands/plcc-trees.bats \
    tests/bats/integration/ll1-tree.bats \
    tests/bats/integration/tokens-tree.bats \
    tests/bats/integration/java-emit.bats \
    tests/bats/integration/python-emit.bats \
    tests/bats/integration/plcc-parse-errors.bats
git commit -m "feat(tree): rename plcc-tree → plcc-trees"
```

---

## Self-Review

**Spec coverage check:**

| Spec section | Task |
|---|---|
| `plcc-tokens` emits `$` | Task 2 |
| `plcc-tree` → `plcc-trees` rename | Task 6 |
| `IncompleteInputError` removed, `parse()` returns `(tree, consumed)`, `ParseError` carries source | Task 1 |
| `plcc-parser-table` skip-and-retry loop, JSONL stream, exit 0 | Task 3 |
| `ParseHandler.feed()` uniform record iteration, `file:line:col` format | Task 5 |
| `SourceRunner` `SubmitOn` enum, required parameter, EOF mode | Task 4 |
| `plcc-scan` passes `SubmitOn.EOL` | Task 5 |
| Error records gain `source` field (issue 012) | Tasks 1, 3 |
| `file:line:col` in human-facing output (issue 019) | Task 5 |
| Tree emitted before trailing-token error (issue 022) | Task 3 |
| Multiple trees from one input (issue 008) | Task 3 |

**Placeholder scan:** None found.

**Type consistency:** `ParseError(message, source)` defined in Task 1, used in Tasks 1 and 3. `parse()` returns `(tree, consumed_count)` in Task 1, consumed in Task 3. `SubmitOn` defined in Task 4, used in Tasks 4 and 5. `plcc-trees` command name in Tasks 5 and 6. All consistent.

**One note:** Task 5 step 4 changes `ParseHandler` to call `plcc-trees` instead of `plcc-tree`. This depends on Task 6 completing the rename. If running tasks in order, Task 6 comes after Task 5, so `plcc-trees` won't exist yet when Task 5 runs. **Reorder:** swap Tasks 5 and 6 — rename first (Task 5), then update `parse.py` to call `plcc-trees` (Task 6). The plan as written has tasks numbered correctly but the rename (Task 6) should be executed before Task 5 step 4. Alternatively, update `parse.py` to still call `plcc-tree` in Task 5 and update the reference to `plcc-trees` in Task 6.

**Fix:** In Task 5 step 4, keep the subprocess call as `"plcc-tree"` for now. In Task 6 step 1, additionally update `parse.py` to use `"plcc-trees"`. Add a note to Task 6 step 1.
