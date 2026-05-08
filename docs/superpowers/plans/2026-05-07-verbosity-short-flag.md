# Verbosity Short Flag Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `--verbose=LEVEL` with the conventional `-v` / `-vv` / `-vvv` counting flag across all 22 PLCC CLIs.

**Architecture:** All changes flow from one place: `verbose.py` holds `VERBOSE_OPTIONS` (shared help text), `from_args` (parses the flag), and `child_flags` / `child_flags_for_orchestrator` (re-emits the flag to child processes). Each of the 22 CLIs needs one additional word in its `Usage:` line so docopt-ng knows to count `-v` instead of treating it as a boolean.

**Tech Stack:** Python, docopt-ng 0.9.0, pytest, bats

---

### Task 1: Update `verbose_test.py` to expect the `-v` interface (RED)

**Files:**
- Modify: `src/plcc/verbose_test.py`

docopt-ng returns an `int` for counted options (e.g. `{"-v": 2}`), not a string. All hand-crafted args dicts and all assertions about `child_flags` output must change.

- [ ] **Step 1: Update `test_verbose_options_is_a_string`**

In `src/plcc/verbose_test.py`, change:
```python
def test_verbose_options_is_a_string():
    assert isinstance(VERBOSE_OPTIONS, str)
    assert "--verbose" in VERBOSE_OPTIONS
    assert "--verbose-format" in VERBOSE_OPTIONS
```
to:
```python
def test_verbose_options_is_a_string():
    assert isinstance(VERBOSE_OPTIONS, str)
    assert "-v" in VERBOSE_OPTIONS
    assert "--verbose-format" in VERBOSE_OPTIONS
```

- [ ] **Step 2: Update all `from_args` args dicts**

Change every occurrence of `{"--verbose": "<N>", ...}` to `{"-v": <N>, ...}` (int, not string). Full list of functions and their replacements:

`test_from_args_defaults`: `{"--verbose": "0", "--verbose-format": "text"}` → `{"-v": 0, "--verbose-format": "text"}`

`test_from_args_with_values`: `{"--verbose": "2", "--verbose-format": "json"}` → `{"-v": 2, "--verbose-format": "json"}`

`test_emit_text_format`: `{"--verbose": "1", "--verbose-format": "text"}` → `{"-v": 1, "--verbose-format": "text"}`

`test_emit_json_format`: `{"--verbose": "1", "--verbose-format": "json"}` → `{"-v": 1, "--verbose-format": "json"}`

`test_emit_suppressed_when_level_too_low`: `{"--verbose": "0", "--verbose-format": "text"}` → `{"-v": 0, "--verbose-format": "text"}`

`test_child_flags_returns_unchanged`: `{"--verbose": "2", "--verbose-format": "text"}` → `{"-v": 2, "--verbose-format": "text"}`

`test_child_flags_for_orchestrator_forces_json`: `{"--verbose": "1", "--verbose-format": "text"}` → `{"-v": 1, "--verbose-format": "text"}`

`test_child_flags_for_orchestrator_keeps_higher_user_level`: `{"--verbose": "3", "--verbose-format": "text"}` → `{"-v": 3, "--verbose-format": "text"}`

`test_parse_child_events_roundtrip`: `{"--verbose": "1", "--verbose-format": "json"}` → `{"-v": 1, "--verbose-format": "json"}`

`test_reformat_child_events_to_text`: `{"--verbose": "1", "--verbose-format": "text"}` → `{"-v": 1, "--verbose-format": "text"}`

`test_parity_both_renderers_handle_all_events`: `{"--verbose": "1", "--verbose-format": fmt}` → `{"-v": 1, "--verbose-format": fmt}`

- [ ] **Step 3: Update `child_flags` assertions**

In `test_child_flags_returns_unchanged`, change:
```python
assert "--verbose=2" in flags
assert "--verbose-format=text" in flags
```
to:
```python
assert flags.count("-v") == 2
assert "--verbose-format=text" in flags
```

In `test_child_flags_for_orchestrator_forces_json`, change:
```python
assert "--verbose=2" in flags
assert "--verbose-format=json" in flags
```
to:
```python
assert flags.count("-v") == 2
assert "--verbose-format=json" in flags
```

In `test_child_flags_for_orchestrator_keeps_higher_user_level`, change:
```python
assert "--verbose=3" in flags
```
to:
```python
assert flags.count("-v") == 3
```

- [ ] **Step 4: Run the unit tests — expect failures**

```bash
bin/test/units.bash src/plcc/verbose_test.py -v
```
Expected: several FAILED (the tests now call `from_args` with `"-v"` keys but the implementation still reads `"--verbose"`).

---

### Task 2: Update `verbose.py` to make the tests pass (GREEN)

**Files:**
- Modify: `src/plcc/verbose.py`

- [ ] **Step 1: Replace `VERBOSE_OPTIONS`**

Change:
```python
VERBOSE_OPTIONS = """
    --verbose=LEVEL         Verbosity level 0-3 [default: 0].
    --verbose-format=FMT    Output format: text or json [default: text].
"""
```
to:
```python
VERBOSE_OPTIONS = """
    -v                      Increase verbosity (may repeat: -v, -vv, -vvv for levels 1-3).
    --verbose-format=FMT    Output format: text or json [default: text].
"""
```

- [ ] **Step 2: Update `from_args`**

Change:
```python
level = int(args.get("--verbose") or 0)
```
to:
```python
level = int(args.get("-v") or 0)
```

- [ ] **Step 3: Update `child_flags`**

Change:
```python
def child_flags(self):
    return [f"--verbose={self.level}", f"--verbose-format={self.fmt}"]
```
to:
```python
def child_flags(self):
    return ["-v"] * self.level + [f"--verbose-format={self.fmt}"]
```

- [ ] **Step 4: Update `child_flags_for_orchestrator`**

Change:
```python
def child_flags_for_orchestrator(self, min_level=None):
    level = max(self.level, min_level or 0)
    return [f"--verbose={level}", "--verbose-format=json"]
```
to:
```python
def child_flags_for_orchestrator(self, min_level=None):
    level = max(self.level, min_level or 0)
    return ["-v"] * level + ["--verbose-format=json"]
```

- [ ] **Step 5: Run the unit tests — expect all passing**

```bash
bin/test/units.bash src/plcc/verbose_test.py -v
```
Expected: all PASSED.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/verbose.py src/plcc/verbose_test.py
git commit -m "feat: replace --verbose=LEVEL with -v counting flag in verbose.py"
```

---

### Task 3: Add `[-v ...]` to all 22 CLI usage lines

**Files:** 22 CLI source files (listed below)

docopt-ng only counts repeated occurrences of a short flag when `[-v ...]` appears in the `Usage:` line. The `...` is what triggers counting behaviour. Without it, `-v` is parsed as a boolean.

The pattern is: add `[-v ...]` as the first optional element in each usage line — before `[options]` if present, or before required positional arguments.

- [ ] **Step 1: Update `src/plcc/cmd/scan.py`**

Change: `plcc-scan [options] GRAMMAR [SOURCE ...]`
To: `plcc-scan [-v ...] [options] GRAMMAR [SOURCE ...]`

- [ ] **Step 2: Update `src/plcc/cmd/parse.py`**

Change: `plcc-parse [options] GRAMMAR [SOURCE ...]`
To: `plcc-parse [-v ...] [options] GRAMMAR [SOURCE ...]`

- [ ] **Step 3: Update `src/plcc/cmd/make.py`**

Change: `plcc-make [options] GRAMMAR`
To: `plcc-make [-v ...] [options] GRAMMAR`

- [ ] **Step 4: Update `src/plcc/cmd/rep.py`**

Change: `plcc-rep [options] GRAMMAR [SOURCE ...]`
To: `plcc-rep [-v ...] [options] GRAMMAR [SOURCE ...]`

- [ ] **Step 5: Update `src/plcc/tokens/tokens_cli.py`**

Change: `plcc-tokens [options] SPEC_JSON [SOURCE ...]`
To: `plcc-tokens [-v ...] [options] SPEC_JSON [SOURCE ...]`

- [ ] **Step 6: Update `src/plcc/model/model_cli.py`**

Change: `plcc-model [options] [SPEC_JSON]`
To: `plcc-model [-v ...] [options] [SPEC_JSON]`

- [ ] **Step 7: Update `src/plcc/ll1/ll1_cli.py`**

Change: `plcc-ll1 [options]`
To: `plcc-ll1 [-v ...] [options]`

- [ ] **Step 8: Update `src/plcc/tree/tree_cli.py`**

Change: `plcc-tree [options] --ll1=LL1_JSON`
To: `plcc-tree [-v ...] [options] --ll1=LL1_JSON`

- [ ] **Step 9: Update `src/plcc/spec/plcc_spec_cli.py`**

Change: `plcc-spec [options] FILE`
To: `plcc-spec [-v ...] [options] FILE`

- [ ] **Step 10: Update `src/plcc/parser/list_cli.py`**

Change: `plcc-parser-list [options]`
To: `plcc-parser-list [-v ...] [options]`

- [ ] **Step 11: Update `src/plcc/parser/table_cli.py`**

Change: `plcc-parser-table [options] --ll1=LL1_JSON`
To: `plcc-parser-table [-v ...] [options] --ll1=LL1_JSON`

- [ ] **Step 12: Update `src/plcc/diagram/list.py`**

Change: `plcc-diagram-list [options]`
To: `plcc-diagram-list [-v ...] [options]`

- [ ] **Step 13: Update `src/plcc/diagram/plantuml/emit.py`**

Change: `plcc-plantuml-diagram --output=DIR [options]`
To: `plcc-plantuml-diagram --output=DIR [-v ...] [options]`

- [ ] **Step 14: Update `src/plcc/lang/emit.py`**

Change: `plcc-lang-emit [options] --target=LANG --output=DIR`
To: `plcc-lang-emit [-v ...] [options] --target=LANG --output=DIR`

- [ ] **Step 15: Update `src/plcc/diagram/dispatch.py`**

Change: `plcc-diagram --output=DIR [options]`
To: `plcc-diagram --output=DIR [-v ...] [options]`

- [ ] **Step 16: Update `src/plcc/lang/build.py`**

Change: `plcc-lang-build [options] --target=LANG --output=DIR`
To: `plcc-lang-build [-v ...] [options] --target=LANG --output=DIR`

- [ ] **Step 17: Update `src/plcc/lang/list.py`**

Change: `plcc-lang-list [options]`
To: `plcc-lang-list [-v ...] [options]`

- [ ] **Step 18: Update `src/plcc/lang/run.py`**

Change: `plcc-lang-run --target=LANG --output=DIR [options]`
To: `plcc-lang-run --target=LANG --output=DIR [-v ...] [options]`

- [ ] **Step 19: Update `src/plcc/lang/ext/java/emit.py`**

Change: `plcc-java-emit --output=DIR [options]`
To: `plcc-java-emit --output=DIR [-v ...] [options]`

- [ ] **Step 20: Update `src/plcc/lang/ext/java/build.py`**

Change: `plcc-java-build --output=DIR [options]`
To: `plcc-java-build --output=DIR [-v ...] [options]`

- [ ] **Step 21: Update `src/plcc/lang/ext/java/run.py`**

Change: `plcc-java-run --output=DIR [options]`
To: `plcc-java-run --output=DIR [-v ...] [options]`

- [ ] **Step 22: Update `src/plcc/lang/ext/python/emit.py`**

Change: `plcc-python-emit --output=DIR [options]`
To: `plcc-python-emit --output=DIR [-v ...] [options]`

- [ ] **Step 23: Update `src/plcc/lang/ext/python/run.py`**

Change: `plcc-python-run --output=DIR [options]`
To: `plcc-python-run --output=DIR [-v ...] [options]`

- [ ] **Step 24: Run all unit tests**

```bash
bin/test/units.bash -v
```
Expected: all PASSED.

- [ ] **Step 25: Commit**

```bash
git add src/plcc/cmd/scan.py src/plcc/cmd/parse.py src/plcc/cmd/make.py src/plcc/cmd/rep.py \
        src/plcc/tokens/tokens_cli.py src/plcc/model/model_cli.py src/plcc/ll1/ll1_cli.py \
        src/plcc/tree/tree_cli.py src/plcc/spec/plcc_spec_cli.py \
        src/plcc/parser/list_cli.py src/plcc/parser/table_cli.py \
        src/plcc/diagram/list.py src/plcc/diagram/plantuml/emit.py \
        src/plcc/diagram/dispatch.py src/plcc/lang/emit.py src/plcc/lang/build.py \
        src/plcc/lang/list.py src/plcc/lang/run.py \
        src/plcc/lang/ext/java/emit.py src/plcc/lang/ext/java/build.py \
        src/plcc/lang/ext/java/run.py src/plcc/lang/ext/python/emit.py \
        src/plcc/lang/ext/python/run.py
git commit -m "feat: add [-v ...] to all CLI usage lines for docopt-ng counting"
```

---

### Task 4: Update CLI unit tests

**Files:**
- Modify: `src/plcc/ll1/ll1_cli_test.py`
- Modify: `src/plcc/lang/ext/java/emit_test.py`

- [ ] **Step 1: Update `ll1_cli_test.py`**

In `src/plcc/ll1/ll1_cli_test.py`, make these three changes:

`test_verbose_started_emitted` (line 74):
```python
# Before:
run_main(["--verbose=1", "--verbose-format=json"])
# After:
run_main(["-v", "--verbose-format=json"])
```

`test_verbose_finished_emitted` (line 82):
```python
# Before:
run_main(["--verbose=1", "--verbose-format=json"])
# After:
run_main(["-v", "--verbose-format=json"])
```

`test_verbose_level2_first_set_events` (line 90):
```python
# Before:
run_main(["--verbose=2", "--verbose-format=json"])
# After:
run_main(["-vv", "--verbose-format=json"])
```

- [ ] **Step 2: Update `emit_test.py`**

In `src/plcc/lang/ext/java/emit_test.py` at line 180, change:
```python
run_main([f'--output={tmp_path}', '--verbose=1'])
```
to:
```python
run_main([f'--output={tmp_path}', '-v'])
```

- [ ] **Step 3: Run the affected test files**

```bash
bin/test/units.bash src/plcc/ll1/ll1_cli_test.py src/plcc/lang/ext/java/emit_test.py -v
```
Expected: all PASSED.

- [ ] **Step 4: Commit**

```bash
git add src/plcc/ll1/ll1_cli_test.py src/plcc/lang/ext/java/emit_test.py
git commit -m "test: update CLI unit tests to use -v flag"
```

---

### Task 5: Update bats command tests

**Files:**
- Modify: `tests/bats/commands/plcc-scan.bats`
- Modify: `tests/bats/commands/plcc-parse.bats`
- Modify: `tests/bats/commands/plcc-make.bats`
- Modify: `tests/bats/commands/plcc-rep.bats`
- Modify: `tests/bats/commands/plcc-ll1.bats`
- Modify: `tests/bats/commands/plcc-tree.bats`
- Modify: `tests/bats/commands/plcc-parser-list.bats`
- Modify: `tests/bats/commands/plcc-parser-table.bats`
- Modify: `tests/bats/commands/plcc-java-emit.bats`
- Modify: `tests/bats/commands/plcc-python-emit.bats`

The pattern for each file: replace `--verbose=1` with `-v` and rename the surrounding test description from `"... accepts --verbose ..."` to `"... accepts -v ..."`. `--verbose-format` is unchanged.

- [ ] **Step 1: Update `plcc-scan.bats`**

```bash
# Before:
@test "plcc-scan accepts --verbose" {
    run bash -c "echo '42' | plcc-scan --verbose=1 '${FIXTURES}/trivial.plcc'"
# After:
@test "plcc-scan accepts -v" {
    run bash -c "echo '42' | plcc-scan -v '${FIXTURES}/trivial.plcc'"
```

- [ ] **Step 2: Update `plcc-parse.bats`**

```bash
# Before:
@test "plcc-parse accepts --verbose" {
    run bash -c "echo '42' | plcc-parse --verbose=1 '${FIXTURES}/trivial.plcc'"
# After:
@test "plcc-parse accepts -v" {
    run bash -c "echo '42' | plcc-parse -v '${FIXTURES}/trivial.plcc'"
```

- [ ] **Step 3: Update `plcc-make.bats`**

```bash
# Before:
@test "plcc-make accepts --verbose" {
    run plcc-make --verbose=1 "${FIXTURES}/trivial-python.plcc"
# After:
@test "plcc-make accepts -v" {
    run plcc-make -v "${FIXTURES}/trivial-python.plcc"
```

- [ ] **Step 4: Update `plcc-rep.bats`**

```bash
# Before:
@test "plcc-rep accepts --verbose" {
    run bash -c "echo '42' | plcc-rep --tool=py --verbose=1 '${FIXTURES}/trivial-python.plcc'"
# After:
@test "plcc-rep accepts -v" {
    run bash -c "echo '42' | plcc-rep --tool=py -v '${FIXTURES}/trivial-python.plcc'"
```

- [ ] **Step 5: Update `plcc-ll1.bats`**

```bash
# Before (two tests):
@test "plcc-ll1 accepts --verbose without error" {
    run bash -c "plcc-ll1 --verbose=1 < '${SPEC_JSON}'"

@test "plcc-ll1 accepts --verbose-format without error" {
    run bash -c "plcc-ll1 --verbose=1 --verbose-format=json < '${SPEC_JSON}'"

# After:
@test "plcc-ll1 accepts -v without error" {
    run bash -c "plcc-ll1 -v < '${SPEC_JSON}'"

@test "plcc-ll1 accepts --verbose-format without error" {
    run bash -c "plcc-ll1 -v --verbose-format=json < '${SPEC_JSON}'"
```

- [ ] **Step 6: Update `plcc-tree.bats`**

```bash
# Before:
@test "plcc-tree accepts --verbose without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}' --verbose=1"
# After:
@test "plcc-tree accepts -v without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}' -v"
```

- [ ] **Step 7: Update `plcc-parser-list.bats`**

```bash
# Before (two tests):
@test "plcc-parser-list accepts --verbose" {
    run plcc-parser-list --verbose=1

@test "plcc-parser-list accepts --verbose-format" {
    run plcc-parser-list --verbose=1 --verbose-format=json

# After:
@test "plcc-parser-list accepts -v" {
    run plcc-parser-list -v

@test "plcc-parser-list accepts --verbose-format" {
    run plcc-parser-list -v --verbose-format=json
```

- [ ] **Step 8: Update `plcc-parser-table.bats`**

```bash
# Before (two tests):
@test "plcc-parser-table accepts --verbose without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' --verbose=1"

@test "plcc-parser-table accepts --verbose-format without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' --verbose=1 --verbose-format=json"

# After:
@test "plcc-parser-table accepts -v without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' -v"

@test "plcc-parser-table accepts --verbose-format without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' -v --verbose-format=json"
```

- [ ] **Step 9: Update `plcc-java-emit.bats`**

```bash
# Before:
@test "plcc-java-emit accepts --verbose" {
    run bash -c "plcc-java-emit --output='${WORK_DIR}' --verbose=1 < '${MODEL_JSON}'"
# After:
@test "plcc-java-emit accepts -v" {
    run bash -c "plcc-java-emit --output='${WORK_DIR}' -v < '${MODEL_JSON}'"
```

- [ ] **Step 10: Update `plcc-python-emit.bats`**

```bash
# Before:
@test "plcc-python-emit accepts --verbose" {
    run bash -c "plcc-python-emit --output='${WORK_DIR}' --verbose=1 < '${MODEL_JSON}'"
# After:
@test "plcc-python-emit accepts -v" {
    run bash -c "plcc-python-emit --output='${WORK_DIR}' -v < '${MODEL_JSON}'"
```

- [ ] **Step 11: Run all command bats tests**

```bash
bin/test/commands.bash
```
Expected: all passing.

- [ ] **Step 12: Commit**

```bash
git add tests/bats/commands/plcc-scan.bats tests/bats/commands/plcc-parse.bats \
        tests/bats/commands/plcc-make.bats tests/bats/commands/plcc-rep.bats \
        tests/bats/commands/plcc-ll1.bats tests/bats/commands/plcc-tree.bats \
        tests/bats/commands/plcc-parser-list.bats tests/bats/commands/plcc-parser-table.bats \
        tests/bats/commands/plcc-java-emit.bats tests/bats/commands/plcc-python-emit.bats
git commit -m "test: update bats command tests to use -v flag"
```

---

### Task 6: Full verification

- [ ] **Step 1: Run the full functional test suite**

```bash
bin/test/functional.bash
```
Expected: all tiers (units, commands, integration, e2e) pass.

- [ ] **Step 2: Smoke-check help output**

```bash
plcc-scan --help
```
Expected: `-v` appears in the Options section; `--verbose` does not.

- [ ] **Step 3: Smoke-check counting behaviour**

```bash
plcc-scan -vv --verbose-format=json --help 2>/dev/null; echo exit=$?
```
Expected: exit=0 and `-v` visible in the help output; `--verbose` absent.
