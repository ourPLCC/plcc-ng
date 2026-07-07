# Drop Mermaid Diagram Support — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove all Mermaid diagram code, entry points, tests, and documentation from plcc-ng in a single clean pass.

**Architecture:** Delete two source packages and one doc page; edit pyproject.toml, mkdocs.yml, two `diagram.py` orchestrators, three unit test files, one bats test file, and four user-facing doc pages to remove every Mermaid reference.

**Tech Stack:** Python, pytest, bats, pyproject.toml entry points, MkDocs nav

## Global Constraints

- Run `bin/test/units.bash` after every source change; run `bin/test/commands.bash` after removing entry points.
- Conventional commits: `refactor(diagram): …` for source/test changes, `docs: …` for doc-only changes.
- All commits include `[skip ci]` only for doc-only commits; source changes do not.

---

### Task 1: Delete Mermaid source packages and their unit tests

**Files:**
- Delete: `src/plcc/diagram/mermaid/` (entire directory)
- Delete: `src/plcc/diagram/class_diagram/mermaid/` (entire directory)

**Interfaces:**
- Produces: nothing — these packages are self-contained and not imported anywhere else

- [ ] **Step 1: Delete the packages**

```bash
rm -rf src/plcc/diagram/mermaid/
rm -rf src/plcc/diagram/class_diagram/mermaid/
```

- [ ] **Step 2: Verify unit tests still pass**

Run: `bin/test/units.bash`
Expected: all tests pass (the deleted tests are simply gone; no failures)

- [ ] **Step 3: Commit**

```bash
git add -A src/plcc/diagram/mermaid/ src/plcc/diagram/class_diagram/mermaid/
git commit -m "refactor(diagram): delete Mermaid source packages (#124)"
```

---

### Task 2: Remove Mermaid entry points from pyproject.toml

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: deleted packages from Task 1

- [ ] **Step 1: Remove the three entry points**

Open `pyproject.toml` and delete these three lines from `[project.scripts]`:

```toml
plcc-diagram-class-mermaid-emit = "plcc.diagram.class_diagram.mermaid.emit:main"
plcc-diagram-mermaid-build  = "plcc.diagram.mermaid.build:main"
plcc-diagram-mermaid-run    = "plcc.diagram.mermaid.run:main"
```

- [ ] **Step 2: Reinstall the package so the entry points are gone**

```bash
pdm install
```

- [ ] **Step 3: Verify the commands are no longer on PATH**

```bash
command -v plcc-diagram-mermaid-build && echo "FAIL: still exists" || echo "OK: gone"
command -v plcc-diagram-mermaid-run   && echo "FAIL: still exists" || echo "OK: gone"
command -v plcc-diagram-class-mermaid-emit && echo "FAIL: still exists" || echo "OK: gone"
```

Expected: all three print `OK: gone`

- [ ] **Step 4: Run packaging test to confirm entry points are clean**

```bash
bin/test/packaging.bash
```

Expected: passes (no missing entry point errors for the removed commands)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "refactor(diagram): remove Mermaid entry points from pyproject.toml (#124)"
```

---

### Task 3: Remove Mermaid from `_SOURCE_EXT` maps

**Files:**
- Modify: `src/plcc/diagram/class_diagram/diagram.py`
- Modify: `src/plcc/diagram/syntax_diagram/diagram.py`

**Interfaces:**
- Consumes: nothing new
- Produces: `_SOURCE_EXT` dicts that contain only `plantuml`

- [ ] **Step 1: Edit `class_diagram/diagram.py`**

Find this line (around line 32):

```python
_SOURCE_EXT = {'mermaid': 'mmd', 'plantuml': 'puml'}
```

Replace with:

```python
_SOURCE_EXT = {'plantuml': 'puml'}
```

- [ ] **Step 2: Edit `syntax_diagram/diagram.py`**

Find this line (around line 29):

```python
_SOURCE_EXT = {'plantuml': 'puml', 'mermaid': 'mmd'}
```

Replace with:

```python
_SOURCE_EXT = {'plantuml': 'puml'}
```

- [ ] **Step 3: Run unit tests**

Run: `bin/test/units.bash`
Expected: all tests pass

- [ ] **Step 4: Commit**

```bash
git add src/plcc/diagram/class_diagram/diagram.py src/plcc/diagram/syntax_diagram/diagram.py
git commit -m "refactor(diagram): remove mermaid from _SOURCE_EXT maps (#124)"
```

---

### Task 4: Remove Mermaid test cases from unit test files

**Files:**
- Modify: `src/plcc/diagram/build_test.py`
- Modify: `src/plcc/diagram/run_test.py`
- Modify: `src/plcc/diagram/list_test.py`

**Interfaces:**
- Consumes: nothing new

- [ ] **Step 1: Edit `build_test.py` — remove `test_custom_format_dispatches_correctly`**

Delete the entire `test_custom_format_dispatches_correctly` test function (the one that uses `--format=mermaid` and asserts `calls[0][0] == 'plcc-diagram-mermaid-build'`). The result should look like:

```python
import pytest
from unittest.mock import patch, MagicMock

from .build import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_dispatches_to_diagram_plantuml_build(tmp_path):
    src = tmp_path / "diagram.puml"
    src.write_text("@startuml\n@enduml\n")
    out = tmp_path / "diagram.png"
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-plantuml-build'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={src}', f'--output={out}'])

    assert calls[0][0] == 'plcc-diagram-plantuml-build'
    assert f'--input={src}' in calls[0]
    assert f'--output={out}' in calls[0]


def test_missing_plugin_exits_nonzero(tmp_path, capsys):
    src = tmp_path / "diagram.mmd"
    src.write_text("classDiagram\n")
    out = tmp_path / "diagram.png"

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={src}', f'--output={out}', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
```

- [ ] **Step 2: Edit `run_test.py` — remove `test_custom_format_dispatches_correctly`**

Delete the entire `test_custom_format_dispatches_correctly` test function (the one that uses `--format=mermaid` and asserts `calls[0][0] == 'plcc-diagram-mermaid-run'`). The result should look like:

```python
import pytest
from unittest.mock import patch, MagicMock

from .run import main as run_main


def test_missing_required_args_exits_nonzero():
    import docopt
    with pytest.raises((docopt.DocoptExit, SystemExit)):
        run_main([])


def test_dispatches_to_diagram_plantuml_run(tmp_path):
    img = tmp_path / "diagram.png"
    img.write_bytes(b'\x89PNG')
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        m = MagicMock()
        m.returncode = 0
        return m

    with patch('shutil.which', return_value='/usr/bin/plcc-diagram-plantuml-run'):
        with patch('subprocess.run', side_effect=fake_run):
            run_main([f'--input={img}'])

    assert calls[0][0] == 'plcc-diagram-plantuml-run'
    assert f'--input={img}' in calls[0]


def test_missing_plugin_exits_nonzero(tmp_path, capsys):
    img = tmp_path / "diagram.png"
    img.write_bytes(b'\x89PNG')

    with patch('shutil.which', return_value=None):
        with pytest.raises(SystemExit) as exc:
            run_main([f'--input={img}', '--format=nonexistent'])

    assert exc.value.code != 0
    _, err = capsys.readouterr()
    assert 'nonexistent' in err
```

- [ ] **Step 3: Edit `list_test.py` — remove the two Mermaid test cases and update the `test_main_prints_type_slash_format` fixture**

Delete `test_extract_type_format_mermaid` entirely, and update `test_main_prints_type_slash_format` to only include `class/plantuml`. The result should look like:

```python
from .list import extract_type_format, find_plugins, main


def test_extract_type_format_plantuml():
    assert extract_type_format('plcc-diagram-class-plantuml-emit') == ('class', 'plantuml')


def test_extract_ignores_dispatcher():
    assert extract_type_format('plcc-diagram-emit') is None


def test_extract_ignores_old_pattern():
    assert extract_type_format('plcc-plantuml-diagram-emit') is None


def test_extract_ignores_non_matching():
    assert extract_type_format('plcc-diagram-list') is None
    assert extract_type_format('python') is None


def test_main_prints_type_slash_format(capsys, monkeypatch):
    monkeypatch.setattr(
        'plcc.diagram.list.find_plugins',
        lambda: [('class', 'plantuml')]
    )
    main([])
    out, _ = capsys.readouterr()
    assert out.splitlines() == ['class/plantuml']
```

- [ ] **Step 4: Run unit tests**

Run: `bin/test/units.bash`
Expected: all tests pass

- [ ] **Step 5: Commit**

```bash
git add src/plcc/diagram/build_test.py src/plcc/diagram/run_test.py src/plcc/diagram/list_test.py
git commit -m "test(diagram): remove Mermaid test cases from unit tests (#124)"
```

---

### Task 5: Delete and update Mermaid bats tests

**Files:**
- Delete: `tests/bats/commands/plcc-diagram-class-mermaid-emit.bats`
- Delete: `tests/bats/commands/plcc-diagram-mermaid-build.bats`
- Delete: `tests/bats/commands/plcc-diagram-mermaid-run.bats`
- Modify: `tests/bats/commands/plcc-diagram-list.bats`

- [ ] **Step 1: Delete the three Mermaid bats test files**

```bash
rm tests/bats/commands/plcc-diagram-class-mermaid-emit.bats
rm tests/bats/commands/plcc-diagram-mermaid-build.bats
rm tests/bats/commands/plcc-diagram-mermaid-run.bats
```

- [ ] **Step 2: Remove the `class/mermaid` assertion from `plcc-diagram-list.bats`**

Delete the entire `@test "plcc-diagram-list finds class/mermaid"` block. The result should look like:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-list is on PATH" { command -v plcc-diagram-list; }

@test "plcc-diagram-list exits 0" {
    run plcc-diagram-list
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-list finds syntax/plantuml" {
    run plcc-diagram-list
    [ "$status" -eq 0 ]
    [[ "$output" =~ "syntax/plantuml" ]]
}
```

- [ ] **Step 3: Run commands tests**

Run: `bin/test/commands.bash`
Expected: all tests pass (no failures referencing removed commands)

- [ ] **Step 4: Commit**

```bash
git add -A tests/bats/commands/plcc-diagram-class-mermaid-emit.bats \
           tests/bats/commands/plcc-diagram-mermaid-build.bats \
           tests/bats/commands/plcc-diagram-mermaid-run.bats \
           tests/bats/commands/plcc-diagram-list.bats
git commit -m "test(diagram): remove Mermaid bats tests (#124)"
```

---

### Task 6: Remove Mermaid from user-facing docs and mkdocs.yml

**Files:**
- Modify: `mkdocs.yml`
- Delete: `docs/cli/commands/plcc-diagram-class-mermaid-emit.md`
- Modify: `docs/cli/guide/diagram-extensions.md`
- Modify: `docs/cli/guide/under-the-hood.md`
- Modify: `docs/cli/guide/author-commands.md`
- Modify: `docs/cli/commands/plcc-diagram-class.md`
- Modify: `docs/cli/commands/plcc-diagram-emit.md`
- Modify: `docs/cli/commands/plcc-diagram-list.md`

- [ ] **Step 1: Remove stale Mermaid nav entries from `mkdocs.yml`**

Delete these three lines (they reference old pre-#113 paths that never existed on disk):

```yaml
- plcc-mermaid-diagram-build: cli/commands/plcc-mermaid-diagram-build.md
- plcc-mermaid-diagram-emit: cli/commands/plcc-mermaid-diagram-emit.md
- plcc-mermaid-diagram-run: cli/commands/plcc-mermaid-diagram-run.md
```

- [ ] **Step 2: Delete the Mermaid command doc page**

```bash
rm docs/cli/commands/plcc-diagram-class-mermaid-emit.md
```

- [ ] **Step 3: Edit `docs/cli/guide/diagram-extensions.md`**

Remove the entire `## plcc-mermaid-diagram` section (the heading, the intro paragraph mentioning `npm install -g @mermaid-js/mermaid-cli`, the command table, and the usage example `plcc-diagram-class --format=mermaid`).

- [ ] **Step 4: Edit `docs/cli/guide/under-the-hood.md`**

Remove the `plcc-mermaid-diagram` package block from the PlantUML diagram (the `package plcc-mermaid-diagram { … }` block and its three arrow lines). Also remove the mention of `class/mermaid` in the `type/format` pair example sentence — change it to reference only `class/plantuml`.

- [ ] **Step 5: Edit `docs/cli/guide/author-commands.md`**

Remove the one reference to `class/mermaid` in the `type/format` pair example. Change the example to reference only `class/plantuml`.

- [ ] **Step 6: Edit `docs/cli/commands/plcc-diagram-class.md`**

Remove the line referencing `--format=mermaid` or `plcc-diagram-class --format=mermaid`.

- [ ] **Step 7: Edit `docs/cli/commands/plcc-diagram-emit.md`**

Remove the line: `plcc-spec spec.plcc | plcc-model | plcc-diagram-emit --type=class --format=mermaid`

- [ ] **Step 8: Edit `docs/cli/commands/plcc-diagram-list.md`**

Remove the `# class/mermaid` line from the example output.

- [ ] **Step 9: Verify no remaining Mermaid references in docs**

```bash
grep -rn "mermaid" docs/cli/ --include="*.md"
```

Expected: no output

- [ ] **Step 10: Commit**

```bash
git add mkdocs.yml \
        docs/cli/commands/plcc-diagram-class-mermaid-emit.md \
        docs/cli/guide/diagram-extensions.md \
        docs/cli/guide/under-the-hood.md \
        docs/cli/guide/author-commands.md \
        docs/cli/commands/plcc-diagram-class.md \
        docs/cli/commands/plcc-diagram-emit.md \
        docs/cli/commands/plcc-diagram-list.md
git commit -m "docs: remove Mermaid from user-facing docs and mkdocs nav (#124) [skip ci]"
```

---

### Task 7: Final verification and CHANGELOG

**Files:**
- Modify: `CHANGELOG.md` (semantic-release manages this; add a note in the PR description instead — see step below)

- [ ] **Step 1: Run full functional test suite**

```bash
bin/test/functional.bash
```

Expected: all tests pass

- [ ] **Step 2: Verify no Mermaid references remain in source or tests**

```bash
grep -rn "mermaid" src/ tests/ pyproject.toml mkdocs.yml --include="*.py" --include="*.bats" --include="*.toml" --include="*.yml" 2>/dev/null
```

Expected: no output

- [ ] **Step 3: Note breaking change for PR description**

The PR description must note: "`--format=mermaid` is no longer accepted. The commands `plcc-diagram-class-mermaid-emit`, `plcc-diagram-mermaid-build`, and `plcc-diagram-mermaid-run` have been removed. Use PlantUML (the default) instead."

The CHANGELOG entry will be auto-generated by semantic-release from the conventional commits above.
