# Path filter for bats-backed test tiers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `bin/test/commands.bash`, `bin/test/integration.bash`, `bin/test/e2e.bash`, and `bin/test/functional.bash` an optional path parameter that narrows the `bats` invocation, matching the TDD-inner-loop role `bin/test/units.bash` already plays for pytest.

**Architecture:** Each script's `_run()` function grows an optional `$1` path parameter, defaulting to today's whole-tier behavior when absent. `functional.bash` additionally routes a given path to whichever single sub-script owns that tier. A prerequisite fix folds command arguments into the test-output cache key (`bin/test/_cache.bash`) so that different paths at the same git state don't collide in the cache.

**Tech Stack:** Bash (`set -euo pipefail`), bats (bats-core 1.11.0), git.

**Spec:** [dev-docs/specs/2026-07-23-155-test-scripts-path-filter-design.md](../specs/2026-07-23-155-test-scripts-path-filter-design.md)

## Global Constraints

- No path validation before forwarding to `bats` — let `bats` report a bad path itself. (Matches `units.bash`'s existing no-pre-check precedent.)
- `set -euo pipefail` and `SCRIPT_DIR`/`PROJECT_ROOT` absolute-path resolution stay unchanged in every modified script — match existing style (CONTRIBUTING.md).
- All new/changed bash goes in `bin/test/`; no new top-level scripts (CONTRIBUTING.md: check `bin/` first, extend don't duplicate).

---

### Task 1: Cache key includes command arguments

**Files:**
- Modify: `bin/test/_cache.bash:12-21` (`_cache_key`), `bin/test/_cache.bash:37` (`run_cached`'s call site)
- Test: `tests/bats/commands/cache.bats`

**Interfaces:**
- Consumes: nothing new.
- Produces: `_cache_key <extra-args-string>` — now takes one argument, folds it into the returned hash alongside existing git state. `run_cached` computes it as `_cache_key "$*"` using its own remaining positional params after the cache-file `shift`. Every later task's scripts still call `run_cached <cache-file> _run "$@"` exactly as before — this task changes `run_cached`'s internals only, not its external contract.

- [ ] **Step 1: Write the failing test**

Open `tests/bats/commands/cache.bats` and add this new test case right after the existing `"content change on already-dirty file invalidates cache"` test (currently ending at line 109) and before the `"fallback: runs uncached when git is unavailable"` test:

```bash
@test "different arguments produce independent cache entries (no false hit)" {
    run bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo arg-one 2>/dev/null"
    [[ "$output" == "arg-one" ]]
    run bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo arg-two 2>/dev/null"
    [[ "$output" == "arg-two" ]]
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bats tests/bats/commands/cache.bats -f "different arguments produce independent cache entries"`
Expected: FAIL — the second `run_cached` call hits the cache (same git state, args-agnostic key) and replays `"arg-one"` instead of running `echo arg-two`, so the second assertion (`"$output" == "arg-two"`) fails.

- [ ] **Step 3: Write minimal implementation**

In `bin/test/_cache.bash`, replace the `_cache_key` function (currently):

```bash
_cache_key() {
    local head status diff untracked
    head=$(git rev-parse HEAD 2>/dev/null) || return 1
    status=$(git status --porcelain 2>/dev/null) || return 1
    diff=$(git diff HEAD 2>/dev/null) || return 1
    untracked=$(git ls-files --others --exclude-standard -z 2>/dev/null \
        | xargs -0 -I{} cat "{}" 2>/dev/null) || return 1
    printf '%s\n%s\n%s\n%s' "${head}" "${status}" "${diff}" "${untracked}" \
        | sha256sum | cut -d' ' -f1
}
```

with:

```bash
_cache_key() {
    local extra_args="$1"
    local head status diff untracked
    head=$(git rev-parse HEAD 2>/dev/null) || return 1
    status=$(git status --porcelain 2>/dev/null) || return 1
    diff=$(git diff HEAD 2>/dev/null) || return 1
    untracked=$(git ls-files --others --exclude-standard -z 2>/dev/null \
        | xargs -0 -I{} cat "{}" 2>/dev/null) || return 1
    printf '%s\n%s\n%s\n%s\n%s' "${head}" "${status}" "${diff}" "${untracked}" "${extra_args}" \
        | sha256sum | cut -d' ' -f1
}
```

Then update the call site inside `run_cached` (currently):

```bash
    local key
    if ! key=$(_cache_key); then
        "$@"
        return
    fi
```

to:

```bash
    local key
    if ! key=$(_cache_key "$*"); then
        "$@"
        return
    fi
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bats tests/bats/commands/cache.bats`
Expected: all tests PASS, including the new one.

- [ ] **Step 5: Commit**

```bash
git add bin/test/_cache.bash tests/bats/commands/cache.bats
git commit -m "fix(test): fold command arguments into the test-output cache key"
```

---

### Task 2: `commands.bash` and `integration.bash` accept an optional path

**Files:**
- Modify: `bin/test/commands.bash` (whole file, currently 19 lines)
- Modify: `bin/test/integration.bash` (whole file, currently 19 lines)
- Create: `tests/bats/commands/test-scripts-path-filter.bats`

**Interfaces:**
- Consumes: `run_cached <cache-file> <command> [args...]` from Task 1 (unchanged external contract).
- Produces: CLI contract `commands.bash [path]` and `integration.bash [path]` — `path` optional; when given, forwarded verbatim to `bats`; when absent, defaults to the tier directory (`tests/bats/commands/` / `tests/bats/integration/`). Task 4 (`functional.bash`) relies on this exact contract: calling `commands.bash "<path>"` or `commands.bash` with no args.

- [ ] **Step 1: Write the failing test**

Create `tests/bats/commands/test-scripts-path-filter.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

PROJECT_ROOT="$(git rev-parse --show-toplevel)"

setup() {
    FAKE_BIN="$(mktemp -d)"
    CAPTURED_ARGS="${FAKE_BIN}/captured-args"
    cat > "${FAKE_BIN}/bats" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$@" > "${CAPTURED_ARGS}"
exit 0
EOF
    chmod +x "${FAKE_BIN}/bats"
    export PATH="${FAKE_BIN}:${PATH}"
    export SKIP_SETUP=1
    export PLCC_NO_TEST_CACHE=1
}

teardown() {
    rm -rf "${FAKE_BIN}"
    unset SKIP_SETUP
    unset PLCC_NO_TEST_CACHE
}

@test "commands.bash: path argument narrows bats invocation to that path" {
    "${PROJECT_ROOT}/bin/test/commands.bash" "tests/bats/commands/plcc-make.bats"
    [ "$(cat "${CAPTURED_ARGS}")" = "tests/bats/commands/plcc-make.bats" ]
}

@test "commands.bash: no argument runs the whole tier directory" {
    "${PROJECT_ROOT}/bin/test/commands.bash"
    [ "$(cat "${CAPTURED_ARGS}")" = "tests/bats/commands/" ]
}

@test "integration.bash: path argument narrows bats invocation to that path" {
    "${PROJECT_ROOT}/bin/test/integration.bash" "tests/bats/integration/ll1-tree.bats"
    [ "$(cat "${CAPTURED_ARGS}")" = "tests/bats/integration/ll1-tree.bats" ]
}

@test "integration.bash: no argument runs the whole tier directory" {
    "${PROJECT_ROOT}/bin/test/integration.bash"
    [ "$(cat "${CAPTURED_ARGS}")" = "tests/bats/integration/" ]
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bats tests/bats/commands/test-scripts-path-filter.bats`
Expected: FAIL on all four tests — `bin/test/commands.bash` and `bin/test/integration.bash` currently ignore `$1` entirely, and their `run_cached` calls don't forward `"$@"`, so the fake `bats` never runs and `${CAPTURED_ARGS}` is never written (`cat` on a missing file fails the test).

- [ ] **Step 3: Write minimal implementation**

Replace the full contents of `bin/test/commands.bash` (currently):

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

with:

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
    bats "${1:-tests/bats/commands/}"
}

run_cached /tmp/plcc-test-commands.log _run "$@"
```

Replace the full contents of `bin/test/integration.bash` (currently):

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

with:

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
    bats "${1:-tests/bats/integration/}"
}

run_cached /tmp/plcc-test-integration.log _run "$@"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bats tests/bats/commands/test-scripts-path-filter.bats`
Expected: all four tests PASS.

- [ ] **Step 5: Commit**

```bash
git add bin/test/commands.bash bin/test/integration.bash tests/bats/commands/test-scripts-path-filter.bats
git commit -m "feat(test): commands.bash and integration.bash accept an optional path argument"
```

---

### Task 3: `e2e.bash` accepts an optional path

**Files:**
- Modify: `bin/test/e2e.bash` (whole file, currently 23 lines)
- Modify: `tests/bats/commands/test-scripts-path-filter.bats` (append two cases)

**Interfaces:**
- Consumes: `run_cached` from Task 1; same fake-`bats`/`SKIP_SETUP`/`PLCC_NO_TEST_CACHE` test pattern from Task 2.
- Produces: CLI contract `e2e.bash [path]` — when given, `bats "$1"` runs directly (bypassing the default file list and the `LANGUAGES_REPO_PATH` conditional); when absent, today's default-list-plus-conditional behavior is unchanged. Task 4 relies on this same `[path]`-optional contract.

- [ ] **Step 1: Write the failing test**

Append to `tests/bats/commands/test-scripts-path-filter.bats` (after the `integration.bash` tests added in Task 2):

```bash
@test "e2e.bash: path argument bypasses the default file list" {
    "${PROJECT_ROOT}/bin/test/e2e.bash" "tests/bats/e2e/happy-path.bats"
    [ "$(cat "${CAPTURED_ARGS}")" = "tests/bats/e2e/happy-path.bats" ]
}

@test "e2e.bash: no argument runs the default file list, excluding java and haskell roundtrip" {
    "${PROJECT_ROOT}/bin/test/e2e.bash"
    run cat "${CAPTURED_ARGS}"
    [[ "$output" == *"tests/bats/e2e/"* ]]
    [[ "$output" != *"languages-java.bats"* ]]
    [[ "$output" != *"haskell_roundtrip.bats"* ]]
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bats tests/bats/commands/test-scripts-path-filter.bats -f "e2e.bash"`
Expected: FAIL on both — `bin/test/e2e.bash` currently ignores `$1` and always runs the `find`-built default file list regardless of arguments, and its `run_cached` call doesn't forward `"$@"`.

- [ ] **Step 3: Write minimal implementation**

Replace the full contents of `bin/test/e2e.bash` (currently):

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
    bats $(find tests/bats/e2e/ -name "*.bats" ! -name "languages-java.bats" ! -name "haskell_roundtrip.bats" | sort)
    if [ -n "${LANGUAGES_REPO_PATH:-}" ]; then
        "${PROJECT_ROOT}/bin/install/java.bash"
        echo ""
        echo "Running Java corpus tests (LANGUAGES_REPO_PATH=${LANGUAGES_REPO_PATH})"
        bats tests/bats/e2e/languages-java.bats
    fi
}

run_cached /tmp/plcc-test-e2e.log _run
```

with:

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
    if [ -n "${1:-}" ]; then
        bats "$1"
        return
    fi
    bats $(find tests/bats/e2e/ -name "*.bats" ! -name "languages-java.bats" ! -name "haskell_roundtrip.bats" | sort)
    if [ -n "${LANGUAGES_REPO_PATH:-}" ]; then
        "${PROJECT_ROOT}/bin/install/java.bash"
        echo ""
        echo "Running Java corpus tests (LANGUAGES_REPO_PATH=${LANGUAGES_REPO_PATH})"
        bats tests/bats/e2e/languages-java.bats
    fi
}

run_cached /tmp/plcc-test-e2e.log _run "$@"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bats tests/bats/commands/test-scripts-path-filter.bats`
Expected: all six tests (four from Task 2, two new) PASS.

- [ ] **Step 5: Commit**

```bash
git add bin/test/e2e.bash tests/bats/commands/test-scripts-path-filter.bats
git commit -m "feat(test): e2e.bash accepts an optional path argument"
```

---

### Task 4: `functional.bash` routes a path to the one matching tier

**Files:**
- Modify: `bin/test/functional.bash` (whole file, currently 19 lines)
- Modify: `tests/bats/commands/test-scripts-path-filter.bats` (append routing tests)

**Interfaces:**
- Consumes: the `[path]`-optional CLI contract of `units.bash` (pre-existing), `commands.bash`, `integration.bash` (Task 2), and `e2e.bash` (Task 3).
- Produces: CLI contract `functional.bash [path]` — a path under `tests/bats/commands`, `tests/bats/integration`, or `tests/bats/e2e` runs only that one sub-script (with the path forwarded); any other path is forwarded to `units.bash` alone; no argument runs all four sub-scripts in full, unchanged.

Because `functional.bash`'s `_run()` calls `"${SCRIPT_DIR}/../install/pdm.bash"`, `pdm install`, and `"${SCRIPT_DIR}/../install/bats.bash"` unconditionally (not gated by `SKIP_SETUP`, unlike the four scripts it composes), testing its routing logic in isolation requires running a copy of it inside a self-contained fake `bin/` tree — real `bin/install/*.bash` scripts and a real `pdm` on `PATH` would otherwise trigger real installs/network calls. `SCRIPT_DIR` is derived from `${BASH_SOURCE[0]}`, so copying `functional.bash` next to stub sub-scripts makes it resolve and call the stubs.

- [ ] **Step 1: Write the failing test**

Append to `tests/bats/commands/test-scripts-path-filter.bats`:

```bash
setup_functional_stub_tree() {
    STUB_ROOT="$(mktemp -d)"
    mkdir -p "${STUB_ROOT}/bin/test" "${STUB_ROOT}/bin/install"
    cp "${PROJECT_ROOT}/bin/test/functional.bash" "${STUB_ROOT}/bin/test/functional.bash"
    cp "${PROJECT_ROOT}/bin/test/_cache.bash" "${STUB_ROOT}/bin/test/_cache.bash"
    ROUTE_LOG="${STUB_ROOT}/route-log"
    for tier in units commands integration e2e; do
        cat > "${STUB_ROOT}/bin/test/${tier}.bash" <<EOF
#!/usr/bin/env bash
printf '${tier} %s\n' "\$*" >> "${ROUTE_LOG}"
EOF
        chmod +x "${STUB_ROOT}/bin/test/${tier}.bash"
    done
    for installer in pdm bats; do
        cat > "${STUB_ROOT}/bin/install/${installer}.bash" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
        chmod +x "${STUB_ROOT}/bin/install/${installer}.bash"
    done
    FAKE_PDM_BIN="$(mktemp -d)"
    printf '#!/usr/bin/env bash\nexit 0\n' > "${FAKE_PDM_BIN}/pdm"
    chmod +x "${FAKE_PDM_BIN}/pdm"
    export PATH="${FAKE_PDM_BIN}:${PATH}"
}

@test "functional.bash: commands-tier path routes only to commands.bash" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash" "tests/bats/commands/plcc-make.bats"
    [ "$(cat "${ROUTE_LOG}")" = "commands tests/bats/commands/plcc-make.bats" ]
}

@test "functional.bash: integration-tier path routes only to integration.bash" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash" "tests/bats/integration/ll1-tree.bats"
    [ "$(cat "${ROUTE_LOG}")" = "integration tests/bats/integration/ll1-tree.bats" ]
}

@test "functional.bash: e2e-tier path routes only to e2e.bash" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash" "tests/bats/e2e/happy-path.bats"
    [ "$(cat "${ROUTE_LOG}")" = "e2e tests/bats/e2e/happy-path.bats" ]
}

@test "functional.bash: non-bats-tier path routes only to units.bash" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash" "src/plcc/cmd/make_test.py"
    [ "$(cat "${ROUTE_LOG}")" = "units src/plcc/cmd/make_test.py" ]
}

@test "functional.bash: no argument runs all four sub-scripts" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash"
    run cat "${ROUTE_LOG}"
    [[ "$output" == *"units "* ]]
    [[ "$output" == *"commands "* ]]
    [[ "$output" == *"integration "* ]]
    [[ "$output" == *"e2e "* ]]
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bats tests/bats/commands/test-scripts-path-filter.bats -f "functional.bash"`
Expected: FAIL on all five — `bin/test/functional.bash` currently ignores any argument and always runs all four sub-scripts with no path forwarded, so `${ROUTE_LOG}` never matches the single-tier expectations (and the "no argument" case's four `SKIP_SETUP=1 ...` sub-invocations pass no path already, but that one may coincidentally pass before the others do — run the full file, not just this filter, at the end of the task to confirm all six from Tasks 2-3 plus these five are green together).

- [ ] **Step 3: Write minimal implementation**

Replace the full contents of `bin/test/functional.bash` (currently):

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/funcional.bash"
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

with:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/funcional.bash"
echo "-----------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    "${SCRIPT_DIR}/../install/pdm.bash"
    pdm install
    "${SCRIPT_DIR}/../install/bats.bash"

    local path="${1:-}"
    if [[ -z "${path}" ]]; then
        SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash"
        return
    fi

    case "${path}" in
        tests/bats/commands*)    SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash" "${path}" ;;
        tests/bats/integration*) SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash" "${path}" ;;
        tests/bats/e2e*)         SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash" "${path}" ;;
        *)                       SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash" "${path}" ;;
    esac
}

run_cached /tmp/plcc-test-functional.log _run "$@"
```

(Note: the typo `funcional.bash` in the echoed header is pre-existing, out of scope for this issue — leave it as-is.)

- [ ] **Step 4: Run test to verify it passes**

Run: `bats tests/bats/commands/test-scripts-path-filter.bats`
Expected: all 11 tests (4 from Task 2, 2 from Task 3, 5 from this task) PASS.

Also run the full commands tier to confirm nothing else broke:
Run: `bin/test/commands.bash`
Expected: exit 0, all bats files pass including `cache.bats` and `test-scripts-path-filter.bats`.

- [ ] **Step 5: Commit**

```bash
git add bin/test/functional.bash tests/bats/commands/test-scripts-path-filter.bats
git commit -m "feat(test): functional.bash routes a path argument to its matching tier"
```

---

### Task 5: Document the path filter in CONTRIBUTING.md

**Files:**
- Modify: `CONTRIBUTING.md:24-35` (Test command table), `CONTRIBUTING.md:37-39` (Test output cache section), `CONTRIBUTING.md:68-78` (TDD inner loop section)

**Interfaces:**
- Consumes: nothing (documentation only).
- Produces: nothing consumed by other tasks — this is the last task.

- [ ] **Step 1: Update the Test command table**

In `CONTRIBUTING.md`, replace the Test command table (currently):

```markdown
| Command | What it does | When to use |
|---|---|---|
| [bin/test/units.bash](bin/test/units.bash) | Run Python unit tests via pytest (wrapped as `pdm test`). Accepts pytest args. Fastest tier. | **TDD inner loop.** Run this on every edit. |
| [bin/test/commands.bash](bin/test/commands.bash) | Run black-box CLI tests (`tests/bats/commands/`) for individual commands exercised through their installed entry points. Covers both Level 0 primitives and Level 2 orchestrators (see architectural spec §5–6). | After finishing a command's unit tests, verify its CLI contract. |
| [bin/test/integration.bash](bin/test/integration.bash) | Run adjacent-pair pipeline tests (`tests/bats/integration/`). | After touching a stage that sits next to another in the pipeline. |
| [bin/test/e2e.bash](bin/test/e2e.bash) | Run end-to-end pipeline tests (`tests/bats/e2e/`). | After changes that could affect the whole pipeline. |
| [bin/test/functional.bash](bin/test/functional.bash) | Run all functional tiers (units + commands + integration + e2e). Does NOT include the Haskell roundtrip (see below). | Before pushing. |
```

with:

```markdown
| Command | What it does | When to use |
|---|---|---|
| [bin/test/units.bash](bin/test/units.bash) | Run Python unit tests via pytest (wrapped as `pdm test`). Accepts pytest args, e.g. `bin/test/units.bash src/plcc/cmd/make_test.py`. Fastest tier. | **TDD inner loop.** Run this on every edit. |
| [bin/test/commands.bash](bin/test/commands.bash) | Run black-box CLI tests (`tests/bats/commands/`) for individual commands exercised through their installed entry points. Covers both Level 0 primitives and Level 2 orchestrators (see architectural spec §5–6). Accepts an optional path to narrow to one file or subdirectory, e.g. `bin/test/commands.bash tests/bats/commands/plcc-make.bats`; defaults to the whole tier. | After finishing a command's unit tests, verify its CLI contract. |
| [bin/test/integration.bash](bin/test/integration.bash) | Run adjacent-pair pipeline tests (`tests/bats/integration/`). Accepts an optional path to narrow to one file or subdirectory; defaults to the whole tier. | After touching a stage that sits next to another in the pipeline. |
| [bin/test/e2e.bash](bin/test/e2e.bash) | Run end-to-end pipeline tests (`tests/bats/e2e/`). Accepts an optional path to narrow to one file or subdirectory; defaults to the whole tier (excluding the Java corpus and Haskell roundtrip, see below). | After changes that could affect the whole pipeline. |
| [bin/test/functional.bash](bin/test/functional.bash) | Run all functional tiers (units + commands + integration + e2e). Does NOT include the Haskell roundtrip (see below). Accepts an optional path; it is routed to whichever single tier owns it (a `tests/bats/<tier>/...` path runs only that tier, anything else is treated as a pytest path and runs only `units.bash`) instead of running all four tiers in full. | Before pushing. |
```

- [ ] **Step 2: Update the Test output cache section**

In `CONTRIBUTING.md`, replace this sentence (currently, on the line right after `### Test output cache`):

```markdown
All test scripts cache their output to `/tmp` so agents and tools can grep results without re-running the suite. The cache is keyed on git state (`git rev-parse HEAD` + `git status --porcelain` + `git diff HEAD` + the contents of untracked files) and is invalidated automatically whenever the working tree, HEAD, or any file's content changes.
```

with:

```markdown
All test scripts cache their output to `/tmp` so agents and tools can grep results without re-running the suite. The cache is keyed on git state (`git rev-parse HEAD` + `git status --porcelain` + `git diff HEAD` + the contents of untracked files) plus the script's own arguments, and is invalidated automatically whenever the working tree, HEAD, any file's content, or the arguments passed to the script changes — so narrowing to a different path is always a cache miss the first time, never a stale replay of a different path's result.
```

- [ ] **Step 3: Update the TDD inner loop section**

In `CONTRIBUTING.md`, replace this sentence (currently, the last line of the "## TDD inner loop" section):

```markdown
[bin/test/units.bash](bin/test/units.bash) runs in seconds and is the tightest feedback loop available. Keep it green at every commit.
```

with:

```markdown
[bin/test/units.bash](bin/test/units.bash) runs in seconds and is the tightest feedback loop available. Keep it green at every commit.

The same narrow-and-rerun pattern applies to bats-covered work: [bin/test/commands.bash](bin/test/commands.bash), [bin/test/integration.bash](bin/test/integration.bash), and [bin/test/e2e.bash](bin/test/e2e.bash) all accept an optional path to a single file or subdirectory, so you can narrow to the bats test you're iterating on instead of rerunning the whole tier.
```

- [ ] **Step 4: Verify the doc renders sensibly**

Run: `grep -n "Accepts an optional path\|narrow-and-rerun" CONTRIBUTING.md`
Expected: four matches — one per script mention added in Steps 1 and 3.

- [ ] **Step 5: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: document the path filter on bats-backed test scripts"
```

---

## Final Verification

After Task 5's commit, run the full functional tier once with caching bypassed to confirm nothing regressed:

Run: `PLCC_NO_TEST_CACHE=1 bin/test/functional.bash`
Expected: exit 0, all four tiers pass (units, commands, integration, e2e), including the new `tests/bats/commands/test-scripts-path-filter.bats` cases as part of the commands tier.
