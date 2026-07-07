# Rename `build/` Output Directory to `plcc-ng/` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the plcc-ng output directory from `build/` to `plcc-ng/` everywhere in source, tests, and docs.

**Architecture:** Add `OUTPUT_DIR = 'plcc-ng'` to `src/plcc/build/__init__.py` as the single source of truth, then update all hardcoded `'build'` / `"build"` directory references in source files to import and use that constant; update pytest and bats tests to match; update user-facing docs.

**Tech Stack:** Python, pytest, bats

## Global Constraints

- TDD: update tests to expect `plcc-ng/` before updating source; confirm the test fails; then fix the source; confirm it passes.
- Run tests with `bin/test/units.bash` (fast, seconds).
- Run bats tests with `bin/test/commands.bash` or `bin/test/e2e.bash`.
- Commit after each task with `[skip ci]` only if the task is docs-only; otherwise use a normal commit.
- Do NOT change `src/plcc/cmd/diagram.py:28` — the `'build'` in `_RESERVED = frozenset({'emit', 'build', 'run', 'list'})` is a subcommand verb, not a directory.
- Do NOT change `docs/superpowers/plans/` or `docs/superpowers/specs/` — frozen historical records.

---

### Task 1: Add the OUTPUT_DIR constant

**Files:**
- Modify: `src/plcc/build/__init__.py`

**Interfaces:**
- Produces: `OUTPUT_DIR: str` — importable as `from plcc.build import OUTPUT_DIR`

- [ ] **Step 1: Add the constant**

Replace the entire contents of `src/plcc/build/__init__.py` with:

```python
OUTPUT_DIR = 'plcc-ng'
```

- [ ] **Step 2: Verify all existing tests still pass**

```bash
bin/test/units.bash
```

Expected: all tests pass (no callers changed yet).

- [ ] **Step 3: Commit**

```bash
git add src/plcc/build/__init__.py
git commit -m "feat(125): add OUTPUT_DIR constant to plcc.build"
```

---

### Task 2: Update `make.py` — the orchestrator

**Files:**
- Modify: `src/plcc/cmd/make.py:18,60`
- Modify: `src/plcc/cmd/make_test.py` (5 occurrences of `tmp_path / "build"`)

**Interfaces:**
- Consumes: `OUTPUT_DIR` from `plcc.build` (Task 1)

- [ ] **Step 1: Update `make_test.py` to expect `plcc-ng/`**

In `src/plcc/cmd/make_test.py`, replace every occurrence of:
```python
tmp_path / "build"
```
with:
```python
tmp_path / "plcc-ng"
```

There are 5 occurrences (lines ~198, 213, 226, 238, 250). After this change the tests that create the directory as a fixture will set up `plcc-ng/` but `make.py` still looks for `build/` — so those tests will fail.

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash 2>&1 | grep -E "FAILED|PASSED|ERROR" | head -20
```

Expected: several tests in `make_test.py` now fail because `make.py` still reads from `build/`.

- [ ] **Step 3: Update `make.py`**

Add `OUTPUT_DIR` to the import at line 18. Change:
```python
from plcc.build.spec import read_spec, write_spec, resolve_spec_path
```
to:
```python
from plcc.build import OUTPUT_DIR
from plcc.build.spec import read_spec, write_spec, resolve_spec_path
```

Change line 60:
```python
    build_dir = Path('build')
```
to:
```python
    build_dir = Path(OUTPUT_DIR)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
bin/test/units.bash
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/make.py src/plcc/cmd/make_test.py
git commit -m "feat(125): update plcc-make to write output to plcc-ng/"
```

---

### Task 3: Update `scan.py`, `parse.py`, `rep.py`

**Files:**
- Modify: `src/plcc/cmd/scan.py:12,204,206`
- Modify: `src/plcc/cmd/parse.py:10,97,99,100`
- Modify: `src/plcc/cmd/rep.py:12,100,101,115,118`
- Modify: `src/plcc/cmd/scan_test.py` (3 occurrences of `tmp_path / "build"`)
- Modify: `src/plcc/cmd/parse_test.py` (1 occurrence of `tmp_path / "build"`)
- Modify: `src/plcc/cmd/rep_test.py` (2 occurrences of `tmp_path / "build"`)

**Interfaces:**
- Consumes: `OUTPUT_DIR` from `plcc.build` (Task 1)

#### scan.py

- [ ] **Step 1: Update `scan_test.py` to expect `plcc-ng/`**

In `src/plcc/cmd/scan_test.py`, replace every occurrence of:
```python
tmp_path / "build"
```
with:
```python
tmp_path / "plcc-ng"
```

There are 3 occurrences (~lines 97, 122, 136).

- [ ] **Step 2: Run to confirm scan tests fail**

```bash
bin/test/units.bash 2>&1 | grep "scan_test" | head -10
```

Expected: scan_test failures.

- [ ] **Step 3: Update `scan.py`**

Add import after the existing `from plcc.build.spec import read_spec` line (line 12):

```python
from plcc.build import OUTPUT_DIR
from plcc.build.spec import read_spec
```

Change line 204:
```python
        print_banner(get_version(), os.path.abspath(read_spec("build")))
```
to:
```python
        print_banner(get_version(), os.path.abspath(read_spec(OUTPUT_DIR)))
```

Change line 206:
```python
    spec_path = os.path.join("build", "spec.json")
```
to:
```python
    spec_path = os.path.join(OUTPUT_DIR, "spec.json")
```

#### parse.py

- [ ] **Step 4: Update `parse_test.py` to expect `plcc-ng/`**

In `src/plcc/cmd/parse_test.py`, replace every occurrence of:
```python
tmp_path / "build"
```
with:
```python
tmp_path / "plcc-ng"
```

There is 1 occurrence (~line 228).

- [ ] **Step 5: Run to confirm parse tests fail**

```bash
bin/test/units.bash 2>&1 | grep "parse_test" | head -10
```

Expected: parse_test failures.

- [ ] **Step 6: Update `parse.py`**

Add import after the existing `from plcc.build.spec import read_spec` line (line 10):

```python
from plcc.build import OUTPUT_DIR
from plcc.build.spec import read_spec
```

Change line 97:
```python
        print_banner(get_version(), os.path.abspath(read_spec("build")))
```
to:
```python
        print_banner(get_version(), os.path.abspath(read_spec(OUTPUT_DIR)))
```

Change line 99:
```python
    spec_path = os.path.join("build", "spec.json")
```
to:
```python
    spec_path = os.path.join(OUTPUT_DIR, "spec.json")
```

Change line 100:
```python
    ll1_path = os.path.join("build", "ll1.json")
```
to:
```python
    ll1_path = os.path.join(OUTPUT_DIR, "ll1.json")
```

#### rep.py

- [ ] **Step 7: Update `rep_test.py` to expect `plcc-ng/`**

In `src/plcc/cmd/rep_test.py`, replace every occurrence of:
```python
tmp_path / "build"
```
with:
```python
tmp_path / "plcc-ng"
```

There are 2 occurrences (~lines 23, 407).

- [ ] **Step 8: Run to confirm rep tests fail**

```bash
bin/test/units.bash 2>&1 | grep "rep_test" | head -10
```

Expected: rep_test failures.

- [ ] **Step 9: Update `rep.py`**

Add import after the existing `from plcc.build.spec import read_spec` line (line 12):

```python
from plcc.build import OUTPUT_DIR
from plcc.build.spec import read_spec
```

Change line 100:
```python
    spec_path = os.path.join('build', 'spec.json')
```
to:
```python
    spec_path = os.path.join(OUTPUT_DIR, 'spec.json')
```

Change line 101:
```python
    ll1_path = os.path.join('build', 'll1.json')
```
to:
```python
    ll1_path = os.path.join(OUTPUT_DIR, 'll1.json')
```

Change line 115:
```python
            os.path.abspath(read_spec('build')),
```
to:
```python
            os.path.abspath(read_spec(OUTPUT_DIR)),
```

Change line 118:
```python
    output_dir = os.path.join('build', language)
```
to:
```python
    output_dir = os.path.join(OUTPUT_DIR, language)
```

- [ ] **Step 10: Run all unit tests to confirm everything passes**

```bash
bin/test/units.bash
```

Expected: all tests pass.

- [ ] **Step 11: Commit**

```bash
git add src/plcc/cmd/scan.py src/plcc/cmd/scan_test.py \
        src/plcc/cmd/parse.py src/plcc/cmd/parse_test.py \
        src/plcc/cmd/rep.py src/plcc/cmd/rep_test.py
git commit -m "feat(125): update plcc-scan, plcc-parse, plcc-rep to read from plcc-ng/"
```

---

### Task 4: Update diagram files

**Files:**
- Modify: `src/plcc/diagram/class_diagram/diagram.py:1-14,71,74,78`
- Modify: `src/plcc/diagram/syntax_diagram/diagram.py:1-13,53,80`
- Modify: `src/plcc/diagram/class_diagram/diagram_test.py` (3 × `tmp_path / 'build'`, 2 path assertions)
- Modify: `src/plcc/diagram/syntax_diagram/diagram_test.py` (2 path assertions)

**Interfaces:**
- Consumes: `OUTPUT_DIR` from `plcc.build` (Task 1)

- [ ] **Step 1: Update `class_diagram/diagram_test.py` to expect `plcc-ng/`**

In `src/plcc/diagram/class_diagram/diagram_test.py`:

Replace every occurrence of:
```python
tmp_path / 'build'
```
with:
```python
tmp_path / 'plcc-ng'
```

There are 3 occurrences (~lines 47, 74, 99).

Also change the path assertions in `test_build_uses_class_puml_path`:
```python
    assert '--input=build/diagram/class.puml' in build_call
    assert '--output=build/diagram/class.png' in build_call
```
to:
```python
    assert '--input=plcc-ng/diagram/class.puml' in build_call
    assert '--output=plcc-ng/diagram/class.png' in build_call
```

- [ ] **Step 2: Update `syntax_diagram/diagram_test.py` to expect `plcc-ng/`**

In `src/plcc/diagram/syntax_diagram/diagram_test.py`, change the path assertions in `test_build_uses_syntax_paths`:
```python
    assert '--input=build/diagram/syntax.puml' in build_call
    assert '--output=build/diagram/syntax.png' in build_call
```
to:
```python
    assert '--input=plcc-ng/diagram/syntax.puml' in build_call
    assert '--output=plcc-ng/diagram/syntax.png' in build_call
```

- [ ] **Step 3: Run to confirm diagram tests fail**

```bash
bin/test/units.bash 2>&1 | grep "diagram" | head -20
```

Expected: class_diagram and syntax_diagram test failures.

- [ ] **Step 4: Update `class_diagram/diagram.py`**

Add `OUTPUT_DIR` to imports. After the existing `from plcc.build.spec import read_spec` line (line 11):

```python
from plcc.build import OUTPUT_DIR
from plcc.build.spec import read_spec
```

Change line 71:
```python
        print_banner(get_version(), os.path.abspath(read_spec('build')))
```
to:
```python
        print_banner(get_version(), os.path.abspath(read_spec(OUTPUT_DIR)))
```

Change line 74:
```python
    build_diagram_dir = os.path.join('build', 'diagram')
```
to:
```python
    build_diagram_dir = os.path.join(OUTPUT_DIR, 'diagram')
```

Change line 78:
```python
    model_json = os.path.join('build', 'model.json')
```
to:
```python
    model_json = os.path.join(OUTPUT_DIR, 'model.json')
```

- [ ] **Step 5: Update `syntax_diagram/diagram.py`**

Add `OUTPUT_DIR` to imports. After the existing `from plcc.build.spec import read_spec, resolve_spec_path` line (line 11):

```python
from plcc.build import OUTPUT_DIR
from plcc.build.spec import read_spec, resolve_spec_path
```

Change line 53:
```python
    spec_path = resolve_spec_path(args['--spec'], read_spec('build'))
```
to:
```python
    spec_path = resolve_spec_path(args['--spec'], read_spec(OUTPUT_DIR))
```

Change line 80:
```python
    build_diagram_dir = os.path.join('build', 'diagram')
```
to:
```python
    build_diagram_dir = os.path.join(OUTPUT_DIR, 'diagram')
```

- [ ] **Step 6: Run all unit tests to confirm they pass**

```bash
bin/test/units.bash
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/plcc/diagram/class_diagram/diagram.py \
        src/plcc/diagram/class_diagram/diagram_test.py \
        src/plcc/diagram/syntax_diagram/diagram.py \
        src/plcc/diagram/syntax_diagram/diagram_test.py
git commit -m "feat(125): update diagram commands to write to plcc-ng/"
```

---

### Task 5: Update bats tests

Bats tests exercise the installed CLI — they are the black-box contract tests. By this point all source is updated; only the expected paths in the test scripts need to change.

**Files:**
- Modify: `tests/bats/commands/plcc-make.bats` (~30 occurrences)
- Modify: `tests/bats/e2e/happy-path.bats` (2 occurrences)
- Modify: `tests/bats/e2e/plcc-rep.bats` (~14 occurrences)

**Interfaces:**
- Consumes: updated source from Tasks 2–4 (already committed)

- [ ] **Step 1: Update `plcc-make.bats`**

In `tests/bats/commands/plcc-make.bats`, replace every occurrence of `build/` with `plcc-ng/` and every occurrence of `build/.` with `plcc-ng/.`. Use a global search-and-replace.

Quick check before editing — verify the count:
```bash
grep -c "build" tests/bats/commands/plcc-make.bats
```

Then replace. The pattern to change: any shell path referencing the output directory, e.g.:
- `build/spec.json` → `plcc-ng/spec.json`
- `build/ll1.json` → `plcc-ng/ll1.json`
- `build/model.json` → `plcc-ng/model.json`
- `build/.spec` → `plcc-ng/.spec`
- `build/.spec-hash` → `plcc-ng/.spec-hash`
- `build/` (bare references) → `plcc-ng/`

Do NOT change any comment that describes behavior conceptually — only the shell path strings.

- [ ] **Step 2: Update `happy-path.bats`**

In `tests/bats/e2e/happy-path.bats`, replace:
- `build/spec.json` → `plcc-ng/spec.json`
- `build/model.json` → `plcc-ng/model.json`

These appear in test names and file path assertions (~lines 20, 28).

- [ ] **Step 3: Update `plcc-rep.bats`**

In `tests/bats/e2e/plcc-rep.bats`, replace every `build/` path with `plcc-ng/`. These appear in `setup_*` functions and test body assertions (~14 occurrences).

Patterns to change:
- `mkdir -p build` → `mkdir -p plcc-ng`
- `> build/spec.json` → `> plcc-ng/spec.json`
- `> build/ll1.json` → `> plcc-ng/ll1.json`
- `plcc-model build/spec.json` → `plcc-model plcc-ng/spec.json`
- `--output=build/Python` → `--output=plcc-ng/Python`
- `build/Python` path references → `plcc-ng/Python`
- `[ -d build/Python ]` etc. → `[ -d plcc-ng/Python ]`

- [ ] **Step 4: Run command and e2e bats tests**

```bash
bin/test/commands.bash
bin/test/e2e.bash
```

Expected: all bats tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/bats/commands/plcc-make.bats \
        tests/bats/e2e/happy-path.bats \
        tests/bats/e2e/plcc-rep.bats
git commit -m "test(125): update bats tests to expect plcc-ng/ output directory"
```

---

### Task 6: Update user-facing docs and CHANGELOG

**Files:**
- Modify: `docs/cli/commands/plcc-make.md`
- Modify: `docs/cli/commands/plcc-ll1.md`
- Modify: `docs/cli/commands/plcc-trees.md`
- Modify: `docs/cli/commands/plcc-model.md`
- Modify: `docs/cli/commands/plcc-tokens.md`
- Modify: `docs/cli/commands/plcc-parser-table.md`
- Modify: `docs/migration.md`
- Modify: `CHANGELOG.md`

**Interfaces:** None — docs only.

- [ ] **Step 1: Update `plcc-make.md`**

In `docs/cli/commands/plcc-make.md`, change:

```
`plcc-make` caches its output in `build/` and skips stages whose inputs
```
to:
```
`plcc-make` caches its output in `plcc-ng/` and skips stages whose inputs
```

- [ ] **Step 2: Update command docs with shell examples**

In each file below, replace every `build/` path in shell code examples with `plcc-ng/`:

`docs/cli/commands/plcc-ll1.md`:
```bash
plcc-spec spec.plcc | plcc-ll1 > build/ll1.json
```
→
```bash
plcc-spec spec.plcc | plcc-ll1 > plcc-ng/ll1.json
```

`docs/cli/commands/plcc-trees.md`:
```bash
plcc-spec spec.plcc > build/spec.json
plcc-spec spec.plcc | plcc-ll1 > build/ll1.json
plcc-tokens build/spec.json samples/ | plcc-trees --ll1=build/ll1.json
```
→
```bash
plcc-spec spec.plcc > plcc-ng/spec.json
plcc-spec spec.plcc | plcc-ll1 > plcc-ng/ll1.json
plcc-tokens plcc-ng/spec.json samples/ | plcc-trees --ll1=plcc-ng/ll1.json
```

`docs/cli/commands/plcc-model.md`:
```bash
plcc-model build/spec.json
```
→
```bash
plcc-model plcc-ng/spec.json
```

`docs/cli/commands/plcc-tokens.md`:
```bash
plcc-spec spec.plcc > build/spec.json
plcc-tokens build/spec.json samples/
```
→
```bash
plcc-spec spec.plcc > plcc-ng/spec.json
plcc-tokens plcc-ng/spec.json samples/
```

`docs/cli/commands/plcc-parser-table.md`:
```bash
plcc-spec spec.plcc | plcc-ll1 > build/ll1.json
plcc-tokens build/spec.json samples/ | plcc-parser-table --ll1=build/ll1.json
```
→
```bash
plcc-spec spec.plcc | plcc-ll1 > plcc-ng/ll1.json
plcc-tokens plcc-ng/spec.json samples/ | plcc-parser-table --ll1=plcc-ng/ll1.json
```

- [ ] **Step 3: Update `docs/migration.md`**

In `docs/migration.md`, replace every `build/` path in shell examples with `plcc-ng/` (3 occurrences around the pipeline examples).

- [ ] **Step 4: Add CHANGELOG breaking change entry**

In `CHANGELOG.md`, find the most recent `## v...` heading and add a `### Breaking Changes` section immediately below the heading (before the first existing subsection):

```markdown
### Breaking Changes

- The output directory has been renamed from `build/` to `plcc-ng/`. Update any
  `.gitignore` entries, scripts, or tooling that reference the old path.
```

- [ ] **Step 5: Commit**

```bash
git add docs/cli/commands/plcc-make.md \
        docs/cli/commands/plcc-ll1.md \
        docs/cli/commands/plcc-trees.md \
        docs/cli/commands/plcc-model.md \
        docs/cli/commands/plcc-tokens.md \
        docs/cli/commands/plcc-parser-table.md \
        docs/migration.md \
        CHANGELOG.md
git commit -m "docs(125): rename build/ to plcc-ng/ in user-facing docs and CHANGELOG [skip ci]"
```

---

## Self-Review

**Spec coverage:**

| Spec requirement | Covered by |
| --- | --- |
| `OUTPUT_DIR = 'plcc-ng'` constant in `plcc.build.__init__` | Task 1 |
| `make.py` updated | Task 2 |
| `scan.py`, `parse.py`, `rep.py` updated | Task 3 |
| `class_diagram/diagram.py`, `syntax_diagram/diagram.py` updated | Task 4 |
| Pytest tests updated | Tasks 2–4 |
| Bats tests updated | Task 5 |
| User-facing docs updated | Task 6 |
| CHANGELOG breaking change entry | Task 6 |
| `_RESERVED` in `diagram.py` left alone | Global Constraints |
| `docs/superpowers/plans/` left alone | Global Constraints |
| Clean cut (no migration) | No migration task — correct |

All spec requirements covered. ✓
