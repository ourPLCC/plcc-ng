# E2E Haskell Roundtrip CI Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the slow Haskell roundtrip test out of the main e2e suite, add a dedicated local script and CI job for it, and cache aggressively so CI wall time equals the slowest parallel job rather than their sum.

**Architecture:** Three independent changes applied in order: (1) split the bats file so the fast emit test and the slow roundtrip test are separate files; (2) add a new `bin/test/e2e_haskell_roundtrip.bash` script and update `e2e.bash` and `all.bash` to exclude/include the roundtrip appropriately; (3) rewrite `ci.yml` to run all six tiers as parallel jobs with `.venv/`, cabal store, and `dist-newstyle/` caches.

**Tech Stack:** bash, bats, GitHub Actions, cabal (Haskell), PDM (Python)

## Global Constraints

- All `bin/test/*.bash` scripts must follow the existing pattern: `set -euo pipefail`, `SCRIPT_DIR`/`PROJECT_ROOT` setup, `source _cache.bash`, `_run()` function, `run_cached /tmp/plcc-test-<name>.log _run`.
- `SKIP_SETUP=1` skips `bats.bash` + `pdm install` inside scripts (used by `functional.bash` to avoid repeated setup).
- All bats e2e tests live in `tests/bats/e2e/`. The `find` command in `e2e.bash` excludes files by name.
- Commits touching only docs/specs/plans must include `[skip ci]` in the subject line.
- Run `bin/test/units.bash` after every code change to keep the fast tier green.

---

### Task 1: Split haskell.bats into fast and slow files

**Files:**
- Modify: `tests/bats/e2e/haskell.bats`
- Create: `tests/bats/e2e/haskell_roundtrip.bats`

**Interfaces:**
- Produces: `tests/bats/e2e/haskell_roundtrip.bats` — a standalone bats file containing exactly one test ("haskell pipeline: emit-build-run roundtrip") that respects `HASKELL_ROUNDTRIP_OUT_DIR` for its output directory.
- Produces: `tests/bats/e2e/haskell.bats` — retains exactly one test ("haskell pipeline: spec to model to emit produces expected files"), no cabal dependency.

- [ ] **Step 1: Create `tests/bats/e2e/haskell_roundtrip.bats`**

This file is the roundtrip test extracted from the current `haskell.bats`, with two changes: (a) `OUT_DIR` uses `HASKELL_ROUNDTRIP_OUT_DIR` when set so CI can cache the `dist-newstyle/` directory; (b) teardown only removes `OUT_DIR` when it was a temp dir.

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v cabal &>/dev/null; then skip "cabal not available"; fi
    cabal update
    SPEC_DIR=$(mktemp -d)
    OUT_DIR="${HASKELL_ROUNDTRIP_OUT_DIR:-$(mktemp -d)}"
    cat > "$SPEC_DIR/arith.plcc" << 'EOF'
token NUM '\d+'
token PLUS '\+'
skip SPACE '\s+'
%
<Program>              ::= <Expr:expr>
<Expr>                 ::= <Term:term> <ExprRest:rest>
<ExprRest:AddRest>     ::= PLUS <Term:term> <ExprRest:rest>
<ExprRest:NilRest>     ::=
<Term>                 ::= <NUM:num>
%
Haskell
Program
%%%
_run :: Program -> String
_run (Program e) = evalExpr e
%%%
Expr
%%%
evalExpr :: Expr -> String
evalExpr (Expr t r) = evalRest r (read (evalTerm t) :: Int)
%%%
ExprRest
%%%
evalRest :: ExprRest -> Int -> String
evalRest (AddRest t r) acc = evalRest r (acc + read (evalTerm t) :: Int)
evalRest NilRest acc = show acc
%%%
Term
%%%
evalTerm :: Term -> String
evalTerm (Term n) = lexeme n
%%%
EOF
}

teardown() {
    rm -rf "$SPEC_DIR"
    if [[ -z "${HASKELL_ROUNDTRIP_OUT_DIR:-}" ]]; then
        rm -rf "$OUT_DIR"
    fi
}

@test "haskell pipeline: emit-build-run roundtrip" {
    SPEC_JSON=$(mktemp)
    MODEL_JSON=$(mktemp)
    LL1_JSON=$(mktemp)
    trap "rm -f '$SPEC_JSON' '$MODEL_JSON' '$LL1_JSON'" RETURN

    plcc-spec "$SPEC_DIR/arith.plcc" > "$SPEC_JSON"
    plcc-model "$SPEC_JSON" > "$MODEL_JSON"
    plcc-spec "$SPEC_DIR/arith.plcc" | plcc-ll1 > "$LL1_JSON"
    plcc-haskell-emit --output="$OUT_DIR" < "$MODEL_JSON"
    plcc-haskell-build --output="$OUT_DIR"

    result=$(echo '1 + 2' \
        | plcc-tokens "$SPEC_JSON" \
        | plcc-trees --ll1="$LL1_JSON" \
        | plcc-haskell-run --output="$OUT_DIR")

    echo "$result" | grep -q '"value":"3"'
}
```

- [ ] **Step 2: Update `tests/bats/e2e/haskell.bats`**

Remove `cabal update` from `setup()` (cabal is not needed for the emit test), and remove the roundtrip `@test` block entirely. The file becomes:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    SPEC_DIR=$(mktemp -d)
    OUT_DIR=$(mktemp -d)
    cat > "$SPEC_DIR/arith.plcc" << 'EOF'
token NUM '\d+'
token PLUS '\+'
skip SPACE '\s+'
%
<Program>              ::= <Expr:expr>
<Expr>                 ::= <Term:term> <ExprRest:rest>
<ExprRest:AddRest>     ::= PLUS <Term:term> <ExprRest:rest>
<ExprRest:NilRest>     ::=
<Term>                 ::= <NUM:num>
%
Haskell
Program
%%%
_run :: Program -> String
_run (Program e) = evalExpr e
%%%
Expr
%%%
evalExpr :: Expr -> String
evalExpr (Expr t r) = evalRest r (read (evalTerm t) :: Int)
%%%
ExprRest
%%%
evalRest :: ExprRest -> Int -> String
evalRest (AddRest t r) acc = evalRest r (acc + read (evalTerm t) :: Int)
evalRest NilRest acc = show acc
%%%
Term
%%%
evalTerm :: Term -> String
evalTerm (Term n) = lexeme n
%%%
EOF
}

teardown() {
    rm -rf "$SPEC_DIR" "$OUT_DIR"
}

@test "haskell pipeline: spec to model to emit produces expected files" {
    SPEC_JSON=$(mktemp)
    MODEL_JSON=$(mktemp)
    trap "rm -f '$SPEC_JSON' '$MODEL_JSON'" RETURN

    plcc-spec "$SPEC_DIR/arith.plcc" > "$SPEC_JSON"
    plcc-model "$SPEC_JSON" > "$MODEL_JSON"
    plcc-haskell-emit --output="$OUT_DIR" < "$MODEL_JSON"

    [ -f "$OUT_DIR/interpreter.cabal" ]
    [ -f "$OUT_DIR/Token.hs" ]
    [ -f "$OUT_DIR/Main.hs" ]
    [ -f "$OUT_DIR/Program.hs" ]
}
```

- [ ] **Step 3: Run `haskell.bats` and verify only the fast test runs**

```bash
pdm run bats tests/bats/e2e/haskell.bats
```

Expected: 1 test, 0 failures. No cabal involvement. Completes in seconds.

- [ ] **Step 4: Run `haskell_roundtrip.bats` and verify it runs or skips cleanly**

```bash
pdm run bats tests/bats/e2e/haskell_roundtrip.bats
```

Expected: either 1 test passed (if cabal is available) or 1 test skipped with "cabal not available". Either outcome is correct.

- [ ] **Step 5: Run unit tests to confirm nothing is broken**

```bash
bin/test/units.bash
```

Expected: 1073 passed, 1 skipped (or similar — no failures).

- [ ] **Step 6: Commit**

```bash
git add tests/bats/e2e/haskell.bats tests/bats/e2e/haskell_roundtrip.bats
git commit -m "test: split haskell.bats into fast emit and slow roundtrip"
```

---

### Task 2: Add e2e_haskell_roundtrip.bash and update e2e.bash / all.bash

**Files:**
- Modify: `bin/test/e2e.bash`
- Create: `bin/test/e2e_haskell_roundtrip.bash`
- Modify: `bin/test/all.bash`

**Interfaces:**
- Consumes: `tests/bats/e2e/haskell_roundtrip.bats` from Task 1.
- Produces: `bin/test/e2e_haskell_roundtrip.bash` — a script that runs only `haskell_roundtrip.bats`, caches output to `/tmp/plcc-test-e2e-haskell-roundtrip.log`, and respects `SKIP_SETUP`.

- [ ] **Step 1: Add `haskell_roundtrip.bats` exclusion to `bin/test/e2e.bash`**

The `find` line currently reads:
```bash
bats $(find tests/bats/e2e/ -name "*.bats" ! -name "languages-java.bats" | sort)
```

Change it to:
```bash
bats $(find tests/bats/e2e/ -name "*.bats" ! -name "languages-java.bats" ! -name "haskell_roundtrip.bats" | sort)
```

- [ ] **Step 2: Verify `bin/test/e2e.bash` no longer runs the roundtrip**

```bash
PLCC_NO_TEST_CACHE=1 bin/test/e2e.bash 2>&1 | grep -E "haskell|roundtrip|tests,"
```

Expected: output mentions the fast emit test ("spec to model to emit") but NOT "roundtrip". The summary line will show one fewer test than before.

- [ ] **Step 3: Create `bin/test/e2e_haskell_roundtrip.bash`**

Follow the identical structure as `bin/test/commands.bash` and `bin/test/integration.bash`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/e2e_haskell_roundtrip.bash"
echo "------------------------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    cd "${PROJECT_ROOT}"
    if [[ -z "${SKIP_SETUP:-}" ]]; then
        "${PROJECT_ROOT}/bin/install/bats.bash"
        pdm install
    fi
    export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
    bats tests/bats/e2e/haskell_roundtrip.bats
}

run_cached /tmp/plcc-test-e2e-haskell-roundtrip.log _run
```

Make it executable:
```bash
chmod +x bin/test/e2e_haskell_roundtrip.bash
```

- [ ] **Step 4: Verify `bin/test/e2e_haskell_roundtrip.bash` runs the roundtrip**

```bash
PLCC_NO_TEST_CACHE=1 bin/test/e2e_haskell_roundtrip.bash 2>&1 | grep -E "roundtrip|skipped|passed"
```

Expected: output contains "roundtrip" and either "1 test" (passed or skipped). No failures.

- [ ] **Step 5: Update `bin/test/all.bash`**

Add `e2e_haskell_roundtrip.bash` between `functional.bash` and `packaging.bash`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/all.bash"
echo "-----------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    "${SCRIPT_DIR}/functional.bash"
    "${SCRIPT_DIR}/e2e_haskell_roundtrip.bash"
    "${SCRIPT_DIR}/packaging.bash"
}

run_cached /tmp/plcc-test-all.log _run
```

- [ ] **Step 6: Run unit tests**

```bash
bin/test/units.bash
```

Expected: all pass, no failures.

- [ ] **Step 7: Commit**

```bash
git add bin/test/e2e.bash bin/test/e2e_haskell_roundtrip.bash bin/test/all.bash
git commit -m "feat: add e2e_haskell_roundtrip.bash and exclude roundtrip from e2e suite"
```

---

### Task 3: Restructure CI with parallel jobs and caches

**Files:**
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `bin/test/e2e_haskell_roundtrip.bash` from Task 2.
- Consumes: `HASKELL_ROUNDTRIP_OUT_DIR` env var support in `haskell_roundtrip.bats` from Task 1.

- [ ] **Step 1: Replace `.github/workflows/ci.yml` with six parallel jobs**

Completely replace the file contents:

```yaml
name: CI

on:
  pull_request:
    branches: [main]
    paths-ignore:
      - 'dev-docs/**'
      - 'docs/**'
      - '*.md'
      - 'mkdocs.yml'
      - 'mkdocs-dev.yml'

jobs:
  units:
    name: Unit tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - uses: actions/cache@v4
        with:
          path: .venv
          key: ${{ runner.os }}-venv-${{ hashFiles('pdm.lock') }}
      - name: Install PDM
        run: pip install pdm
      - name: Run unit tests
        env:
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/units.bash

  commands:
    name: Command tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - uses: actions/cache@v4
        with:
          path: .venv
          key: ${{ runner.os }}-venv-${{ hashFiles('pdm.lock') }}
      - name: Install PDM
        run: pip install pdm
      - name: Run command tests
        env:
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/commands.bash

  integration:
    name: Integration tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - uses: actions/cache@v4
        with:
          path: .venv
          key: ${{ runner.os }}-venv-${{ hashFiles('pdm.lock') }}
      - name: Install PDM
        run: pip install pdm
      - name: Run integration tests
        env:
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/integration.bash

  e2e:
    name: E2E tests
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
      - uses: actions/cache@v4
        with:
          path: .venv
          key: ${{ runner.os }}-venv-${{ hashFiles('pdm.lock') }}
      - name: Install PDM
        run: pip install pdm
      - name: Clone languages repo at pinned commit
        run: |
          PIN=$(cat tests/fixtures/languages-pin.txt)
          git clone https://github.com/ourPLCC/languages.git /tmp/languages
          git -C /tmp/languages checkout "${PIN}"
      - name: Run e2e tests
        env:
          LANGUAGES_REPO_PATH: /tmp/languages
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/e2e.bash

  e2e-haskell-roundtrip:
    name: E2E Haskell roundtrip
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - uses: actions/cache@v4
        with:
          path: .venv
          key: ${{ runner.os }}-venv-${{ hashFiles('pdm.lock') }}
      - uses: actions/cache@v4
        with:
          path: |
            ~/.cabal/packages
            ~/.cabal/store
          key: ${{ runner.os }}-cabal-${{ hashFiles('src/plcc/lang/ext/haskell/emit.py') }}
          restore-keys: ${{ runner.os }}-cabal-
      - uses: actions/cache@v4
        with:
          path: ~/.cache/plcc-haskell-roundtrip
          key: ${{ runner.os }}-dist-newstyle-${{ hashFiles('src/plcc/lang/ext/haskell/emit.py', 'src/plcc/lang/ext/haskell/runtime/**', 'tests/bats/e2e/haskell_roundtrip.bats') }}
      - name: Install PDM
        run: pip install pdm
      - name: Run Haskell roundtrip test
        env:
          HASKELL_ROUNDTRIP_OUT_DIR: ~/.cache/plcc-haskell-roundtrip
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/e2e_haskell_roundtrip.bash

  package:
    name: Packaging
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - uses: actions/cache@v4
        with:
          path: .venv
          key: ${{ runner.os }}-venv-${{ hashFiles('pdm.lock') }}
      - name: Install PDM
        run: pip install pdm
      - name: Build wheel
        run: bin/build/package.bash
      - name: Validate metadata and README
        run: pip install twine && twine check dist/*
      - name: Run packaging smoke test
        env:
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/packaging.bash
```

- [ ] **Step 2: Validate the YAML is well-formed**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "YAML valid"
```

Expected: prints `YAML valid` with no errors.

- [ ] **Step 3: Confirm the old `unit-and-integration` and `languages-corpus` job names are gone**

```bash
grep -E "unit-and-integration|languages-corpus" .github/workflows/ci.yml
```

Expected: no output (both old job names are gone).

- [ ] **Step 4: Confirm all six job names are present**

```bash
grep "^  [a-z]" .github/workflows/ci.yml
```

Expected: six lines — `units:`, `commands:`, `integration:`, `e2e:`, `e2e-haskell-roundtrip:`, `package:`.

- [ ] **Step 5: Run unit tests**

```bash
bin/test/units.bash
```

Expected: all pass, no failures.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: parallelize all test jobs and add venv/cabal/dist-newstyle caches"
```
