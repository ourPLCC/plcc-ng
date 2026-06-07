# Rename --grammar-file to --grammar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the `--grammar-file` flag to `--grammar` (with short form `-g`) across all five commands that accept it, in a single clean commit.

**Architecture:** Pure rename across five source files and their tests. No behavioral change. All changes land in one commit on the `refactor-050-rename-grammar-file` worktree branch.

**Tech Stack:** Python / docopt, pytest, bats

---

### Task 1: Update source files — make.py, scan.py, parse.py, rep.py, diagram.py

**Files:**
- Modify: `src/plcc/cmd/make.py`
- Modify: `src/plcc/cmd/scan.py`
- Modify: `src/plcc/cmd/parse.py`
- Modify: `src/plcc/cmd/rep.py`
- Modify: `src/plcc/cmd/diagram.py`

In each file, three kinds of changes are needed:

1. The docopt option line: `--grammar-file=<path>` → `-g <path> --grammar=<path>`
2. The key lookup: `args['--grammar-file']` → `args['--grammar']`
3. Forwarded flag strings: `f'--grammar-file={grammar_file}'` → `f'--grammar={grammar_file}'`

One additional change in `make.py` only: an error message that tells users which flag to use.

- [ ] **Step 1: Update make.py**

  In `src/plcc/cmd/make.py`:

  Replace the docopt option line (lines 28–30):
  ```python
      --grammar-file=<path>   Grammar to build from. Once set, remembered for subsequent
                              commands until changed. Defaults to grammar.plcc on first use.
  ```
  with:
  ```python
      -g <path> --grammar=<path>
                              Grammar to build from. Once set, remembered for subsequent
                              commands until changed. Defaults to grammar.plcc on first use.
  ```

  Replace the key lookup (line 55):
  ```python
      explicit_grammar = args['--grammar-file']
  ```
  with:
  ```python
      explicit_grammar = args['--grammar']
  ```

  Replace the error message hint (line 80):
  ```python
              "use --grammar-file to specify a different one)",
  ```
  with:
  ```python
              "use --grammar to specify a different one)",
  ```

- [ ] **Step 2: Update scan.py**

  In `src/plcc/cmd/scan.py`:

  Replace the docopt option line (lines 32–33):
  ```python
      --grammar-file=<path>       Grammar to build from. Once set, remembered for subsequent
                                  commands until changed. Defaults to grammar.plcc on first use.
  ```
  with:
  ```python
      -g <path> --grammar=<path>  Grammar to build from. Once set, remembered for subsequent
                                  commands until changed. Defaults to grammar.plcc on first use.
  ```

  Replace the key lookup (line 136):
  ```python
      grammar_file = args["--grammar-file"]
  ```
  with:
  ```python
      grammar_file = args["--grammar"]
  ```

  Replace the forwarded flag (line 153):
  ```python
          + ([f'--grammar-file={grammar_file}'] if grammar_file is not None else [])
  ```
  with:
  ```python
          + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
  ```

- [ ] **Step 3: Update parse.py**

  In `src/plcc/cmd/parse.py`:

  Replace the docopt option line (lines 24–25):
  ```python
      --grammar-file=<path>       Grammar to build from. Once set, remembered for subsequent
                                  commands until changed. Defaults to grammar.plcc on first use.
  ```
  with:
  ```python
      -g <path> --grammar=<path>  Grammar to build from. Once set, remembered for subsequent
                                  commands until changed. Defaults to grammar.plcc on first use.
  ```

  Replace the key lookup (line 66):
  ```python
      grammar_file = args["--grammar-file"]
  ```
  with:
  ```python
      grammar_file = args["--grammar"]
  ```

  Replace the forwarded flag (line 83):
  ```python
          + ([f'--grammar-file={grammar_file}'] if grammar_file is not None else [])
  ```
  with:
  ```python
          + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
  ```

- [ ] **Step 4: Update rep.py**

  In `src/plcc/cmd/rep.py`:

  Replace the docopt option line (lines 24–25):
  ```python
      --grammar-file=<path>   Grammar to build from. Once set, remembered for subsequent
                              commands until changed. Defaults to grammar.plcc on first use.
  ```
  with:
  ```python
      -g <path> --grammar=<path>
                              Grammar to build from. Once set, remembered for subsequent
                              commands until changed. Defaults to grammar.plcc on first use.
  ```

  Replace the key lookup (line 73):
  ```python
      grammar_file = args['--grammar-file']
  ```
  with:
  ```python
      grammar_file = args['--grammar']
  ```

  Replace the forwarded flag (line 89):
  ```python
          + ([f'--grammar-file={grammar_file}'] if grammar_file is not None else [])
  ```
  with:
  ```python
          + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
  ```

- [ ] **Step 5: Update diagram.py**

  In `src/plcc/cmd/diagram.py`:

  Replace the docopt option line (lines 17–18):
  ```python
      --grammar-file=<path>   Grammar to build from. Once set, remembered for subsequent
                              commands until changed. Defaults to grammar.plcc on first use.
  ```
  with:
  ```python
      -g <path> --grammar=<path>
                              Grammar to build from. Once set, remembered for subsequent
                              commands until changed. Defaults to grammar.plcc on first use.
  ```

  Replace the key lookup (line 44):
  ```python
      grammar_file = args['--grammar-file']
  ```
  with:
  ```python
      grammar_file = args['--grammar']
  ```

  Replace the forwarded flag (line 58):
  ```python
          + ([f'--grammar-file={grammar_file}'] if grammar_file is not None else [])
  ```
  with:
  ```python
          + ([f'--grammar={grammar_file}'] if grammar_file is not None else [])
  ```

---

### Task 2: Update unit tests

**Files:**
- Modify: `src/plcc/cmd/make_test.py`
- Modify: `src/plcc/cmd/rep_test.py`

(`diagram_test.py` has no flag references — only prose "grammar file not found" assertions which stay unchanged.)

- [ ] **Step 1: Update make_test.py**

  Five changes in `src/plcc/cmd/make_test.py`:

  Line 33 — flag passed to `run_main`:
  ```python
          run_main(['--grammar-file=nonexistent.plcc'])
  ```
  →
  ```python
          run_main(['--grammar=nonexistent.plcc'])
  ```

  Line 219 — assertion on error message text:
  ```python
      assert "--grammar-file" in err
  ```
  →
  ```python
      assert "--grammar" in err
  ```

  Line 243 — flag passed to `run_main`:
  ```python
      run_main(["--grammar-file=new.plcc"])
  ```
  →
  ```python
      run_main(["--grammar=new.plcc"])
  ```

  Line 255 — flag passed to `run_main`:
  ```python
      run_main(["--grammar-file=same.plcc"])
  ```
  →
  ```python
      run_main(["--grammar=same.plcc"])
  ```

  Line 265 — flag passed to `run_main`:
  ```python
          run_main(["--grammar-file=bad.plcc"])
  ```
  →
  ```python
          run_main(["--grammar=bad.plcc"])
  ```

- [ ] **Step 2: Update rep_test.py**

  One change in `src/plcc/cmd/rep_test.py`:

  Line 49:
  ```python
      _rep_module.main(["--grammar-file=grammar.plcc", "--tool=calc"])
  ```
  →
  ```python
      _rep_module.main(["--grammar=grammar.plcc", "--tool=calc"])
  ```

---

### Task 3: Run unit tests

- [ ] **Step 1: Run unit tests and confirm they pass**

  From the worktree root (`.worktrees/refactor-050-rename-grammar-file`):
  ```bash
  bin/test/units.bash
  ```
  Expected: all tests pass. If any fail, the most likely cause is a missed `--grammar-file` reference — grep for it: `grep -rn 'grammar-file' src/`.

---

### Task 4: Update bats tests

**Files:**
- Modify: `tests/bats/commands/plcc-make.bats`
- Modify: `tests/bats/commands/plcc-scan.bats`
- Modify: `tests/bats/commands/plcc-parse.bats`
- Modify: `tests/bats/commands/plcc-rep.bats`
- Modify: `tests/bats/commands/plcc-diagram.bats`
- Modify: `tests/bats/integration/plcc-parse-errors.bats`
- Modify: `tests/bats/e2e/happy-path.bats`
- Modify: `tests/bats/e2e/plcc-rep.bats`

- [ ] **Step 1: Update plcc-make.bats**

  Seven changes in `tests/bats/commands/plcc-make.bats`:

  Line 31:
  ```bash
      run --separate-stderr plcc-make --grammar-file=no-such-file.plcc
  ```
  →
  ```bash
      run --separate-stderr plcc-make --grammar=no-such-file.plcc
  ```

  Line 44:
  ```bash
      run plcc-make --through=scan "--grammar-file=${FIXTURES}/trivial.plcc"
  ```
  →
  ```bash
      run plcc-make --through=scan "--grammar=${FIXTURES}/trivial.plcc"
  ```

  Line 208:
  ```bash
      run plcc-make --through=scan "--grammar-file=${FIXTURES}/trivial.plcc"
  ```
  →
  ```bash
      run plcc-make --through=scan "--grammar=${FIXTURES}/trivial.plcc"
  ```

  Line 216:
  ```bash
      run plcc-make --through=scan "--grammar-file=${FIXTURES}/trivial.plcc"
  ```
  →
  ```bash
      run plcc-make --through=scan "--grammar=${FIXTURES}/trivial.plcc"
  ```

  Line 229:
  ```bash
      plcc-make --through=scan --grammar-file=other.plcc
  ```
  →
  ```bash
      plcc-make --through=scan --grammar=other.plcc
  ```

  Line 241 — assertion on error message text:
  ```bash
      [[ "$stderr" == *"--grammar-file"* ]]
  ```
  →
  ```bash
      [[ "$stderr" == *"--grammar"* ]]
  ```

  Line 252:
  ```bash
      run plcc-make --grammar-file=bad.plcc
  ```
  →
  ```bash
      run plcc-make --grammar=bad.plcc
  ```

- [ ] **Step 2: Update plcc-scan.bats**

  One change in `tests/bats/commands/plcc-scan.bats`:

  Line 104:
  ```bash
      run bash -c "echo '42' | plcc-scan --grammar-file='${FIXTURES}/trivial.plcc'"
  ```
  →
  ```bash
      run bash -c "echo '42' | plcc-scan --grammar='${FIXTURES}/trivial.plcc'"
  ```

- [ ] **Step 3: Update plcc-parse.bats**

  One change in `tests/bats/commands/plcc-parse.bats`:

  Line 59:
  ```bash
      run bash -c "echo '42' | plcc-parse --grammar-file='${FIXTURES}/trivial.plcc'"
  ```
  →
  ```bash
      run bash -c "echo '42' | plcc-parse --grammar='${FIXTURES}/trivial.plcc'"
  ```

- [ ] **Step 4: Update plcc-rep.bats (commands)**

  One change in `tests/bats/commands/plcc-rep.bats`:

  Line 46:
  ```bash
      run --separate-stderr bash -c "echo '42' | plcc-rep --grammar-file='${FIXTURES}/trivial-python.plcc' --tool=py"
  ```
  →
  ```bash
      run --separate-stderr bash -c "echo '42' | plcc-rep --grammar='${FIXTURES}/trivial-python.plcc' --tool=py"
  ```

- [ ] **Step 5: Update plcc-diagram.bats**

  One change in `tests/bats/commands/plcc-diagram.bats`:

  Line 13:
  ```bash
      run bash -c "cd /tmp && plcc-diagram --grammar-file=nonexistent.plcc"
  ```
  →
  ```bash
      run bash -c "cd /tmp && plcc-diagram --grammar=nonexistent.plcc"
  ```

- [ ] **Step 6: Update plcc-parse-errors.bats (integration)**

  One change in `tests/bats/integration/plcc-parse-errors.bats`:

  Line 14:
  ```bash
      run --separate-stderr bash -c "echo 'abc' | plcc-parse --grammar-file='$tmp/trivial.plcc'"
  ```
  →
  ```bash
      run --separate-stderr bash -c "echo 'abc' | plcc-parse --grammar='$tmp/trivial.plcc'"
  ```

- [ ] **Step 7: Update happy-path.bats (e2e)**

  Three changes in `tests/bats/e2e/happy-path.bats`:

  Line 9 (setup):
  ```bash
      plcc-make --grammar-file="${FIXTURES}/trivial.plcc"
  ```
  →
  ```bash
      plcc-make --grammar="${FIXTURES}/trivial.plcc"
  ```

  Line 39:
  ```bash
      run plcc-make --grammar-file="${WORK_DIR}/grammar2.plcc"
  ```
  →
  ```bash
      run plcc-make --grammar="${WORK_DIR}/grammar2.plcc"
  ```

  Line 70:
  ```bash
          plcc-make --grammar-file="${FIXTURES}/trivial-full.plcc"
  ```
  →
  ```bash
          plcc-make --grammar="${FIXTURES}/trivial-full.plcc"
  ```

- [ ] **Step 8: Update plcc-rep.bats (e2e)**

  Replace all `--grammar-file=` occurrences in `tests/bats/e2e/plcc-rep.bats` with `--grammar=`.
  Lines affected: 30, 37, 43, 50, 56, 66, 89, 96, 103.

  Run this to verify the count before and after:
  ```bash
  grep -c 'grammar-file' tests/bats/e2e/plcc-rep.bats
  ```
  Expected before: 9. Expected after: 0.

---

### Task 5: Run all test tiers and commit

- [ ] **Step 1: Confirm no stray references remain**

  ```bash
  grep -rn 'grammar-file' src/ tests/
  ```
  Expected: no output. If any lines appear, fix them before continuing.

- [ ] **Step 2: Run unit tests**

  ```bash
  bin/test/units.bash
  ```
  Expected: all pass.

- [ ] **Step 3: Run command tests**

  ```bash
  bin/test/commands.bash
  ```
  Expected: all pass.

- [ ] **Step 4: Run integration tests**

  ```bash
  bin/test/integration.bash
  ```
  Expected: all pass.

- [ ] **Step 5: Run e2e tests**

  ```bash
  bin/test/e2e.bash
  ```
  Expected: all pass.

- [ ] **Step 6: Commit**

  ```bash
  git add src/plcc/cmd/make.py src/plcc/cmd/scan.py src/plcc/cmd/parse.py \
          src/plcc/cmd/rep.py src/plcc/cmd/diagram.py \
          src/plcc/cmd/make_test.py src/plcc/cmd/rep_test.py \
          tests/bats/commands/plcc-make.bats tests/bats/commands/plcc-scan.bats \
          tests/bats/commands/plcc-parse.bats tests/bats/commands/plcc-rep.bats \
          tests/bats/commands/plcc-diagram.bats \
          tests/bats/integration/plcc-parse-errors.bats \
          tests/bats/e2e/happy-path.bats tests/bats/e2e/plcc-rep.bats
  git commit -m "refactor: rename --grammar-file to --grammar / -g in all commands (issue 050)"
  ```
