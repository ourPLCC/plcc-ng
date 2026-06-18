# Hoist Test Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run `pdm install`, `bin/install/pdm.bash`, and `bin/install/bats.bash` exactly once per `functional.bash` invocation instead of redundantly inside each leaf script.

**Architecture:** Add a `SKIP_SETUP` env guard to each leaf script's setup block. Hoist all three setup calls into `functional.bash`, which passes `SKIP_SETUP=1` inline to each leaf invocation. Direct callers of leaf scripts are unaffected.

**Tech Stack:** Bash shell scripts only. No new dependencies.

## Global Constraints

- All scripts must remain independently runnable (i.e., work when called directly without `SKIP_SETUP` set).
- `SKIP_SETUP=1` is the only tested/documented value for the guard variable.
- Pass `SKIP_SETUP=1` inline on each leaf invocation in `functional.bash` (not via `export`) to avoid leaking into the surrounding environment.
- All implementation changes are limited to shell scripts under `bin/test/` and `bin/install/` — do not create new files there.
- Commit messages follow the project convention: `chore(096): <description>`.

---

### Task 1: Guard setup in `units.bash`

**Files:**
- Modify: `bin/test/units.bash`

**Interfaces:**
- Produces: `SKIP_SETUP` guard pattern used by Tasks 2 and 3.

- [ ] **Step 1: Read the current file**

Read `bin/test/units.bash` to confirm current content before editing.

- [ ] **Step 2: Add the guard**

Replace the `_run()` body so it reads:

```bash
_run() {
    if [[ -z "${SKIP_SETUP:-}" ]]; then
        "${SCRIPT_DIR}/../install/pdm.bash"
        pdm install
    fi
    pdm test -v "$@"
}
```

Full file after edit:

```bash
#!/usr/bin/env bash

set -euo pipefail

echo "bin/test/units.bash"
echo "-------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    if [[ -z "${SKIP_SETUP:-}" ]]; then
        "${SCRIPT_DIR}/../install/pdm.bash"
        pdm install
    fi
    pdm test -v "$@"
}

run_cached /tmp/plcc-test-units.log _run "$@"
```

- [ ] **Step 3: Verify direct call still works**

```bash
bin/test/units.bash
```

Expected: setup runs (pdm.bash + pdm install output), then `972 passed` (or similar count).

- [ ] **Step 4: Verify SKIP_SETUP skips setup**

```bash
SKIP_SETUP=1 bin/test/units.bash
```

Expected: no `pdm install` output, tests still pass (pdm is already installed in the dev environment).

- [ ] **Step 5: Commit**

```bash
git add bin/test/units.bash
git commit -m "chore(096): guard setup in units.bash with SKIP_SETUP"
```

---

### Task 2: Guard setup in `commands.bash`, `integration.bash`, `e2e.bash`

**Files:**
- Modify: `bin/test/commands.bash`
- Modify: `bin/test/integration.bash`
- Modify: `bin/test/e2e.bash`

**Interfaces:**
- Consumes: `SKIP_SETUP` guard pattern from Task 1.

- [ ] **Step 1: Edit `commands.bash`**

Replace the `_run()` body so `bats.bash` and `pdm install` are guarded:

```bash
_run() {
    cd "${PROJECT_ROOT}"
    if [[ -z "${SKIP_SETUP:-}" ]]; then
        "${PROJECT_ROOT}/bin/install/bats.bash"
        pdm install
    fi
    export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
    bats tests/bats/commands/
}
```

Full file after edit:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/commands.bash"
echo "----------------------"

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
    bats tests/bats/commands/
}

run_cached /tmp/plcc-test-commands.log _run
```

- [ ] **Step 2: Edit `integration.bash`**

Same guard pattern:

```bash
_run() {
    cd "${PROJECT_ROOT}"
    if [[ -z "${SKIP_SETUP:-}" ]]; then
        "${PROJECT_ROOT}/bin/install/bats.bash"
        pdm install
    fi
    export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
    bats tests/bats/integration/
}
```

Full file after edit:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/integration.bash"
echo "-------------------------"

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
    bats tests/bats/integration/
}

run_cached /tmp/plcc-test-integration.log _run
```

- [ ] **Step 3: Edit `e2e.bash`**

Same guard pattern around `bats.bash` + `pdm install` (the `LANGUAGES_REPO_PATH` block is not setup — leave it as-is):

```bash
_run() {
    cd "${PROJECT_ROOT}"
    if [[ -z "${SKIP_SETUP:-}" ]]; then
        "${PROJECT_ROOT}/bin/install/bats.bash"
        pdm install
    fi
    export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
    bats $(find tests/bats/e2e/ -name "*.bats" ! -name "languages-java.bats" | sort)
    if [ -n "${LANGUAGES_REPO_PATH:-}" ]; then
        "${PROJECT_ROOT}/bin/install/java.bash"
        echo ""
        echo "Running Java corpus tests (LANGUAGES_REPO_PATH=${LANGUAGES_REPO_PATH})"
        bats tests/bats/e2e/languages-java.bats
    fi
}
```

Full file after edit:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/e2e.bash"
echo "-----------------"

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
    bats $(find tests/bats/e2e/ -name "*.bats" ! -name "languages-java.bats" | sort)
    if [ -n "${LANGUAGES_REPO_PATH:-}" ]; then
        "${PROJECT_ROOT}/bin/install/java.bash"
        echo ""
        echo "Running Java corpus tests (LANGUAGES_REPO_PATH=${LANGUAGES_REPO_PATH})"
        bats tests/bats/e2e/languages-java.bats
    fi
}

run_cached /tmp/plcc-test-e2e.log _run
```

- [ ] **Step 4: Verify direct calls still work**

```bash
bin/test/commands.bash
```

Expected: setup runs, bats command tests pass.

- [ ] **Step 5: Verify SKIP_SETUP skips setup in all three**

```bash
SKIP_SETUP=1 bin/test/commands.bash
SKIP_SETUP=1 bin/test/integration.bash
SKIP_SETUP=1 bin/test/e2e.bash
```

Expected: no `bats.bash` or `pdm install` output; tests pass (tools already installed in dev environment).

- [ ] **Step 6: Commit**

```bash
git add bin/test/commands.bash bin/test/integration.bash bin/test/e2e.bash
git commit -m "chore(096): guard setup in commands, integration, e2e with SKIP_SETUP"
```

---

### Task 3: Hoist setup into `functional.bash`

**Files:**
- Modify: `bin/test/functional.bash`

**Interfaces:**
- Consumes: `SKIP_SETUP` guard in all four leaf scripts (Tasks 1 and 2).

- [ ] **Step 1: Read the current file**

Read `bin/test/functional.bash` to confirm current content before editing.

- [ ] **Step 2: Add setup calls and pass SKIP_SETUP=1 to each leaf**

Replace the `_run()` body:

```bash
_run() {
    "${SCRIPT_DIR}/../install/pdm.bash"
    pdm install
    "${SCRIPT_DIR}/../install/bats.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash"
}
```

Full file after edit:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/funcional.bash"  # pre-existing typo in the script — leave as-is
echo "-----------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    "${SCRIPT_DIR}/../install/pdm.bash"
    pdm install
    "${SCRIPT_DIR}/../install/bats.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash"
}

run_cached /tmp/plcc-test-functional.log _run
```

- [ ] **Step 3: Run the full functional suite**

```bash
bin/test/cache/clear.bash
bin/test/functional.bash
```

Clear the cache first so this is a live run. Expected: setup output appears once at the top, then all four leaf scripts run without repeating setup. All tests pass.

- [ ] **Step 4: Confirm setup ran only once**

```bash
grep -c "pdm install" /tmp/plcc-test-functional.log
```

Expected output: `1`

- [ ] **Step 5: Commit**

```bash
git add bin/test/functional.bash
git commit -m "chore(096): hoist setup into functional.bash; pass SKIP_SETUP=1 to leaf scripts"
```
