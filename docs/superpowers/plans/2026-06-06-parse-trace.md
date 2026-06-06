# Parse Trace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `--trace` with automatic Style B trace output before parse errors, and remove the flag entirely.

**Architecture:** Buffer `parse-step` records in `ParseHandler.feed()`; on error render them with a new `_render_trace()` function (Style B: indented rule names and tokens); on success discard them. Remove the `--trace`/`-t` CLI option and all supporting code.

**Tech Stack:** Python, pytest, bats

---

## File Map

| File | Change |
|------|--------|
| `src/plcc/cmd/parse.py` | Add `_render_trace()`, update `ParseHandler.feed()`, remove `--trace`/`-t`, remove `_print_parse_step`, remove `trees_flags` trace logic |
| `src/plcc/cmd/parse_test.py` | Remove 3 old parse-step tests; add tests for `_render_trace` and new `feed()` behavior |
| `src/plcc/cmd/_test_helpers.py` | Add `_shift_step_record()` and `_complete_step_record()` helpers |
| `tests/bats/commands/plcc-parse.bats` | Remove `--trace`/`-t` tests; rewrite failure-trace tests to check Style B format |

---

## Task 1: Add test helpers for shift and complete step records

**Files:**

- Modify: `src/plcc/cmd/_test_helpers.py`

- [ ] **Step 1: Add helpers**

Append to the bottom of `src/plcc/cmd/_test_helpers.py`:

```python
def _shift_step_record(name="NUM", lexeme="42", file="-", line=1, col=1, depth=1):
    return json.dumps({
        "kind": "parse-step",
        "event": "shift",
        "name": name,
        "lexeme": lexeme,
        "source": {"file": file, "line": line, "column": col},
        "depth": depth,
    }).encode() + b"\n"


def _complete_step_record(rule="program", depth=0):
    return json.dumps({
        "kind": "parse-step",
        "event": "complete",
        "rule": rule,
        "depth": depth,
    }).encode() + b"\n"
```

Also update the import in `parse_test.py` to include the new helpers:

```python
from ._test_helpers import (
    _proc, _tree_record, _error_record, _error_record_with_source,
    _eof_error_record, _parse_step_record, _shift_step_record, _complete_step_record,
)
```

- [ ] **Step 2: Run units to confirm no breakage**

```bash
cd .worktrees/069-improve-parse-trace
bin/test/units.bash
```

Expected: all pass (no new tests added yet).

- [ ] **Step 3: Commit**

```bash
git add src/plcc/cmd/_test_helpers.py src/plcc/cmd/parse_test.py
git commit -m "test(069): add shift and complete step record helpers"
```

---

## Task 2: Write failing unit tests for `_render_trace`

**Files:**

- Modify: `src/plcc/cmd/parse_test.py`

The `_render_trace` function does not exist yet — all tests below must fail.

- [ ] **Step 1: Add the tests**

Add after the existing imports in `parse_test.py`:

```python
from .parse import _render_trace
```

Then add the following test functions. Add them after the last existing test in the file:

```python
# --- _render_trace tests ---

def test_render_trace_empty_produces_no_output(capsys):
    _render_trace([])
    out, _ = capsys.readouterr()
    assert out == ""


def test_render_trace_single_rule_with_token(capsys):
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "program",
         "production": "program", "depth": 0},
        {"kind": "parse-step", "event": "shift", "name": "NUM", "lexeme": "42",
         "source": {"file": "-", "line": 1, "column": 1}, "depth": 1},
        {"kind": "parse-step", "event": "complete", "rule": "program", "depth": 0},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0] == "program"
    assert lines[1] == "  NUM '42' [-:1:1]"


def test_render_trace_empty_rule_shows_empty_annotation(capsys):
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "NilRest",
         "production": "NilRest", "depth": 2},
        {"kind": "parse-step", "event": "complete", "rule": "NilRest", "depth": 2},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    assert out.strip() == "    NilRest (empty)"


def test_render_trace_nested_rules_indented_correctly(capsys):
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "program",
         "production": "program", "depth": 0},
        {"kind": "parse-step", "event": "predict", "sym": "expr",
         "production": "expr", "depth": 1},
        {"kind": "parse-step", "event": "shift", "name": "NUM", "lexeme": "1",
         "source": {"file": "-", "line": 1, "column": 1}, "depth": 2},
        {"kind": "parse-step", "event": "complete", "rule": "expr", "depth": 1},
        {"kind": "parse-step", "event": "complete", "rule": "program", "depth": 0},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0] == "program"
    assert lines[1] == "  expr"
    assert lines[2] == "    NUM '1' [-:1:1]"


def test_render_trace_incomplete_rules_flushed_at_error(capsys):
    # Error occurred: no shift, no complete events
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "program",
         "production": "program", "depth": 0},
        {"kind": "parse-step", "event": "predict", "sym": "expr",
         "production": "expr", "depth": 1},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    lines = out.splitlines()
    assert lines[0] == "program"
    assert lines[1] == "  expr"
    assert "(empty)" not in out


def test_render_trace_uses_production_name_not_sym(capsys):
    # When a rule has an alternative, production holds the class name
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "exprRest",
         "production": "AddRest", "depth": 0},
        {"kind": "parse-step", "event": "shift", "name": "PLUS", "lexeme": "+",
         "source": {"file": "-", "line": 1, "column": 3}, "depth": 1},
        {"kind": "parse-step", "event": "complete", "rule": "AddRest", "depth": 0},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    assert out.splitlines()[0] == "AddRest"
    assert "exprRest" not in out


def test_render_trace_token_location_uses_bracket_format(capsys):
    steps = [
        {"kind": "parse-step", "event": "predict", "sym": "program",
         "production": "program", "depth": 0},
        {"kind": "parse-step", "event": "shift", "name": "NUM", "lexeme": "99",
         "source": {"file": "foo.txt", "line": 3, "column": 7}, "depth": 1},
        {"kind": "parse-step", "event": "complete", "rule": "program", "depth": 0},
    ]
    _render_trace(steps)
    out, _ = capsys.readouterr()
    assert "NUM '99' [foo.txt:3:7]" in out
```

- [ ] **Step 2: Run to confirm all new tests fail**

```bash
bin/test/units.bash 2>&1 | grep -E "(FAILED|ERROR|_render_trace)"
```

Expected: all `_render_trace` tests fail with `ImportError: cannot import name '_render_trace'`.

- [ ] **Step 3: Commit**

```bash
git add src/plcc/cmd/parse_test.py
git commit -m "test(069): add failing tests for _render_trace [skip ci]"
```

---

## Task 3: Implement `_render_trace`

**Files:**

- Modify: `src/plcc/cmd/parse.py`

- [ ] **Step 1: Add `_render_trace` at the bottom of `parse.py`**

Add after `_print_parse_step`:

```python
def _render_trace(steps):
    stack = []  # dicts: {"rule": str, "depth": int, "printed": bool}
    for step in steps:
        event = step.get("event")
        depth = step.get("depth", 0)
        if event == "predict":
            rule = step.get("production") or step.get("sym", "?")
            stack.append({"rule": rule, "depth": depth, "printed": False})
        elif event == "shift":
            for frame in stack:
                if not frame["printed"]:
                    print("  " * frame["depth"] + frame["rule"])
                    frame["printed"] = True
            name = step.get("name", "?")
            lexeme = step.get("lexeme", "?")
            source = step.get("source", {})
            loc = location_str(source)
            loc_str = f" [{loc}]" if loc else ""
            print(f"{'  ' * depth}{name} '{lexeme}'{loc_str}")
        elif event == "complete":
            if stack:
                frame = stack[-1]
                if not frame["printed"]:
                    print(f"{'  ' * frame['depth']}{frame['rule']} (empty)")
                stack.pop()
    for frame in stack:
        if not frame["printed"]:
            print("  " * frame["depth"] + frame["rule"])
```

- [ ] **Step 2: Run the new tests**

```bash
bin/test/units.bash 2>&1 | grep -E "(FAILED|ERROR|PASSED|render_trace)"
```

Expected: all 7 `_render_trace` tests pass.

- [ ] **Step 3: Commit**

```bash
git add src/plcc/cmd/parse.py
git commit -m "feat(069): add _render_trace for Style B parse trace output"
```

---

## Task 4: Write failing unit tests for new `feed()` behavior

**Files:**

- Modify: `src/plcc/cmd/parse_test.py`

The new behavior: buffer parse-step records, render them before error, discard them on success.

- [ ] **Step 1: Remove the three old parse-step tests**

Delete these three test functions from `parse_test.py`:

- `test_feed_renders_parse_step_records`
- `test_feed_parse_step_printed_before_tree`
- `test_feed_parse_step_depth_indented`

- [ ] **Step 2: Add new tests**

Add after the `_render_trace` tests:

```python
# --- ParseHandler.feed() trace buffering tests ---

def test_feed_on_error_renders_trace_before_error(monkeypatch, handler, capsys):
    step = _parse_step_record(event="predict", sym="program",
                               production="program", depth=0)
    procs = iter([_proc(), _proc(stdout=step + _error_record("oops"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    out, _ = capsys.readouterr()
    rule_pos = out.index("program")
    error_pos = out.index("oops")
    assert rule_pos < error_pos


def test_feed_on_error_does_not_show_old_trace_vocabulary(monkeypatch, handler, capsys):
    step = _parse_step_record(event="predict", sym="program",
                               production="program", depth=0)
    procs = iter([_proc(), _proc(stdout=step + _error_record("oops"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"bad\n", "-")
    out, _ = capsys.readouterr()
    assert "predict" not in out
    assert "shift" not in out
    assert "complete" not in out


def test_feed_on_success_does_not_render_trace(monkeypatch, capsys):
    # Use a rule name different from "program" so we can distinguish trace from tree
    handler = ParseHandler(spec_path="build/spec.json", ll1_path="build/ll1.json",
                           child_flags=[])
    step = _parse_step_record(event="predict", sym="traceSentinel",
                               production="traceSentinel", depth=0)
    procs = iter([_proc(), _proc(stdout=step + _tree_record())])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"42\n", "-")
    out, _ = capsys.readouterr()
    assert "traceSentinel" not in out


def test_feed_on_error_with_shift_shows_token_in_trace(monkeypatch, handler, capsys):
    predict = _parse_step_record(event="predict", sym="program",
                                  production="program", depth=0)
    shift = _shift_step_record(name="NUM", lexeme="42", depth=1)
    procs = iter([_proc(), _proc(stdout=predict + shift + _error_record("oops"))])
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: next(procs))
    handler.feed(b"42\n", "-")
    out, _ = capsys.readouterr()
    assert "NUM '42'" in out
    assert "program" in out
```

- [ ] **Step 3: Run to confirm new tests fail and old tests are gone**

```bash
bin/test/units.bash 2>&1 | grep -E "(FAILED|ERROR|feed.*trace|trace.*feed)"
```

Expected: the 4 new feed trace tests fail.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/parse_test.py
git commit -m "test(069): add failing feed() trace buffering tests [skip ci]"
```

---

## Task 5: Update `ParseHandler.feed()` to buffer and render on error

**Files:**

- Modify: `src/plcc/cmd/parse.py`

- [ ] **Step 1: Update `ParseHandler.feed()`**

Replace the existing `feed` method body with:

```python
def feed(self, content, source, eof=False):
    items = self._pipeline.run(content, eof)
    if items is None:
        return False
    buffered_steps = []
    for record, _ in items:
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
    return True
```

- [ ] **Step 2: Run the new tests**

```bash
bin/test/units.bash 2>&1 | grep -E "(FAILED|ERROR|PASSED|feed.*trace|trace.*feed)"
```

Expected: all 4 new feed trace tests pass.

- [ ] **Step 3: Run the full unit suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: all pass.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/cmd/parse.py
git commit -m "feat(069): buffer parse-step records and render trace before errors"
```

---

## Task 6: Remove `--trace`/`-t` flag and clean up dead code

**Files:**

- Modify: `src/plcc/cmd/parse.py`

- [ ] **Step 1: Remove the `--trace` option from `__doc__`**

In the `__doc__` string, remove this line:

```
    -t --trace                  Show step-by-step trace of the parse algorithm.
```

- [ ] **Step 2: Remove the `trace` arg extraction and `trees_flags` trace logic**

Note: `plcc-parser-table` already emits parse-step records unconditionally on `ParseError` (no `--trace` flag needed). The `--trace` flag only controls emission on *success*, which we no longer need. So removing `trees_flags` is safe.

Remove these lines from `main()`:

```python
trace = args["--trace"]
```

```python
trees_flags = child_flags + (["--trace"] if trace else [])
```

Change the `ParseHandler` construction to remove `trees_flags`:

```python
handler = ParseHandler(spec_path=spec_path, ll1_path=ll1_path,
                       child_flags=child_flags, verbose=verbose)
```

- [ ] **Step 3: Remove `trees_flags` parameter from `ParseHandler.__init__`**

Update `ParseHandler.__init__` signature and body. Change:

```python
def __init__(self, spec_path, ll1_path, child_flags, trees_flags=None, verbose=None):
    self._pipeline = TreePipeline(spec_path, ll1_path, child_flags, trees_flags=trees_flags, verbose=verbose)
```

To:

```python
def __init__(self, spec_path, ll1_path, child_flags, verbose=None):
    self._pipeline = TreePipeline(spec_path, ll1_path, child_flags, verbose=verbose)
```

- [ ] **Step 4: Remove `_print_parse_step`**

Delete the entire `_print_parse_step` function (lines ~143–164 in the original file).

- [ ] **Step 5: Run unit tests**

```bash
bin/test/units.bash
```

Expected: all pass. The `trees_flags` parameter is removed from `ParseHandler.__init__`; existing unit tests construct `ParseHandler` without it, so no changes needed there.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/parse.py
git commit -m "feat(069): remove --trace flag and dead trace code"
```

---

## Task 7: Update bats tests

**Files:**

- Modify: `tests/bats/commands/plcc-parse.bats`

- [ ] **Step 1: Remove the five `--trace`/`-t` tests**

Delete these five `@test` blocks entirely:

- `plcc-parse --trace shows predict in output`
- `plcc-parse --trace shows shift in output`
- `plcc-parse --trace shows complete in output`
- `plcc-parse --trace trace appears before tree`
- `plcc-parse -t is short for --trace`

- [ ] **Step 2: Update the three failure-trace tests**

Replace these three existing tests:

```bash
@test "plcc-parse no trace on success without --trace" {
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" != *"predict"* ]]
    [[ "$output" != *"shift"* ]]
    [[ "$output" != *"complete"* ]]
}

@test "plcc-parse shows trace on parse failure without --trace" {
    cp "${FIXTURES}/arith.plcc" grammar.plcc
    run bash -c "cd '${WORK_DIR}' && echo '1 +' | plcc-parse"
    [ "$status" -ne 0 ]
    [[ "$output" == *"predict"* ]]
    [[ "$output" == *"shift"* ]]
}

@test "plcc-parse failure trace appears before error message" {
    cp "${FIXTURES}/arith.plcc" grammar.plcc
    run bash -c "cd '${WORK_DIR}' && echo '1 +' | plcc-parse"
    [ "$status" -ne 0 ]
    predict_line=$(echo "$output" | grep -n "predict" | head -1 | cut -d: -f1)
    error_line=$(echo "$output" | grep -n "error:" | head -1 | cut -d: -f1)
    [ "$predict_line" -lt "$error_line" ]
}
```

With:

```bash
@test "plcc-parse no algorithm terms in output on success" {
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" != *"predict"* ]]
    [[ "$output" != *"shift"* ]]
    [[ "$output" != *"complete"* ]]
}

@test "plcc-parse shows partial tree before error on parse failure" {
    cat > grammar.plcc << 'GRAMMAR'
token NUM '\d+'
token PLUS '\+'
skip WS '\s+'
%
<program> ::= <expr>
<expr> ::= NUM PLUS NUM
GRAMMAR
    run bash -c "cd '${WORK_DIR}' && echo '1 +' | plcc-parse"
    [ "$status" -ne 0 ]
    [[ "$output" == *"program"* ]]
    [[ "$output" == *"NUM"* ]]
    [[ "$output" != *"predict"* ]]
}

@test "plcc-parse partial tree appears before error message" {
    cat > grammar.plcc << 'GRAMMAR'
token NUM '\d+'
token PLUS '\+'
skip WS '\s+'
%
<program> ::= <expr>
<expr> ::= NUM PLUS NUM
GRAMMAR
    run bash -c "cd '${WORK_DIR}' && echo '1 +' | plcc-parse"
    [ "$status" -ne 0 ]
    rule_line=$(echo "$output" | grep -n "^program$" | head -1 | cut -d: -f1)
    error_line=$(echo "$output" | grep -n "error:" | head -1 | cut -d: -f1)
    [ "$rule_line" -lt "$error_line" ]
}
```

- [ ] **Step 3: Run the bats tests**

```bash
bats tests/bats/commands/plcc-parse.bats
```

Expected: all tests pass (the three previously-failing failure-trace tests now pass; the five `--trace` tests are gone).

- [ ] **Step 4: Run the full functional suite**

```bash
bin/test/functional.bash
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tests/bats/commands/plcc-parse.bats
git commit -m "test(069): replace --trace bats tests with Style B trace tests"
```
