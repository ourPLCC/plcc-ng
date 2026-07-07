# Phase 4: Packaging and First Release — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the plcc-scan/plcc-parse visualizers, rename the package to `plcc-ng`, wire up semantic-release CI, and ship the first public release on PyPI.

**Architecture:** Work progresses in four independent streams — (1) visualizer output polish in `src/plcc/cmd/`, (2) packaging metadata in `pyproject.toml` and `README.md`, (3) CI/release workflow files in `.github/workflows/`, and (4) one-time manual setup (Trusted Publishing, branch protection). The streams are independent and can be sequenced in any order; Task ordering below minimises review churn.

**Tech Stack:** Python, Bats, pdm-backend, python-semantic-release v9, PyPA Trusted Publishing (OIDC), GitHub Actions

---

## Phase 4 Entry Conditions

Before beginning, confirm all of the following are true:

- [ ] `tests/fixtures/languages-corpus.txt` has 29 grammars (GINGER included)
- [ ] `dev-docs/specs/2026-04-29-phase-3-java-emitter-design.md` has an `## 11. Phase 3 Retro` section
- [ ] This Phase 4 design doc (`dev-docs/specs/2026-05-01-phase-4-packaging-and-release-design.md`) is approved and committed
- [ ] `bin/test/functional.bash` passes locally with `LANGUAGES_REPO_PATH` set

---

## File Map

| File | Action | Purpose |
| ---- | ------ | ------- |
| `src/plcc/cmd/scan.py` | Modify | Location-aware token output; compiler-style error records |
| `tests/bats/commands/plcc-scan.bats` | Modify | Tests for new output format |
| `src/plcc/cmd/parse.py` | Modify | Location-aware token leaves in tree output; error record handling |
| `tests/bats/commands/plcc-parse.bats` | Modify | Tests for new output format |
| `pyproject.toml` | Modify | Rename to `plcc-ng`, fix license, add metadata, add `[tool.semantic_release]` |
| `README.md` | Modify | Fix typo, add install section and "what this is" paragraph |
| `src/plcc/lang/ext/plantuml/` | Delete | Empty stub — remove before packaging |
| `bin/test/packaging.bash` | Modify | Add `plcc-lang-list` and `plcc-diagram-list` checks |
| `tests/fixtures/languages-pin.txt` | Create | Pinned `languages` repo commit SHA for CI corpus run |
| `.github/workflows/ci.yml` | Replace | Three-job workflow (unit-and-integration, languages-corpus, packaging) |
| `.github/workflows/pypi.yaml` | Delete | Replaced by release.yml |
| `.github/workflows/release.yml` | Create | semantic-release + TestPyPI + PyPI publish |

---

## Task 1: plcc-scan location-aware output

**Files:**
- Modify: `tests/bats/commands/plcc-scan.bats`
- Modify: `src/plcc/cmd/scan.py`

### Background

`plcc-tokens` emits token records with a `source` object: `{"file": "<stdin>", "line": 1, "column": 1}`. The file is the string `"<stdin>"` when reading from a pipe. Since `plcc-scan` always pipes input to `plcc-tokens`, file is always `"<stdin>"`.

New token output format: `{line}:{col} {NAME} '{lexeme}'` (file prefix omitted when file is null or `"<stdin>"`).

New error record format: `{line}:{col}: error: {message}` (same omit logic).

Exit-code change: `plcc-scan` exits 0 even when `plcc-tokens` exits non-zero (lex error in source is an in-band event, not a tool failure). It exits non-zero only when `plcc-spec` fails (bad grammar file).

- [ ] **Step 1: Add failing tests for the new token output format**

Append to `tests/bats/commands/plcc-scan.bats`:

```bash
@test "plcc-scan includes line:col in token output" {
    run bash -c "echo '42' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ^1:1\ NUM\ \'42\'$ ]]
}

@test "plcc-scan exits 0 on lex error in source" {
    run bash -c "echo 'abc' | plcc-scan '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
}
```

- [ ] **Step 2: Run the new tests and confirm they fail**

```bash
bin/test/commands.bash 2>&1 | grep -A2 "line:col\|exits 0 on lex"
```

Expected: FAIL — output currently shows `NUM '42'` without location.

- [ ] **Step 3: Update `src/plcc/cmd/scan.py` — add `_location_str` and update the output loop**

Replace the token/error printing section (the `for line in result.stdout...` loop and the `if result.returncode != 0` block after plcc-tokens) with:

```python
        if result.returncode != 0:
            # lex error: plcc-tokens already emitted the error to stderr via verbose;
            # treat as non-fatal — pipeline completed with an error in-band
            pass
        else:
            for line in result.stdout.decode("utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("kind") == "token":
                    name = record.get("name", "?")
                    lexeme = record.get("lexeme", "?")
                    source = record.get("source", {})
                    loc = _location_str(source)
                    print(f"{loc} {name} '{lexeme}'")
                elif record.get("kind") == "error":
                    source = record.get("source") or {}
                    loc = _location_str(source)
                    message = record.get("message", "unknown error")
                    print(f"{loc}: error: {message}")
```

Add this helper at module level (after the imports, before `main`):

```python
def _location_str(source):
    file = source.get("file")
    line = source.get("line", "?")
    col = source.get("column", "?")
    if file and file != "<stdin>":
        return f"{file}:{line}:{col}"
    return f"{line}:{col}"
```

- [ ] **Step 4: Run the tests and confirm they pass**

```bash
bin/test/commands.bash 2>&1 | grep -E "plcc-scan"
```

Expected: all plcc-scan tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/plcc/cmd/scan.py tests/bats/commands/plcc-scan.bats
git commit -m "feat(scan): add location-aware output and compiler-style error format"
```

---

## Task 2: plcc-parse location-aware tree output

**Files:**
- Modify: `tests/bats/commands/plcc-parse.bats`
- Modify: `src/plcc/cmd/parse.py`

### Background

Token leaves in the tree now show `{NAME} '{lexeme}' [{line}:{col}]`. Error records that come through the tree (passed through by `plcc-parser-table`) are formatted as `{line}:{col}: error: {message}`.

- [ ] **Step 1: Add failing tests for the new tree output format**

Append to `tests/bats/commands/plcc-parse.bats`:

```bash
@test "plcc-parse includes location on token leaves" {
    run bash -c "echo '42' | plcc-parse '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" =~ NUM\ \'42\'\ \[1:1\] ]]
}
```

- [ ] **Step 2: Run the new test and confirm it fails**

```bash
bin/test/commands.bash 2>&1 | grep -A2 "location on token"
```

Expected: FAIL — token leaves currently show `NUM '42'` without location.

- [ ] **Step 3: Add `_location_str` helper and update `_print_tree` in `src/plcc/cmd/parse.py`**

Add the helper at module level (after imports, before `main`):

```python
def _location_str(source):
    file = source.get("file")
    line = source.get("line", "?")
    col = source.get("column", "?")
    if file and file != "<stdin>":
        return f"{file}:{line}:{col}"
    return f"{line}:{col}"
```

Replace `_print_tree` entirely:

```python
def _print_tree(node, indent):
    prefix = "  " * indent
    kind = node.get("kind", "?")
    if kind == "tree":
        rule = node.get("rule", "?")
        print(f"{prefix}{rule}")
        for child in node.get("children", []):
            _print_tree(child, indent + 1)
    elif kind == "token":
        name = node.get("name", "?")
        lexeme = node.get("lexeme", "?")
        source = node.get("source", {})
        loc = _location_str(source)
        print(f"{prefix}{name} '{lexeme}' [{loc}]")
    elif kind == "error":
        source = node.get("source") or {}
        loc = _location_str(source)
        message = node.get("message", "unknown error")
        print(f"{prefix}{loc}: error: {message}")
```

- [ ] **Step 4: Run the tests and confirm they pass**

```bash
bin/test/commands.bash 2>&1 | grep -E "plcc-parse"
```

Expected: all plcc-parse tests pass.

- [ ] **Step 5: Run the full command + integration suite to check for regressions**

```bash
bin/test/commands.bash && bin/test/integration.bash
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/plcc/cmd/parse.py tests/bats/commands/plcc-parse.bats
git commit -m "feat(parse): add location-aware tree output and compiler-style error format"
```

---

## Task 3: Package rename and metadata

**Files:**
- Modify: `pyproject.toml`

Change `pyproject.toml` to rename the package to `plcc-ng`, fix the license, add full PyPI metadata, and configure `python-semantic-release` in tag-only mode.

- [ ] **Step 1: Update `[project]` section of `pyproject.toml`**

Replace the entire `[project]` section (keep everything else):

```toml
[project]
name = "plcc-ng"
dynamic = ["version"]
description = "Programming Languages Compiler Compiler — experimental rewrite of PLCC"
authors = [
    {name = "PLCC Community", email = "https://discord.gg/EVtNSxS9E2"},
]
dependencies = [
    "docopt-ng>=0.9.0",
    "jinja2>=3.1.0",
]
requires-python = ">=3.12"
readme = "README.md"
license = {text = "AGPL-3.0-or-later"}
keywords = ["compiler", "parser", "education", "plcc", "teaching", "programming-languages"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Education",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Compilers",
    "Topic :: Education",
]

[project.urls]
Homepage = "https://github.com/ourorg/plcc-ng"
Repository = "https://github.com/ourorg/plcc-ng"
Issues = "https://github.com/ourorg/plcc-ng/issues"
```

> **Note:** Replace `ourorg/plcc-ng` above with the actual GitHub org/repo path (e.g. `StoneyJackson/plcc-ng`). Run `git remote get-url origin` if unsure.

- [ ] **Step 2: Add `python-semantic-release` dev dependency**

In the `[dependency-groups]` `dev` list, add:

```toml
    "python-semantic-release>=9.0.0",
    "twine>=5.0.0",
```

- [ ] **Step 3: Add `[tool.semantic_release]` config at the bottom of `pyproject.toml`**

```toml
[tool.semantic_release]
tag_format = "v{version}"
version_variables = []
version_toml = []
major_on_zero = false
```

`version_variables = []` and `version_toml = []` prevent PSR from committing version changes to any file (tag-only mode). `major_on_zero = false` prevents a breaking change from auto-promoting 0.x to 1.0.

- [ ] **Step 4: Install and verify the metadata**

```bash
pdm install
pdm build
.venv/bin/twine check dist/*.whl
```

Expected: `PASSED` for both checks. If README fails, fix the markdown issue and re-run.

- [ ] **Step 5: Verify non-Python package data is present in the wheel**

```bash
unzip -l dist/*.whl | grep -E "org\.json.*\.jar|\.jinja|\.schema\.json"
```

Expected: lines for `org.json-20250107.jar`, `.jinja` templates, and `.schema.json` files. If any are missing, pdm-backend didn't pick them up from git tracking. Fix by adding explicit `[tool.pdm.build.package-data]` entries to `pyproject.toml`:

```toml
[tool.pdm.build.package-data]
"plcc.lang.ext.java.runtime" = ["*.jar", "*.java"]
"plcc.lang.ext.java.templates" = ["*.jinja"]
"plcc.lang.ext.python.runtime" = ["*.py"]
"plcc.diagram.plantuml.templates" = ["*.jinja"]
"plcc.schemas" = ["*.json"]
```

Then rebuild and re-run `twine check`.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml
git commit -m "chore(packaging): rename to plcc-ng, fix license, add PyPI metadata and semantic-release config"
```

---

## Task 4: README polish

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Fix the typo "Licnesing" → "Licensing", add install section, add "what this is" paragraph**

Open `README.md`. Make three changes:

1. Fix the heading typo: `## Licnesing` → `## Licensing`

2. Add after the opening paragraph, before `## Licensing`:

```markdown
## Install

```bash
pip install plcc-ng
```

> This package has a separate identity from the original `plcc` package.
> `plcc-ng` is experimental — no compatibility guarantees with `plcc` until a stable 1.0 release.
```

3. (No other changes — README is intentionally minimal for now.)

- [ ] **Step 2: Verify README renders**

```bash
pdm build && .venv/bin/twine check dist/*.whl
```

Expected: `PASSED`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): fix typo, add install section and 'what this is' note"
```

---

## Task 5: Delete empty plantuml ext stub

**Files:**
- Delete: `src/plcc/lang/ext/plantuml/__init__.py` (and directory)

The `src/plcc/lang/ext/plantuml/` directory is an empty stub left over from an earlier architectural shift. PlantUML lives in `plcc.diagram.plantuml`; this directory should not be shipped.

- [ ] **Step 1: Delete the directory**

```bash
git rm -r src/plcc/lang/ext/plantuml/
```

- [ ] **Step 2: Run unit and command tests to confirm nothing broke**

```bash
bin/test/units.bash && bin/test/commands.bash
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: delete empty src/plcc/lang/ext/plantuml stub"
```

---

## Task 6: Extend packaging smoke test

**Files:**
- Modify: `bin/test/packaging.bash`

Add checks that the installed wheel exposes language and diagram discovery commands, and that they report the right plugins.

- [ ] **Step 1: Add the new checks to `bin/test/packaging.bash`**

After the loop that checks for console scripts (after the `done` line) and before the `export PATH` line, insert:

```bash
export PATH="${VENV}/bin:${PATH}"

# Verify language and diagram discovery
LANG_LIST=$("${VENV}/bin/plcc-lang-list")
echo "${LANG_LIST}" | grep -q "python" || { echo "FAIL: plcc-lang-list missing 'python'"; exit 1; }
echo "${LANG_LIST}" | grep -q "java"   || { echo "FAIL: plcc-lang-list missing 'java'";   exit 1; }
echo "OK: plcc-lang-list reports python and java"

DIAGRAM_LIST=$("${VENV}/bin/plcc-diagram-list")
echo "${DIAGRAM_LIST}" | grep -q "plantuml" || { echo "FAIL: plcc-diagram-list missing 'plantuml'"; exit 1; }
echo "OK: plcc-diagram-list reports plantuml"
```

> **Note:** Remove the `export PATH` line that appears later in the file (it would be a duplicate). The line currently appears as `export PATH="${VENV}/bin:${PATH}"` just before the `WORK_DIR` block — merge these together.

- [ ] **Step 2: Build the wheel and run the packaging test**

```bash
bin/build/package.bash && bin/test/packaging.bash
```

Expected: all checks pass including the new lang-list/diagram-list checks.

- [ ] **Step 3: Commit**

```bash
git add bin/test/packaging.bash
git commit -m "test(packaging): add plcc-lang-list and plcc-diagram-list smoke checks"
```

---

## Task 7: languages-pin.txt

**Files:**
- Create: `tests/fixtures/languages-pin.txt`

CI needs to clone the `languages` repo at a pinned commit so corpus tests are reproducible.

- [ ] **Step 1: Get the current HEAD SHA of the languages repo**

```bash
git -C "${LANGUAGES_REPO_PATH}" rev-parse HEAD
```

Copy the SHA printed.

- [ ] **Step 2: Create the pin file**

```bash
echo "<SHA-from-step-1>" > tests/fixtures/languages-pin.txt
```

The file must contain exactly one line: the 40-character SHA.

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/languages-pin.txt
git commit -m "chore(ci): add languages-pin.txt for reproducible corpus tests"
```

---

## Task 8: ci.yml

**Files:**
- Replace: `.github/workflows/ci.yml`

Replace the existing ci.yml with a three-job workflow. The `unit-and-integration` job gives fast feedback. `languages-corpus` and `packaging` run only after it passes.

- [ ] **Step 1: Replace `.github/workflows/ci.yml` entirely**

```yaml
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  unit-and-integration:
    name: Unit and integration tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install PDM
        run: pip install pdm
      - name: Run unit tests
        run: bin/test/units.bash
      - name: Run command tests
        run: bin/test/commands.bash
      - name: Run integration tests
        run: bin/test/integration.bash

  languages-corpus:
    name: Languages corpus (Java e2e)
    needs: unit-and-integration
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'
      - name: Install PDM
        run: pip install pdm
      - name: Clone languages repo at pinned commit
        run: |
          PIN=$(cat tests/fixtures/languages-pin.txt)
          git clone https://github.com/ourorg/languages.git /tmp/languages
          git -C /tmp/languages checkout "${PIN}"
      - name: Run e2e corpus tests
        env:
          LANGUAGES_REPO_PATH: /tmp/languages
        run: bin/test/e2e.bash

  packaging:
    name: Packaging
    needs: unit-and-integration
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install PDM
        run: pip install pdm
      - name: Build wheel
        run: bin/build/package.bash
      - name: Validate metadata and README
        run: pip install twine && twine check dist/*
      - name: Run packaging smoke test
        run: bin/test/packaging.bash
```

> **Note:** Replace `ourorg/languages` with the actual GitHub path of the languages repo (e.g. `StoneyJackson/languages`). Run `git remote get-url origin` in `${LANGUAGES_REPO_PATH}` if unsure.

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: replace ci.yml with three-job workflow (unit-integration, corpus, packaging)"
```

---

## Task 9: release.yml

**Files:**
- Delete: `.github/workflows/pypi.yaml`
- Create: `.github/workflows/release.yml`

The release workflow runs on every push to `main` and on manual `workflow_dispatch`. It determines the next version, tags, creates a GitHub Release, and publishes to TestPyPI then real PyPI.

When triggered by `workflow_dispatch`, the real-PyPI step is skipped — making it a safe rehearsal.

- [ ] **Step 1: Delete the old release workflow**

```bash
git rm .github/workflows/pypi.yaml
```

- [ ] **Step 2: Create `.github/workflows/release.yml`**

```yaml
name: Release

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: write
  id-token: write

jobs:
  semantic-release:
    name: Semantic release
    runs-on: ubuntu-latest
    outputs:
      released: ${{ steps.release.outputs.released }}
      version: ${{ steps.release.outputs.version }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Python Semantic Release
        id: release
        uses: python-semantic-release/python-semantic-release@v9
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          push: "true"
          commit: "false"
          changelog: "false"

  publish:
    name: Publish to PyPI
    needs: semantic-release
    if: needs.semantic-release.outputs.released == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ needs.semantic-release.outputs.version && format('v{0}', needs.semantic-release.outputs.version) || github.sha }}
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install PDM
        run: pip install pdm
      - name: Build wheel
        run: bin/build/package.bash

      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/

      - name: Smoke test TestPyPI install
        run: |
          VERSION="${{ needs.semantic-release.outputs.version }}"
          python -m venv /tmp/smoke-venv
          /tmp/smoke-venv/bin/pip install \
            --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            "plcc-ng==${VERSION}"
          WORK=$(mktemp -d)
          /tmp/smoke-venv/bin/plcc-make "$(pwd)/tests/fixtures/trivial.plcc" --output="${WORK}"
          test -f "${WORK}/spec.json" || { echo "FAIL: spec.json missing"; exit 1; }
          echo "TestPyPI smoke test passed"

      - name: Publish to PyPI
        if: github.event_name != 'workflow_dispatch'
        uses: pypa/gh-action-pypi-publish@release/v1
```

> **Note on Trusted Publishing:** The `pypa/gh-action-pypi-publish` action uses OIDC (no API token needed) when Trusted Publishing is configured on PyPI/TestPyPI. See Task 10 for the one-time manual setup.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml .github/workflows/pypi.yaml
git commit -m "ci: add release.yml with semantic-release and Trusted Publishing"
```

---

## Task 10: Manual setup checklist

These steps cannot be automated. Complete them once before the first release attempt.

- [ ] **Step 1: Verify the GitHub repo name matches pyproject.toml URLs**

Check that `[project.urls]` in `pyproject.toml` and the `languages-corpus` job's clone URL in `ci.yml` both use the correct GitHub org/repo paths.

- [ ] **Step 2: Configure Trusted Publishing on TestPyPI**

Go to https://test.pypi.org → Account settings → Publishing → Add a new pending publisher:
- PyPI project name: `plcc-ng`
- Owner: `<your GitHub org>`
- Repository: `plcc-ng` (or whatever the repo is named)
- Workflow filename: `release.yml`
- Environment name: *(leave blank — the release.yml publish job has no environment block for TestPyPI)*

- [ ] **Step 3: Configure Trusted Publishing on real PyPI**

Same as Step 2 but at https://pypi.org.

- [ ] **Step 4: Enable branch protection on `main`**

Go to the GitHub repo → Settings → Branches → Add rule for `main`:
- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging
  - Add required checks: `Unit and integration tests`, `Languages corpus (Java e2e)`, `Packaging`
- ✅ Require linear history
- ✅ Do not allow bypassing the above settings

- [ ] **Step 5: Test the release pipeline with workflow_dispatch**

Merge a PR (or push directly to main before branch protection is active). Go to Actions → Release → Run workflow. This triggers a `workflow_dispatch` run which: determines version, tags, creates a GitHub Release, builds wheel, publishes to **TestPyPI only** (real PyPI is skipped on `workflow_dispatch`), runs the smoke test.

Verify: the TestPyPI smoke test passes and the package appears at https://test.pypi.org/project/plcc-ng/.

- [ ] **Step 6: Confirm first real release**

After branch protection is active, merge a PR with conventional commits. The `release.yml` push-to-main trigger fires, produces a real PyPI release. Verify at https://pypi.org/project/plcc-ng/.

---

## Running the full suite after all tasks

```bash
cd .worktrees/multi-lang
bin/test/units.bash
bin/test/commands.bash
bin/test/integration.bash
LANGUAGES_REPO_PATH=/tmp/languages bin/test/e2e.bash
bin/build/package.bash && bin/test/packaging.bash
```

All should pass.
