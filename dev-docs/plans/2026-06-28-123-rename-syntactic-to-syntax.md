# Rename syntactic → syntax in plcc-diagram-* Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace every occurrence of "syntactic" in the `plcc-diagram-*` command surface, output filenames, and Python module with "syntax".

**Architecture:** Clean-break rename across four layers — pyproject.toml entry points, Python source (module dir + two files), pytest unit tests, and bats command tests. No aliases. The entry point rename flows through a `pdm install` step that makes the new binary names available for bats tests to exercise.

**Tech Stack:** Python 3, PDM (package/install), pytest (unit tests), bats (command tests)

## Global Constraints

- No backward-compatibility aliases — this is an acknowledged breaking change
- All tests must pass before each commit
- Run `bin/test/units.bash` for unit tests; `bin/test/commands.bash` for bats tests
- Reinstall after any pyproject.toml or module path change: `pdm install`

---

### Task 1: Update unit tests and source to use "syntax"

**Files:**
- Modify: `src/plcc/diagram/syntactic_diagram/diagram_test.py`
- Modify: `src/plcc/diagram/syntactic_diagram/diagram.py`
- Modify: `src/plcc/diagram/syntactic_diagram/plantuml/emit.py`
- Modify: `pyproject.toml`
- Rename: `src/plcc/diagram/syntactic_diagram/` → `src/plcc/diagram/syntax_diagram/`

**Interfaces:**
- Produces: `plcc-diagram-syntax` and `plcc-diagram-syntax-plantuml-emit` entry points; module at `plcc.diagram.syntax_diagram`

- [ ] **Step 1: Update unit tests to assert new names (they will fail)**

  In `src/plcc/diagram/syntactic_diagram/diagram_test.py`, make these changes:

  Rename the two test functions:
  ```python
  # old
  def test_emit_called_with_type_syntactic(tmp_path, monkeypatch):
  # new
  def test_emit_called_with_type_syntax(tmp_path, monkeypatch):
  ```
  ```python
  # old
  def test_build_uses_syntactic_paths(tmp_path, monkeypatch):
  # new
  def test_build_uses_syntax_paths(tmp_path, monkeypatch):
  ```

  Update the three assertions in those functions:
  ```python
  # old
  assert '--type=syntactic' in emit_call
  # new
  assert '--type=syntax' in emit_call
  ```
  ```python
  # old
  assert '--input=build/diagram/syntactic.puml' in build_call
  assert '--output=build/diagram/syntactic.png' in build_call
  # new
  assert '--input=build/diagram/syntax.puml' in build_call
  assert '--output=build/diagram/syntax.png' in build_call
  ```

- [ ] **Step 2: Run unit tests to confirm they fail**

  ```bash
  bin/test/units.bash src/plcc/diagram/syntactic_diagram/diagram_test.py -v
  ```
  Expected: 2 tests FAIL (`test_emit_called_with_type_syntax`, `test_build_uses_syntax_paths`)

- [ ] **Step 3: Update diagram.py — docstring and command name strings**

  Replace the `__doc__` block (lines 15–26) in `src/plcc/diagram/syntactic_diagram/diagram.py`:
  ```python
  __doc__ = """plcc-diagram-syntax
      Generate and display a syntax grammar diagram from a PLCC spec file.

  Usage:
      plcc-diagram-syntax [-v ...] [options]

  Options:
  """ + SPEC_OPTION + """\
      --format=FMT            Diagram format [default: plantuml].
      -b --banner             Show the version and spec banner on stderr.
      -h --help               Show this message.
  """ + VERBOSE_OPTIONS
  ```

  Replace all remaining "syntactic" string literals in `diagram.py`:
  ```python
  # line 45 — old
  print("Run 'plcc-diagram-syntactic --help' for more information.", file=sys.stderr)
  # new
  print("Run 'plcc-diagram-syntax --help' for more information.", file=sys.stderr)
  ```
  ```python
  # line 51 — old
  validate_spec_flag('plcc-diagram-syntactic', args)
  # new
  validate_spec_flag('plcc-diagram-syntax', args)
  ```
  ```python
  # line 55 — old
  print(f"plcc-diagram-syntactic: spec file not found: {spec_path}", file=sys.stderr)
  # new
  print(f"plcc-diagram-syntax: spec file not found: {spec_path}", file=sys.stderr)
  ```
  ```python
  # line 57 — old
  print("Run 'plcc-diagram-syntactic --help' for more information.", file=sys.stderr)
  # new
  print("Run 'plcc-diagram-syntax --help' for more information.", file=sys.stderr)
  ```
  ```python
  # line 62 — old
  verbose = VerboseContext.from_args("plcc-diagram-syntactic", Events, args)
  verbose.emit(Events.STARTED, message="generating syntactic diagram")
  # new
  verbose = VerboseContext.from_args("plcc-diagram-syntax", Events, args)
  verbose.emit(Events.STARTED, message="generating syntax diagram")
  ```
  ```python
  # lines 82–83 — old
  diagram_source = os.path.join(build_diagram_dir, f'syntactic.{source_ext}')
  diagram_image = os.path.join(build_diagram_dir, 'syntactic.png')
  # new
  diagram_source = os.path.join(build_diagram_dir, f'syntax.{source_ext}')
  diagram_image = os.path.join(build_diagram_dir, 'syntax.png')
  ```
  ```python
  # line 87 — old
  ['plcc-diagram-emit', '--type=syntactic', f'--format={fmt}'] + child_flags,
  # new
  ['plcc-diagram-emit', '--type=syntax', f'--format={fmt}'] + child_flags,
  ```

- [ ] **Step 4: Update plantuml/emit.py — docstring and command name strings**

  Replace the `__doc__` block (lines 9–16) in `src/plcc/diagram/syntactic_diagram/plantuml/emit.py`:
  ```python
  __doc__ = """plcc-diagram-syntax-plantuml-emit
      Emit a PlantUML EBNF diagram from spec JSON.

  Usage:
      plcc-diagram-syntax-plantuml-emit [-v ...] [options]

  Options:
      -h --help   Show this message.
  """ + VERBOSE_OPTIONS
  ```

  Replace the VerboseContext call (line 29):
  ```python
  # old
  VerboseContext.from_args("plcc-diagram-syntactic-plantuml-emit", Events, args)
  # new
  VerboseContext.from_args("plcc-diagram-syntax-plantuml-emit", Events, args)
  ```

- [ ] **Step 5: Rename the module directory**

  ```bash
  git mv src/plcc/diagram/syntactic_diagram src/plcc/diagram/syntax_diagram
  ```

- [ ] **Step 6: Update pyproject.toml entry points**

  Find the two syntactic entry points in `pyproject.toml` and update them:
  ```toml
  # old
  plcc-diagram-syntactic               = "plcc.diagram.syntactic_diagram.diagram:main"
  plcc-diagram-syntactic-plantuml-emit = "plcc.diagram.syntactic_diagram.plantuml.emit:main"
  # new
  plcc-diagram-syntax               = "plcc.diagram.syntax_diagram.diagram:main"
  plcc-diagram-syntax-plantuml-emit = "plcc.diagram.syntax_diagram.plantuml.emit:main"
  ```

- [ ] **Step 7: Reinstall the package**

  ```bash
  pdm install
  ```
  Expected: installs without error; `plcc-diagram-syntax` and `plcc-diagram-syntax-plantuml-emit` now appear on PATH.

- [ ] **Step 8: Run unit tests to confirm they pass**

  ```bash
  bin/test/units.bash src/plcc/diagram/syntax_diagram/ -v
  ```
  Expected: all tests PASS

- [ ] **Step 9: Commit**

  ```bash
  git add pyproject.toml \
    src/plcc/diagram/syntax_diagram/diagram.py \
    src/plcc/diagram/syntax_diagram/diagram_test.py \
    src/plcc/diagram/syntax_diagram/plantuml/emit.py
  git commit -m "refactor: rename plcc-diagram-syntactic to plcc-diagram-syntax (#123)"
  ```

---

### Task 2: Update bats tests and packaging test

**Files:**
- Rename: `tests/bats/commands/plcc-diagram-syntactic.bats` → `tests/bats/commands/plcc-diagram-syntax.bats`
- Rename: `tests/bats/commands/plcc-diagram-syntactic-plantuml-emit.bats` → `tests/bats/commands/plcc-diagram-syntax-plantuml-emit.bats`
- Modify: `tests/bats/commands/plcc-diagram-list.bats`
- Modify: `bin/test/packaging.bash`

**Interfaces:**
- Consumes: `plcc-diagram-syntax` and `plcc-diagram-syntax-plantuml-emit` binaries from Task 1

- [ ] **Step 1: Rename and update plcc-diagram-syntactic.bats**

  ```bash
  git mv tests/bats/commands/plcc-diagram-syntactic.bats \
         tests/bats/commands/plcc-diagram-syntax.bats
  ```

  Replace all content in `tests/bats/commands/plcc-diagram-syntax.bats`:
  ```bash
  #!/usr/bin/env bats

  bats_require_minimum_version 1.5.0

  @test "plcc-diagram-syntax is on PATH" { command -v plcc-diagram-syntax; }

  @test "plcc-diagram-syntax --help exits 0" {
      run plcc-diagram-syntax --help
      [ "$status" -eq 0 ]
  }

  @test "plcc-diagram-syntax fails when spec file not found" {
      run bash -c "cd /tmp && plcc-diagram-syntax --spec=nonexistent.plcc"
      [ "$status" -ne 0 ]
      [[ "$output" =~ "spec file not found" ]]
  }
  ```

- [ ] **Step 2: Rename and update plcc-diagram-syntactic-plantuml-emit.bats**

  ```bash
  git mv tests/bats/commands/plcc-diagram-syntactic-plantuml-emit.bats \
         tests/bats/commands/plcc-diagram-syntax-plantuml-emit.bats
  ```

  Replace all content in `tests/bats/commands/plcc-diagram-syntax-plantuml-emit.bats`:
  ```bash
  #!/usr/bin/env bats

  bats_require_minimum_version 1.5.0

  setup() {
      FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
  }

  @test "plcc-diagram-syntax-plantuml-emit is on PATH" {
      command -v plcc-diagram-syntax-plantuml-emit
  }

  @test "plcc-diagram-syntax-plantuml-emit --help exits 0" {
      run plcc-diagram-syntax-plantuml-emit --help
      [ "$status" -eq 0 ]
  }

  @test "emitter produces @startebnf output" {
      run bash -c "plcc-spec '${FIXTURES}/arith.plcc' | plcc-diagram-syntax-plantuml-emit"
      [ "$status" -eq 0 ]
      [[ "$output" =~ "@startebnf" ]]
      [[ "$output" =~ "@endebnf" ]]
  }

  @test "emitter output contains grammar rule names" {
      run bash -c "plcc-spec '${FIXTURES}/arith.plcc' | plcc-diagram-syntax-plantuml-emit"
      [ "$status" -eq 0 ]
      [[ "$output" =~ "Program" ]]
      [[ "$output" =~ "Expr" ]]
      [[ "$output" =~ "Term" ]]
  }

  @test "emitter output contains quoted terminal" {
      run bash -c "plcc-spec '${FIXTURES}/arith.plcc' | plcc-diagram-syntax-plantuml-emit"
      [ "$status" -eq 0 ]
      [[ "$output" =~ "'PLUS'" ]]
  }
  ```

- [ ] **Step 3: Update plcc-diagram-list.bats**

  In `tests/bats/commands/plcc-diagram-list.bats`, update the two lines that reference `syntactic/plantuml`:
  ```bash
  # old (line 18)
  @test "plcc-diagram-list finds syntactic/plantuml" {
  # new
  @test "plcc-diagram-list finds syntax/plantuml" {
  ```
  ```bash
  # old (line 21)
      [[ "$output" =~ "syntactic/plantuml" ]]
  # new
      [[ "$output" =~ "syntax/plantuml" ]]
  ```

- [ ] **Step 4: Update bin/test/packaging.bash**

  In `bin/test/packaging.bash`, update line 26:
  ```bash
  # old
               plcc-diagram-syntactic plcc-diagram-syntactic-plantuml-emit \
  # new
               plcc-diagram-syntax plcc-diagram-syntax-plantuml-emit \
  ```

  Update lines 45–46:
  ```bash
  # old
      echo "${DIAGRAM_LIST}" | grep -q "syntactic/plantuml" || { echo "FAIL: plcc-diagram-list missing 'syntactic/plantuml'"; exit 1; }
      echo "OK: plcc-diagram-list reports syntactic/plantuml"
  # new
      echo "${DIAGRAM_LIST}" | grep -q "syntax/plantuml" || { echo "FAIL: plcc-diagram-list missing 'syntax/plantuml'"; exit 1; }
      echo "OK: plcc-diagram-list reports syntax/plantuml"
  ```

- [ ] **Step 5: Run command tests to confirm all pass**

  ```bash
  bin/test/commands.bash
  ```
  Expected: all bats tests PASS, including the renamed files

- [ ] **Step 6: Commit**

  ```bash
  git add tests/bats/commands/plcc-diagram-syntax.bats \
    tests/bats/commands/plcc-diagram-syntax-plantuml-emit.bats \
    tests/bats/commands/plcc-diagram-list.bats \
    bin/test/packaging.bash
  git commit -m "test: update bats and packaging tests for syntactic→syntax rename (#123)"
  ```
