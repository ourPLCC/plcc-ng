# plcc-version Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `plcc-version` command that prints `plcc-ng <version>` to stdout and exits 0.

**Architecture:** A single package-level module `src/plcc/version.py` exposes `get_version()` (reads from `importlib.metadata`, falls back to `"unknown"`) and `main()` (prints and exits). One entry point is added to `pyproject.toml`. Unit tests cover `get_version()` and `main()`; a bats test covers the installed CLI contract.

**Tech Stack:** Python `importlib.metadata`, pytest (unit), bats (CLI contract), pdm (entry points).

---

### Task 1: Implement `src/plcc/version.py` with unit tests (TDD)

**Files:**
- Create: `src/plcc/version.py`
- Create: `src/plcc/version_test.py`

- [ ] **Step 1: Write the failing tests**

Create `src/plcc/version_test.py`:

```python
import sys
from unittest.mock import patch
from importlib.metadata import PackageNotFoundError

from plcc.version import get_version, main


def test_get_version_returns_string_from_metadata():
    with patch("plcc.version.importlib.metadata.version", return_value="1.2.3"):
        assert get_version() == "1.2.3"


def test_get_version_returns_unknown_when_not_found():
    with patch(
        "plcc.version.importlib.metadata.version",
        side_effect=PackageNotFoundError("plcc-ng"),
    ):
        assert get_version() == "unknown"


def test_main_prints_version_to_stdout(capsys):
    with patch("plcc.version.importlib.metadata.version", return_value="1.2.3"):
        main()
    captured = capsys.readouterr()
    assert captured.out == "plcc-ng 1.2.3\n"
    assert captured.err == ""
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
bin/test/units.bash src/plcc/version_test.py
```

Expected: 3 errors — `ModuleNotFoundError: No module named 'plcc.version'`

- [ ] **Step 3: Implement `src/plcc/version.py`**

Create `src/plcc/version.py`:

```python
import importlib.metadata
import sys
from importlib.metadata import PackageNotFoundError


def get_version() -> str:
    try:
        return importlib.metadata.version("plcc-ng")
    except PackageNotFoundError:
        return "unknown"


def main():
    print(f"plcc-ng {get_version()}")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
bin/test/units.bash src/plcc/version_test.py
```

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/plcc/version.py src/plcc/version_test.py
git commit -m "feat(version): add get_version and main to plcc.version"
```

---

### Task 2: Register `plcc-version` entry point

**Files:**
- Modify: `pyproject.toml` (add one line to `[project.scripts]`)

- [ ] **Step 1: Add the entry point**

In `pyproject.toml`, add this line to `[project.scripts]` (after `plcc-java-run` at line 82):

```toml
plcc-version = "plcc.version:main"
```

- [ ] **Step 2: Reinstall to register the entry point**

```bash
pdm install
```

Expected: no errors; `plcc-version` is now on PATH.

- [ ] **Step 3: Smoke-test the installed command**

```bash
plcc-version
```

Expected output (version will differ): `plcc-ng 0.22.1.dev9+g...`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "feat(version): register plcc-version entry point"
```

---

### Task 3: Add bats CLI contract test

**Files:**
- Create: `tests/bats/commands/plcc-version.bats`

- [ ] **Step 1: Write the bats test**

Create `tests/bats/commands/plcc-version.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-version is on PATH" {
    command -v plcc-version
}

@test "plcc-version exits 0" {
    run plcc-version
    [ "$status" -eq 0 ]
}

@test "plcc-version prints plcc-ng followed by a version string" {
    run plcc-version
    [[ "$output" =~ ^plcc-ng\ .+ ]]
}
```

- [ ] **Step 2: Run the bats test**

```bash
bats tests/bats/commands/plcc-version.bats
```

Expected: 3 passed

- [ ] **Step 3: Run the full commands suite to check for regressions**

```bash
bin/test/commands.bash
```

Expected: all tests pass (new tests included)

- [ ] **Step 4: Commit**

```bash
git add tests/bats/commands/plcc-version.bats
git commit -m "test(version): add bats CLI contract tests for plcc-version"
```

---

### Task 4: Move issue to done

**Files:**
- Move: `docs/issues/034-plcc-version-command.md` → `docs/issues/done/034-plcc-version-command.md`

- [ ] **Step 1: Move the issue file**

```bash
mv docs/issues/034-plcc-version-command.md docs/issues/done/034-plcc-version-command.md
```

- [ ] **Step 2: Commit**

```bash
git add docs/issues/034-plcc-version-command.md docs/issues/done/034-plcc-version-command.md
git commit -m "docs: close issue 034 (plcc-version) [skip ci]"
```
