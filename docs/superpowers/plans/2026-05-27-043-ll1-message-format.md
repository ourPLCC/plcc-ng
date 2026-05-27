# LL(1) Conflict Message Formatting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Drop the `see build/ll1.json` pointer from the LL(1) error header and add a blank line before each conflict block so the output is easy to scan.

**Architecture:** All changes are in `_report_ll1_failure` in `make.py`. The `format_conflict_message` function already produces correct internal formatting and is not touched. Two tasks: (1) drop the path parameter and fix the header, (2) add blank lines around conflict blocks.

**Tech Stack:** Python, pytest (`bin/test/units.bash`)

---

## File Map

| File | Action | What changes |
|------|--------|-------------|
| `src/plcc/cmd/make.py` | Modify | Remove `path` param from `_report_ll1_failure`; change header string; update call site; add blank-line prints |
| `src/plcc/cmd/make_test.py` | Modify | Update two existing tests (remove `path` arg, drop `ll1.json` assertion); add three new tests |

---

### Task 1: Drop the path parameter and fix the error header

**Files:**
- Modify: `src/plcc/cmd/make.py:131-132, 176-182`
- Modify: `src/plcc/cmd/make_test.py:72-109`

- [ ] **Step 1: Write the failing tests**

In `src/plcc/cmd/make_test.py`, make these changes:

*Update `test_report_ll1_failure_prints_error_and_conflicts`* — remove the `path` argument from the call and drop the `"build/ll1.json" in err` assertion:

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
    _report_ll1_failure(ll1)
    _, err = capsys.readouterr()
    assert "plcc-make: error:" in err
    assert "LL(1) conflict: <expr> on lookahead ID" in err
    assert "FIRST/FIRST" in err
```

*Update `test_report_left_recursion_cycle`* — remove the `path` argument:

```python
def test_report_left_recursion_cycle(capsys):
    ll1 = {
        "conflicts": [],
        "left_recursion": [{"cycle": ["A", "B", "A"]}],
    }
    _report_ll1_failure(ll1)
    _, err = capsys.readouterr()
    assert "A -> B -> A" in err
```

*Add `test_report_ll1_failure_no_path_in_header`* after the updated tests:

```python
def test_report_ll1_failure_no_path_in_header(capsys):
    ll1 = {"conflicts": [], "left_recursion": []}
    _report_ll1_failure(ll1)
    _, err = capsys.readouterr()
    assert "see" not in err
    assert "ll1.json" not in err
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd /workspaces/plcc-ng/.worktrees/043-ll1-message-format
bin/test/units.bash src/plcc/cmd/make_test.py -v -k "report_ll1"
```

Expected: failures because `_report_ll1_failure` still takes two arguments and still prints `see … ll1.json`.

- [ ] **Step 3: Implement — remove `path` and fix the header**

In `src/plcc/cmd/make.py`, change `_report_ll1_failure`:

```python
def _report_ll1_failure(ll1):
    print("plcc-make: error: grammar is not LL(1)", file=sys.stderr)
    for conflict in ll1.get("conflicts", []):
        print(format_conflict_message(conflict), file=sys.stderr)
    for entry in ll1.get("left_recursion", []):
        cycle = entry.get("cycle", [])
        print(f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}", file=sys.stderr)
```

And update the call site at line 132:

```python
        if not ll1.get("is_ll1", True):
            _report_ll1_failure(ll1)
            sys.exit(1)
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py -v -k "report_ll1"
```

Expected: all three test functions pass (the two updated ones and the new one).

- [ ] **Step 5: Run the full unit suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git commit -m "fix(make): drop 'see ll1.json' from LL(1) error header"
```

---

### Task 2: Add a blank line before each conflict block

**Files:**
- Modify: `src/plcc/cmd/make.py:_report_ll1_failure`
- Modify: `src/plcc/cmd/make_test.py`

- [ ] **Step 1: Write the failing tests**

Add these two tests to `src/plcc/cmd/make_test.py`:

```python
def test_report_ll1_failure_blank_line_before_conflict(capsys):
    ll1 = {
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
    _report_ll1_failure(ll1)
    _, err = capsys.readouterr()
    # Header line ends with \n; a blank line means \n\n before the conflict header
    assert "grammar is not LL(1)\n\nLL(1) conflict:" in err


def test_report_ll1_failure_blank_line_between_conflicts(capsys):
    conflict = {
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
    ll1 = {"conflicts": [conflict, conflict], "left_recursion": []}
    _report_ll1_failure(ll1)
    _, err = capsys.readouterr()
    # The second conflict block must be preceded by a blank line
    # format_conflict_message ends without a trailing newline; print() adds one.
    # A blank separator means the last line of block 1, then \n\n, then LL(1) conflict:.
    blocks = err.split("\n\nLL(1) conflict:")
    assert len(blocks) == 3  # header + conflict1 + conflict2
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py -v -k "blank_line"
```

Expected: both tests fail because no blank lines are printed between blocks yet.

- [ ] **Step 3: Implement — add blank line before each conflict**

In `src/plcc/cmd/make.py`, update `_report_ll1_failure`:

```python
def _report_ll1_failure(ll1):
    print("plcc-make: error: grammar is not LL(1)", file=sys.stderr)
    for conflict in ll1.get("conflicts", []):
        print("", file=sys.stderr)
        print(format_conflict_message(conflict), file=sys.stderr)
    for entry in ll1.get("left_recursion", []):
        cycle = entry.get("cycle", [])
        print(f"plcc-make: error: left-recursion cycle: {' -> '.join(cycle)}", file=sys.stderr)
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
bin/test/units.bash src/plcc/cmd/make_test.py -v -k "blank_line"
```

Expected: both new tests pass.

- [ ] **Step 5: Run the full unit suite to check for regressions**

```bash
bin/test/units.bash
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git commit -m "fix(make): blank line before each LL(1) conflict block"
```
