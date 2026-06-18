# Incremental Parsing in Interactive Mode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the `SubmitOn.EOF` interactive model in `plcc-rep`/`plcc-parse` with incremental parsing that auto-detects complete sentences, holds extensible/incomplete input at a `...` prompt, and makes `^D` a single-press context exit.

**Architecture:** The LL(1) parser learns to report whether a successful parse is *extensible* (could be a prefix of a longer sentence). `plcc-parser-table` surfaces that signal as a sibling `hold` marker record (keeping the forwarded tree clean) and tags trailing incomplete fragments with their start position. A new pure function decides, per fed buffer, which complete sentences to commit and what text to retain. `SourceRunner` drives an incremental buffer and the new `^D` semantics. `pipeline.run()` is unchanged.

**Tech Stack:** Python 3.14, pytest. Run tests with `bin/test/units.bash` (whole suite) or `python -m pytest <path>` (single file/test) from the worktree root.

## Global Constraints

- Work entirely in the worktree `/workspaces/plcc-ng/.worktrees/093` on branch `093`. Never commit to `main`.
- TDD throughout: write the failing test, watch it fail, implement minimally, watch it pass, commit.
- All `eof=True` (force-submit / file / pipe / batch) output must stay byte-identical to today — changes are additive on that path so `plcc-parse` batch behavior and existing tests do not regress.
- Token `source` dicts use **1-based** `line` and `column` (confirmed in `src/plcc/tokens/jsonl_formatter.py`).
- `docs(...)` commit subjects must end with `[skip ci]`.
- Commit message footer for every commit:
  ```
  Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
  ```

---

### Task 1: Parser reports extensibility

`parse()` returns a third value, `extensible`, that is `True` when the parse stopped on the `eof` sentinel at a point where a real terminal could have continued the sentence.

**Files:**
- Modify: `src/plcc/parser/predictive_parser.py`
- Modify: `src/plcc/parser/table_cli.py` (call sites only, lines 80 and 116)
- Test: `src/plcc/parser/predictive_parser_test.py`

**Interfaces:**
- Produces: `parse(ll1, tokens, tracer=None) -> (tree: dict, consumed: int, extensible: bool)`.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/parser/predictive_parser_test.py`. `_TRIVIAL_LL1` (`program → NUM`) and `_RANDS_LL1` (an arbno with a `COMMA` separator) already exist. The extensible-via-nullable-tail case needs a new grammar constant — add it near the other `_LL1` constants:

```python
# E → NUM Tail ; Tail → PLUS NUM Tail | ε
# A single NUM is a complete parse, but "NUM + NUM" is also valid, so NUM is extensible.
_EXTENSIBLE_LL1 = {
    "is_ll1": True,
    "start_symbol": "E",
    "parse_table": {
        "E": {"NUM": {"alt": None, "production": [
            {"symbol": "NUM", "field": "n"},
            {"symbol": "Tail", "field": "t"},
        ]}},
        "Tail": {
            "PLUS": {"alt": None, "production": [
                {"symbol": "PLUS", "field": None},
                {"symbol": "NUM", "field": None},
                {"symbol": "Tail", "field": None},
            ]},
            "eof": {"alt": None, "production": []},
        },
    },
}
```

```python
def test_parse_returns_extensible_false_for_nonextensible_grammar():
    # program -> NUM ; a single NUM is complete and cannot be extended.
    _tree, _consumed, extensible = parse(_TRIVIAL_LL1, [_tok("NUM", "42")])
    assert extensible is False


def test_parse_returns_extensible_true_when_more_terminals_could_follow():
    # Nullable tail: parsing "3" takes Tail -> eps on eof, but PLUS could follow.
    _tree, _consumed, extensible = parse(_EXTENSIBLE_LL1, [_tok("NUM", "3")])
    assert extensible is True


def test_parse_returns_extensible_true_when_arbno_could_repeat():
    # Arbno list: after consuming one operand at eof, another (COMMA NUM) could follow.
    _tree, _consumed, extensible = parse(_RANDS_LL1, [_tok("NUM", "1")])
    assert extensible is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest src/plcc/parser/predictive_parser_test.py -k extensible -v`
Expected: FAIL — `parse()` returns a 2-tuple, so unpacking three values raises `ValueError: not enough values to unpack`.

- [ ] **Step 3: Implement extensibility detection**

In `src/plcc/parser/predictive_parser.py`, inside `parse()`, add a mutable flag right after `cursor = [0]`:

```python
    cursor = [0]
    extensible = [False]
```

In `_parse_regular`, immediately after the `production is None` check (after the `raise ParseError(... "no production for" ...)` block), add:

```python
        # The parse reached eof here but a real terminal could have continued
        # this nonterminal — the sentence is a prefix of a longer one.
        if lookahead == "eof" and any(k != "eof" for k in nt_table):
            extensible[0] = True
```

In `_parse_arbno`, just before `return builder`, add:

```python
        # Sitting at eof where another iteration could have started: extensible.
        if current()["name"] == "eof" and lookahead_set:
            extensible[0] = True
```

Change the final return of `parse()` from:

```python
    root_builder = parse_nt(start)
    return root_builder.to_node(), cursor[0]
```

to:

```python
    root_builder = parse_nt(start)
    return root_builder.to_node(), cursor[0], extensible[0]
```

- [ ] **Step 4: Update the two production call sites in `table_cli.py`**

In `src/plcc/parser/table_cli.py`, change both `tree, consumed = parse(ll1, tokens[cursor:], tracer=tracer)` lines (around lines 80 and 116) to:

```python
            tree, consumed, extensible = parse(ll1, tokens[cursor:], tracer=tracer)
```

(The `extensible` value is consumed in Task 2; binding it now keeps the unpacking valid.)

- [ ] **Step 5: Update existing test call sites mechanically**

The existing tests unpack a 2-tuple. Update them in place:

```bash
cd /workspaces/plcc-ng/.worktrees/093
sed -i 's/tree, _ = parse(/tree, _, _ = parse(/g; s/tree, consumed = parse(/tree, consumed, _ = parse(/g; s/_, consumed = parse(/_, consumed, _ = parse(/g' src/plcc/parser/predictive_parser_test.py
```

Confirm no other file unpacks `parse()`:

```bash
grep -rn "= parse(" src/plcc --include="*.py" | grep -v "_, _ = parse\|consumed, _ = parse\|def parse\|ParseError"
```

Expected: only the bare `parse(...)` calls inside `pytest.raises`/tracer tests (no two-value unpacks) remain.

- [ ] **Step 6: Run the parser suite to verify it passes**

Run: `python -m pytest src/plcc/parser/predictive_parser_test.py -v`
Expected: PASS (all tests, including the three new ones).

- [ ] **Step 7: Commit**

```bash
git add src/plcc/parser/predictive_parser.py src/plcc/parser/predictive_parser_test.py src/plcc/parser/table_cli.py
git commit -m "$(printf 'feat(093): parser reports sentence extensibility\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>')"
```

---

### Task 2: `plcc-parser-table` surfaces hold marker and fragment start

For the trailing parse, emit a sibling `hold` marker when the sentence is complete-but-extensible (so the forwarded tree stays clean), and attach the fragment `start` source to a trailing incomplete (`found="eof"`) error.

**Files:**
- Modify: `src/plcc/parser/table_cli.py`
- Test: `src/plcc/parser/table_cli_test.py`

**Interfaces:**
- Consumes: `parse(...) -> (tree, consumed, extensible)` from Task 1.
- Produces (on stdout JSONL, in addition to existing trees/errors):
  - `{"kind": "hold", "source": {"file","line","column",...}}` — emitted immediately after the trailing tree when that final parse consumed all remaining tokens and was extensible. `source` is the trailing tree's own `source` (its start position).
  - Trailing incomplete error gains `"start": {<source of the first token of the failed parse>}` alongside the existing `"found": "eof"`.

- [ ] **Step 1: Write the failing tests**

Add to `src/plcc/parser/table_cli_test.py` (reuse the existing `_run`, `_tok`, `_sentinel`, `_TRIVIAL_LL1`, and `_ADDITION_LL1` helpers). This file does **not** have an extensible grammar — add the same `_EXTENSIBLE_LL1` constant defined in Task 1 (`E → NUM Tail ; Tail → PLUS NUM Tail | ε`) near the other `_LL1` constants:

```python
def test_trailing_extensible_parse_emits_hold_marker(capsys, monkeypatch):
    # Nullable tail: "3" is complete but extensible -> tree then a hold marker.
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_EXTENSIBLE_LL1, ll1_file)
        ll1_file.flush(); ll1_file.close()
        tokens = [_tok("NUM", "3", col=1), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        kinds = [r.get("kind") for r in records]
        assert "tree" in kinds
        assert kinds[-1] == "hold"
        assert records[-1]["source"]["column"] == 1
    finally:
        os.unlink(ll1_file.name)


def test_nonextensible_parse_emits_no_hold_marker(capsys, monkeypatch):
    # program -> NUM : "42" is final, no hold marker.
    code = _run(_TRIVIAL_LL1, [_tok("NUM", "42"), _sentinel()])
    out, _ = capsys.readouterr()
    records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
    assert all(r.get("kind") != "hold" for r in records)


def test_trailing_incomplete_error_carries_start_source(capsys, monkeypatch):
    # program -> NUM PLUS NUM ; "1 +" at col 1 is incomplete.
    ll1_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(_ADDITION_LL1, ll1_file)
        ll1_file.flush(); ll1_file.close()
        tokens = [_tok("NUM", "1", col=1), _tok("PLUS", "+", col=3), _sentinel()]
        stdin_data = "\n".join(json.dumps(t) for t in tokens) + "\n"
        monkeypatch.setattr("sys.stdin", io.StringIO(stdin_data))
        try:
            run_main([f"--ll1={ll1_file.name}"])
        except SystemExit:
            pass
        out, _ = capsys.readouterr()
        records = [json.loads(l) for l in out.strip().splitlines() if l.strip()]
        err = [r for r in records if r.get("kind") == "error"][0]
        assert err["found"] == "eof"
        assert err["start"]["column"] == 1
    finally:
        os.unlink(ll1_file.name)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest src/plcc/parser/table_cli_test.py -k "hold or start_source" -v`
Expected: FAIL — no `hold` record is emitted; the error has no `start` key.

- [ ] **Step 3: Implement the hold marker (success branch)**

In `src/plcc/parser/table_cli.py`, in the main `while` loop, replace the success block (currently):

```python
            if trace:
                _emit_trace(tracer.events)
            verbose.emit(Events.COMPLETE, token_count=consumed, rule_count=_count_rules(tree))
            print(json.dumps(tree), flush=True)
            cursor += consumed
```

with:

```python
            if trace:
                _emit_trace(tracer.events)
            verbose.emit(Events.COMPLETE, token_count=consumed, rule_count=_count_rules(tree))
            print(json.dumps(tree), flush=True)
            cursor += consumed
            at_end = cursor >= len(tokens) or tokens[cursor]["name"] == "eof"
            if at_end and extensible:
                print(json.dumps({"kind": "hold", "source": tree.get("source", {})}), flush=True)
```

- [ ] **Step 4: Implement the `start` source on the incomplete error (failure branch)**

In the same loop, the `except ParseError as e:` block currently builds `record` and adds `record["found"] = e.found`. The first token of the failed attempt is `tokens[cursor]`. Update that block to:

```python
        except ParseError as e:
            _emit_trace(tracer.events)
            record = {
                "kind": "error",
                "message": str(e),
                "stage": "plcc-parser-table",
                "source": e.source,
            }
            if e.found:
                record["found"] = e.found
            if e.found == "eof" and cursor < len(tokens):
                record["start"] = tokens[cursor].get("source", {})
            print(json.dumps(record), flush=True)
            break
```

Leave the second (epsilon-grammar) `except ParseError` block near the bottom unchanged — it handles empty input where `cursor` has no first token to point at.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest src/plcc/parser/table_cli_test.py -v`
Expected: PASS (new tests plus all existing — `eof=True`-equivalent batch output is unchanged except the additive `hold`/`start` fields).

- [ ] **Step 6: Commit**

```bash
git add src/plcc/parser/table_cli.py src/plcc/parser/table_cli_test.py
git commit -m "$(printf 'feat(093): emit hold marker and incomplete-fragment start\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>')"
```

---

### Task 3: Commit/hold split helper

A pure function that, given `pipeline.run()` output, the original buffer bytes, and the `eof` flag, returns the records to dispatch and the remainder bytes to retain.

**Files:**
- Modify: `src/plcc/cmd/pipeline.py` (add functions; `TreePipeline.run` is unchanged)
- Test: `src/plcc/cmd/pipeline_test.py`
- Modify: `src/plcc/cmd/_test_helpers.py` (add a `hold` marker helper)

**Interfaces:**
- Consumes: `pipeline.run()` output — a list of `(record_dict, raw_bytes)` pairs.
- Produces:
  - `split_committed(items, content, eof) -> (dispatch_items: list, remainder: bytes)`.
  - `slice_from_source(content: bytes, source: dict) -> bytes` (helper; returns all of `content` if `source` lacks `line`/`column`).

- [ ] **Step 1: Add a hold-marker test helper**

Add to `src/plcc/cmd/_test_helpers.py`:

```python
def _hold_record(line=1, col=1, file="-"):
    return json.dumps({
        "kind": "hold",
        "source": {"file": file, "line": line, "column": col},
    }).encode() + b"\n"
```

- [ ] **Step 2: Write the failing tests**

Add a new test section to `src/plcc/cmd/pipeline_test.py`:

```python
from .pipeline import split_committed, slice_from_source
from ._test_helpers import _hold_record


def _items(*raws):
    """Build (record, raw) pairs from raw JSONL byte chunks (one record each)."""
    out = []
    for raw in raws:
        line = raw.strip()
        out.append((json.loads(line), line))
    return out


def test_slice_from_source_single_line():
    assert slice_from_source(b"3 + 4\n", {"line": 1, "column": 5}) == b"4\n"


def test_slice_from_source_multiline():
    assert slice_from_source(b"a\nbc\n", {"line": 2, "column": 2}) == b"c\n"


def test_slice_from_source_without_position_returns_all():
    assert slice_from_source(b"abc", {}) == b"abc"


def test_split_eof_dispatches_all_and_strips_hold():
    items = _items(_tree_record(), _hold_record())
    dispatch, remainder = split_committed(items, b"3\n", eof=True)
    assert [r.get("kind") for r, _ in dispatch] == ["tree"]
    assert remainder == b""


def test_split_trial_holds_trailing_extensible_tree():
    items = _items(_tree_record(), _hold_record(line=1, col=1))
    dispatch, remainder = split_committed(items, b"3\n", eof=False)
    assert dispatch == []           # the extensible tree is held, not dispatched
    assert remainder == b"3\n"


def test_split_trial_commits_leading_tree_holds_incomplete():
    # A committed final tree followed by a trailing incomplete fragment at col 3.
    eof_err = json.dumps({
        "kind": "error", "stage": "plcc-parser-table", "found": "eof",
        "message": "unexpected end of input",
        "source": {"file": "-", "line": 1, "column": 4},
        "start": {"file": "-", "line": 1, "column": 3},
    }).encode() + b"\n"
    items = _items(_tree_record(), eof_err)
    dispatch, remainder = split_committed(items, b"5;1+\n", eof=False)
    assert [r.get("kind") for r, _ in dispatch] == ["tree"]
    assert remainder == b"1+\n"


def test_split_trial_commits_final_tree_no_remainder():
    items = _items(_tree_record())   # final tree, no hold marker
    dispatch, remainder = split_committed(items, b"42\n", eof=False)
    assert [r.get("kind") for r, _ in dispatch] == ["tree"]
    assert remainder == b""


def test_split_trial_commits_genuine_error_no_remainder():
    items = _items(_error_record("bad token"))
    dispatch, remainder = split_committed(items, b"@\n", eof=False)
    assert [r.get("kind") for r, _ in dispatch] == ["error"]
    assert remainder == b""
```

(`5;1+` assumes a grammar with `;`-separated statements; the test only exercises the split logic, not real parsing, so the byte content just needs the `start` column to point at `1+`. Column 3 of `5;1+\n` is `1`, giving remainder `b"1+\n"`.)

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest src/plcc/cmd/pipeline_test.py -k "split or slice" -v`
Expected: FAIL — `ImportError: cannot import name 'split_committed'`.

- [ ] **Step 4: Implement the helper functions**

Add to `src/plcc/cmd/pipeline.py` (module-level, after `print_parse_error`):

```python
def slice_from_source(content, source):
    """Return content from the 1-based (line, column) in source to the end.

    Returns all of content when source lacks position info, so the caller
    holds the whole buffer rather than losing input."""
    if not source or "line" not in source or "column" not in source:
        return content
    text = content.decode("utf-8", errors="replace")
    lines = text.split("\n")
    line = source["line"]
    column = source["column"]
    offset = sum(len(l) + 1 for l in lines[: line - 1]) + (column - 1)
    return text[offset:].encode("utf-8")


def split_committed(items, content, eof):
    """Split pipeline.run() output into records to dispatch and bytes to retain.

    items     — list of (record, raw) pairs from TreePipeline.run().
    content   — the buffer that produced these records.
    eof       — True to force-submit (commit everything, retain nothing).

    Returns (dispatch_items, remainder_bytes).
    """
    if eof:
        dispatch = [(r, raw) for (r, raw) in items if r.get("kind") != "hold"]
        return dispatch, b""

    last = items[-1][0]
    if last.get("kind") == "hold":
        # Trailing complete-but-extensible sentence: hold the tree before it.
        return items[:-2], slice_from_source(content, last.get("source", {}))
    if last.get("kind") == "error" and last.get("found") == "eof":
        # Trailing incomplete fragment: commit leading trees, hold the fragment.
        return items[:-1], slice_from_source(content, last.get("start", {}))
    # Trailing is a final tree or a genuine error: commit everything.
    return items, b""
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest src/plcc/cmd/pipeline_test.py -v`
Expected: PASS (new tests plus all existing `TreePipeline.run` tests, which are untouched).

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/pipeline.py src/plcc/cmd/pipeline_test.py src/plcc/cmd/_test_helpers.py
git commit -m "$(printf 'feat(093): add commit/hold split helper\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>')"
```

---

### Task 4: Handlers return remainder bytes

`RepHandler.feed` and `ParseHandler.feed` change their return type from `bool` to remainder `bytes` (`b""` = fully consumed → `>>>`; non-empty = hold → `...`), using `split_committed`.

**Files:**
- Modify: `src/plcc/cmd/rep.py` (`RepHandler.feed`)
- Modify: `src/plcc/cmd/parse.py` (`ParseHandler.feed`)
- Test: `src/plcc/cmd/rep_test.py`, `src/plcc/cmd/parse_test.py`

**Interfaces:**
- Consumes: `split_committed`, `slice_from_source` from Task 3; `pipeline.run()` (returns list or `None`).
- Produces: `feed(content, source, eof=False) -> bytes` (remainder).

- [ ] **Step 1: Rewrite the rep feed tests**

In `src/plcc/cmd/rep_test.py`, the existing feed tests assert `is True` / `is False`. Update them to the bytes contract. Replace the bodies of the affected assertions as follows (keep the `procs`/`monkeypatch` setup lines):

- `test_feed_returns_false_when_no_tree`: assert `h.feed(b"1+\n", "-") == b"1+\n"` (no output → hold all).
- `test_feed_returns_true_when_tree_produced`: assert `h.feed(b"42\n", "-") == b""`.
- `test_feed_accepts_eof_kwarg`: assert `h.feed(b"\n", "-", eof=True) == b""`.
- `test_feed_returns_true_on_error_record`: assert `h.feed(b"bad\n", "-") == b""`.
- `test_feed_returns_false_for_eof_only_error_when_trial`: assert `h.feed(b"1+\n", "-", eof=False) == b"1+\n"`.
- `test_feed_returns_true_for_eof_only_error_when_force_submit`: assert `h.feed(b"1+\n", "-", eof=True) == b""`.
- `test_feed_returns_true_for_genuine_error_regardless_of_eof`: assert `h.feed(b"@\n", "-", eof=False) == b""`.

Add one new test for the hold-trailing-extensible path:

```python
def test_feed_holds_trailing_extensible_without_dispatch(monkeypatch, handler):
    from ._test_helpers import _hold_record
    h, interp = handler
    procs = iter([_proc(), _proc(stdout=_tree_record() + _hold_record(col=1))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    assert h.feed(b"3\n", "-", eof=False) == b"3\n"
    assert interp.stdin.tell() == 0  # extensible tree was NOT sent to interpreter
```

- [ ] **Step 2: Run rep feed tests to verify they fail**

Run: `python -m pytest src/plcc/cmd/rep_test.py -k feed -v`
Expected: FAIL — feed currently returns `True`/`False`, not bytes.

- [ ] **Step 3: Rewrite `RepHandler.feed`**

In `src/plcc/cmd/rep.py`, update the import line:

```python
from .pipeline import TreePipeline, print_parse_error, split_committed
```

Replace `RepHandler.feed` with:

```python
    def feed(self, content, source, eof=False):
        items = self._pipeline.run(content, eof)
        if items is None:
            return b"" if eof else content
        dispatch, remainder = split_committed(items, content, eof)
        for record, raw in dispatch:
            if record.get("kind") == "error":
                print_parse_error(record, default_stage="plcc-rep")
                break
            elif record.get("kind") == "tree":
                try:
                    self._interpreter.stdin.write(raw + b'\n')
                    self._interpreter.stdin.flush()
                except BrokenPipeError:
                    print('plcc-rep: interpreter exited unexpectedly', file=sys.stderr)
                    sys.exit(1)
                _read_response(self._interpreter.stdout, self._interpreter, self._verbose_format)
        return remainder
```

- [ ] **Step 4: Run rep feed tests to verify they pass**

Run: `python -m pytest src/plcc/cmd/rep_test.py -k feed -v`
Expected: PASS.

- [ ] **Step 5: Rewrite the parse feed tests**

In `src/plcc/cmd/parse_test.py`, update the analogous feed assertions to the bytes contract (mirror of Step 1):

- The "returns False" / "no tree" cases → assert `== b"<input>"` (hold).
- The "returns True" / tree / genuine-error / force-submit cases → assert `== b""`.

Keep the trace-buffering and tree-printing assertions as they are; only the return-value checks change.

- [ ] **Step 6: Run parse feed tests to verify they fail**

Run: `python -m pytest src/plcc/cmd/parse_test.py -k feed -v`
Expected: FAIL.

- [ ] **Step 7: Rewrite `ParseHandler.feed`**

In `src/plcc/cmd/parse.py`, update the import:

```python
from .pipeline import TreePipeline, print_parse_error, location_str, split_committed
```

Replace `ParseHandler.feed` with:

```python
    def feed(self, content, source, eof=False):
        items = self._pipeline.run(content, eof)
        if items is None:
            return b"" if eof else content
        dispatch, remainder = split_committed(items, content, eof)
        buffered_steps = []
        for record, _ in dispatch:
            if record.get("kind") == "parse-step":
                buffered_steps.append(record)
            elif record.get("kind") == "error":
                _render_trace(buffered_steps)
                print_parse_error(record, default_stage="plcc-parse")
                self.had_error = True
                break
            elif record.get("kind") == "tree":
                buffered_steps.clear()
                _print_tree(record, indent=0)
        return remainder
```

- [ ] **Step 8: Run parse feed tests to verify they pass**

Run: `python -m pytest src/plcc/cmd/parse_test.py -k feed -v`
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py src/plcc/cmd/parse.py src/plcc/cmd/parse_test.py
git commit -m "$(printf 'feat(093): handlers return remainder bytes\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>')"
```

---

### Task 5: Incremental `SourceRunner` with new `^D` semantics

Replace the all-or-nothing accumulate model and `SubmitOn.EOF`/double-`^D` machinery with a single incremental mode: each line feeds the buffer (`eof=False`) and the returned remainder becomes the new buffer; `^D` is a single-press context exit / force-submit.

**Files:**
- Modify: `src/plcc/cmd/source_runner.py`
- Test: `src/plcc/cmd/source_runner_test.py`

**Interfaces:**
- Consumes: `handler.feed(content, source, eof) -> bytes` (Task 4).
- Produces: `SourceRunner(hint=HINT, prompt=PROMPT, continuation=CONTINUATION)` (no `submit_on`); `run(sources, handler)` returns `None`. `SubmitOn` enum removed.

- [ ] **Step 1: Rewrite the test handler and the affected tests**

In `src/plcc/cmd/source_runner_test.py`:

Change `RecordingHandler.feed` to return **bytes** (the remainder) instead of booleans, and update its `results` to be byte strings:

```python
class RecordingHandler:
    """Captures feed() calls for assertions. results: iterator of remainder bytes."""
    def __init__(self, results=None):
        self._results = iter(results or [])
        self.calls = []       # list of (content, source)
        self.eof_flags = []   # parallel list of eof values

    def feed(self, content, source, eof=False):
        self.calls.append((content, source))
        self.eof_flags.append(eof)
        try:
            return next(self._results)
        except StopIteration:
            return b""
```

Update the `runner` fixture and helpers to construct `SourceRunner()` with no `submit_on`:

```python
@pytest.fixture()
def runner():
    return SourceRunner()
```

Remove the entire `# --- SubmitOn enum and EOF mode ---` section (every `test_eof_mode_*`, `test_submit_on_required`, `test_eol_mode_*`, the `_eof_runner`, `_read1_tty`, and the `SubmitOn` import). Remove the double-`^D` tests `test_first_ctrl_d_on_empty_prompt_prints_warning` and `test_second_ctrl_d_on_empty_prompt_exits_without_feed` and `test_input_after_ctrl_d_warning_clears_pending_exit`. Remove the `_InteractiveState.pending_exit` tests. Update the remaining behavior tests to the bytes/remainder contract and the new `^D` rules:

```python
def test_interactive_remainder_becomes_next_buffer(monkeypatch, runner):
    # First line is held (remainder == the line); second line completes it.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"a\n", b"b\n", b""]))
    handler = RecordingHandler(results=[b"a\n", b""])
    runner.run(["-"], handler)
    assert handler.calls[1][0] == b"a\nb\n"   # accumulated, fed again


def test_interactive_empty_remainder_resets_to_prompt(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b""]))
    handler = RecordingHandler(results=[b""])
    runner.run(["-"], handler)
    _, err = capsys.readouterr()
    assert err.count(">>> ") >= 2


def test_interactive_nonempty_remainder_shows_continuation(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b""]))
    handler = RecordingHandler(results=[b"line1\n"])
    runner.run(["-"], handler)
    _, err = capsys.readouterr()
    assert "... " in err


def test_ctrl_d_empty_buffer_exits_immediately(monkeypatch, runner):
    # Single ^D on the top-level prompt exits; feed is never called.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    handler = RecordingHandler()
    runner.run(["-"], handler)
    assert handler.calls == []


def test_ctrl_d_empty_buffer_prints_newline(monkeypatch, runner, capsys):
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b""]))
    runner.run(["-"], RecordingHandler())
    _, err = capsys.readouterr()
    assert err.endswith(">>> \n")


def test_ctrl_d_nonempty_buffer_force_submits_and_returns_to_prompt(monkeypatch, runner, capsys):
    # line1 is held; ^D on the continuation prompt force-submits with eof=True.
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"line1\n", b""]))
    handler = RecordingHandler(results=[b"line1\n", b""])
    runner.run(["-"], handler)
    assert handler.eof_flags[-1] is True
    assert handler.calls[-1][0] == b"line1\n"


def test_partial_line_then_ctrl_d_force_submits_with_partial(monkeypatch, runner):
    # "world" arrives with no trailing newline (text then ^D).
    monkeypatch.setattr(sys, "stdin", _tty_stdin([b"hello\n", b"world", b""]))
    handler = RecordingHandler(results=[b"hello\n", b""])
    runner.run(["-"], handler)
    assert handler.calls[-1][0] == b"hello\nworld"
    assert handler.eof_flags[-1] is True
```

Keep the file-source, non-tty, and `^C` (`KeyboardInterrupt`) tests, updating any `results=[True/False]` to bytes (`results=[b""]` for success, `results=[b"<content>"]` for hold). The `^C` semantics (`_clear_buffer_or_exit`) are unchanged.

- [ ] **Step 2: Run the source_runner tests to verify they fail**

Run: `python -m pytest src/plcc/cmd/source_runner_test.py -v`
Expected: FAIL — `SourceRunner()` still requires `submit_on`; feed-bytes behavior not implemented.

- [ ] **Step 3: Rewrite `source_runner.py`**

Replace the whole file with:

```python
import sys
from dataclasses import dataclass

HINT = "Enter input. Press ^D (EOF) when done."
PROMPT = ">>> "
CONTINUATION = "... "


@dataclass
class _InteractiveState:
    buffer: bytes
    prompt: str
    done: bool = False


class SourceRunner:
    def __init__(self, hint=HINT, prompt=PROMPT, continuation=CONTINUATION):
        self._hint = hint
        self._prompt = prompt
        self._continuation = continuation

    def run(self, sources, handler):
        """Run handler over sources. Interactive stdin parses incrementally;
        files and piped stdin are fed whole with eof=True."""
        effective = sources if sources else ["-"]
        for source in effective:
            if source == "-":
                if sys.stdin.isatty():
                    self._run_interactive(handler)
                else:
                    content = sys.stdin.buffer.read()
                    handler.feed(content, "-", eof=True)
            else:
                with open(source, "rb") as f:
                    content = f.read()
                handler.feed(content, source, eof=True)

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
        if line is None:
            return self._clear_buffer_or_exit(state)
        if line == b"":
            return self._ctrl_d(handler, state)
        if not line.endswith(b"\n"):
            return self._force_submit(handler, state.buffer + line)
        return self._incremental(handler, state.buffer + line)

    def _ctrl_d(self, handler, state):
        print(file=sys.stderr)
        if state.buffer:
            return self._force_submit(handler, state.buffer)
        return _InteractiveState(buffer=b"", prompt=self._prompt, done=True)

    def _force_submit(self, handler, content):
        remainder = self._evaluate(handler, content, eof=True)
        if remainder:
            print("PLCC internal error: forced submission left unconsumed input.",
                  file=sys.stderr)
            sys.exit(1)
        return _InteractiveState(buffer=b"", prompt=self._prompt)

    def _incremental(self, handler, content):
        remainder = self._evaluate(handler, content, eof=False)
        prompt = self._prompt if not remainder else self._continuation
        return _InteractiveState(buffer=remainder, prompt=prompt)

    def _clear_buffer_or_exit(self, state):
        print(file=sys.stderr)
        if state.buffer:
            print("KeyboardInterrupt", file=sys.stderr)
            return _InteractiveState(buffer=b"", prompt=self._prompt)
        sys.exit(130)

    def _evaluate(self, handler, content, eof):
        try:
            return handler.feed(content, "-", eof=eof)
        except KeyboardInterrupt:
            print(file=sys.stderr)
            sys.exit(130)
```

- [ ] **Step 4: Run the source_runner tests to verify they pass**

Run: `python -m pytest src/plcc/cmd/source_runner_test.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/source_runner.py src/plcc/cmd/source_runner_test.py
git commit -m "$(printf 'feat(093): incremental SourceRunner with single-press ^D\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>')"
```

---

### Task 6: Wire orchestrators to the incremental runner

`plcc-rep` and `plcc-parse` construct `SourceRunner()` without `SubmitOn` and drop the now-dead `completed` exit branch.

**Files:**
- Modify: `src/plcc/cmd/rep.py`
- Modify: `src/plcc/cmd/parse.py`
- Test: `src/plcc/cmd/rep_test.py`, `src/plcc/cmd/parse_test.py`

**Interfaces:**
- Consumes: `SourceRunner()` (Task 5).

- [ ] **Step 1: Update the rep main test**

In `src/plcc/cmd/rep_test.py`, `test_main_uses_eof_submit_mode` asserts the old `SubmitOn.EOF`. Replace it with a test that the runner is constructed without a submit mode:

```python
def test_main_constructs_runner_without_submit_mode(monkeypatch, tmp_path):
    """plcc-rep uses the single incremental SourceRunner (no SubmitOn)."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "grammar.plcc").write_text("")
    build = tmp_path / "build"
    build.mkdir()
    (build / ".spec").write_text(str(tmp_path / "grammar.plcc"))
    (build / "spec.json").write_text(_json.dumps({"semantics": {"language": "Python"}}))
    (build / "ll1.json").write_text("{}")

    captured = {}

    def capturing_runner(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        m = _MagicMock()
        m.run.return_value = None
        return m

    monkeypatch.setattr(_rep_module, "SourceRunner", capturing_runner)
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: _MagicMock(returncode=0, stderr=b""))
    monkeypatch.setattr("subprocess.Popen",
                        lambda *a, **kw: _MagicMock(stdin=_MagicMock(), wait=_MagicMock()))

    _rep_module.main(["--spec=grammar.plcc"])

    assert "submit_on" not in captured["kwargs"]
    assert captured["args"] == ()
```

Remove the now-unused `from .source_runner import SubmitOn` import from the test file.

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest src/plcc/cmd/rep_test.py -k construct_runner -v`
Expected: FAIL — `rep.main` still imports/uses `SubmitOn.EOF`.

- [ ] **Step 3: Update `rep.py`**

In `src/plcc/cmd/rep.py`:

Change the import `from .source_runner import SourceRunner, SubmitOn` to:

```python
from .source_runner import SourceRunner
```

Replace the runner construction and the trailing `completed` branch (currently):

```python
        runner = SourceRunner(submit_on=SubmitOn.EOF)
        completed = runner.run(sources, handler)
    finally:
        ...
    if not completed:
        sys.exit(1)
    verbose.emit(Events.FINISHED, message='done')
```

with:

```python
        runner = SourceRunner()
        runner.run(sources, handler)
    finally:
        ...
    verbose.emit(Events.FINISHED, message='done')
```

(Leave the `finally` block body unchanged.)

- [ ] **Step 4: Update `parse.py`**

In `src/plcc/cmd/parse.py`:

Change `from .source_runner import SourceRunner, SubmitOn` to `from .source_runner import SourceRunner`.

Replace:

```python
    runner = SourceRunner(submit_on=SubmitOn.EOF)
    completed = runner.run(sources, handler)

    if not completed or handler.had_error:
        sys.exit(1)
```

with:

```python
    runner = SourceRunner()
    runner.run(sources, handler)

    if handler.had_error:
        sys.exit(1)
```

- [ ] **Step 5: Update the parse main test if needed**

If `src/plcc/cmd/parse_test.py` has a test asserting `SubmitOn.EOF` or the `completed`/exit-on-incomplete behavior, update it the same way as Step 1 (assert `SourceRunner` is constructed with no args) or remove the obsolete incomplete-exit assertion. Run `grep -n "SubmitOn\|completed" src/plcc/cmd/parse_test.py` to find them.

- [ ] **Step 6: Run rep and parse suites to verify they pass**

Run: `python -m pytest src/plcc/cmd/rep_test.py src/plcc/cmd/parse_test.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/cmd/rep.py src/plcc/cmd/parse.py src/plcc/cmd/rep_test.py src/plcc/cmd/parse_test.py
git commit -m "$(printf 'feat(093): wire orchestrators to incremental runner\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>')"
```

---

### Task 7: End-to-end verification and docs

Verify the full behavior against a real grammar and update the orchestrator docs.

**Files:**
- Test: add an e2e/functional test under the existing e2e tree (see `bin/test/e2e.bash` / `bin/test/functional.bash` for the layout; place the new test beside the existing `plcc-rep`/`plcc-parse` e2e tests).
- Modify: `docs/cli/orchestrators.md`

- [ ] **Step 1: Locate the existing interactive e2e tests**

Run: `grep -rln "plcc-rep\|SubmitOn\|continuation\|>>> " test e2e tests 2>/dev/null; ls bin/test`
Identify where `plcc-rep`/`plcc-parse` interactive behavior is exercised so the new test matches the established harness style.

- [ ] **Step 2: Write a failing e2e test for the incremental flow**

Using the existing harness conventions, add a test that drives `plcc-parse` (or `plcc-rep`) against a small expression grammar via a pipe and asserts:
- Feeding `3\n` then EOF (`^D`) produces one parse result (held `3` is force-submitted at EOF), not two.
- Feeding `3\n4\n` then EOF: `3` is held and extended-attempted; on the second line `3` and `4` are independent complete sentences — assert two results are produced (the first `3` committed when `4` begins a new sentence on its own line) per the split rule.
- Feeding a complete-final sentence followed on the same line by the start of another (e.g. `5;1+`) splits: the first is evaluated, `1+` is retained.

Match the exact assertion mechanism (golden files vs. inline string asserts) used by the neighboring e2e tests.

- [ ] **Step 3: Run it to verify it fails, then run the full suite**

Run: `bin/test/units.bash` and the relevant `bin/test/e2e.bash` (or `functional.bash`).
Expected: the new e2e test fails first if the harness wiring is incomplete; fix wiring until it passes. Then the full unit suite passes with no regressions (the pre-existing `test_emit_generated_main_exits_130_on_sigint` failure noted at baseline is unrelated to this work — confirm it is the only remaining failure).

- [ ] **Step 4: Update `docs/cli/orchestrators.md`**

Document the new interactive behavior for `plcc-rep` and `plcc-parse`:
- After each line, complete sentences are evaluated; a complete-but-extensible or incomplete prefix continues at the `...` prompt.
- `^D` at `>>>` exits immediately (no second press). `^D` at `...` force-submits the buffer (evaluating complete sentences and reporting any trailing incomplete fragment as an error) and returns to `>>>`.
- No submit chord is needed; remove any references to "press ^D when done to submit the whole buffer" that describe the old `SubmitOn.EOF` model.

Verify any rendered command examples still match actual output.

- [ ] **Step 5: Commit**

```bash
git add docs/cli/orchestrators.md test  # plus the new e2e test path
git commit -m "$(printf 'docs(093): document incremental interactive mode and ^D [skip ci]\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>')"
```

(Split into two commits — a `feat(093)` for the e2e test and a `docs(093): ... [skip ci]` for the docs — if you prefer the e2e test to run in CI.)

---

## Self-Review

**Spec coverage:**
- Incremental evaluation (peel complete-final, hold extensible/incomplete) → Tasks 1–4.
- The three parser scenarios (final / extensible / complete+leftover) → Task 1 (extensible flag), Task 2 (hold marker + start), table_cli's existing multi-tree loop (leftover).
- `^D` rules 1–3 (single-press exit; force-submit at `...`; partial-line force-submit) → Task 5.
- Force-submit never holds; trailing incomplete reported as error → Task 3 (`split_committed` with `eof=True`) + Task 4.
- Global application, remove `SubmitOn.EOF` and double-`^D` → Tasks 5–6.
- Docs → Task 7.

**Placeholder scan:** No "TBD"/"handle edge cases" left; Task 7 Steps 1–2 intentionally defer exact assertion mechanics to the discovered harness, with concrete behaviors to assert.

**Type consistency:** `parse() -> (tree, consumed, extensible)` (Task 1) consumed in Task 2; `split_committed(items, content, eof) -> (dispatch, remainder)` and `slice_from_source(content, source) -> bytes` (Task 3) consumed identically in Task 4; `feed(...) -> bytes` (Task 4) consumed by `SourceRunner._evaluate` (Task 5); `SourceRunner()` no-arg (Task 5) consumed in Task 6. The `hold` marker shape `{"kind":"hold","source":{...}}` is produced in Task 2 and matched in Tasks 3–4.
