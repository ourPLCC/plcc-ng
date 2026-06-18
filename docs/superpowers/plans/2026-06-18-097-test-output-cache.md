# Test Output Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add transparent output caching to all `bin/test/` scripts so agents can grep cached output instead of re-running the full suite.

**Architecture:** A sourced helper `bin/test/_cache.bash` provides a `run_cached` function. Each test script sources the helper and wraps its main command in `run_cached`. The cache is keyed on git state; a sidecar `.meta` file stores the key and exit code. Caching is bypassed with `PLCC_NO_TEST_CACHE=1`.

**Tech Stack:** bash, bats (≥1.5.0), git, sha256sum, awk

## Global Constraints

- All bash scripts: `set -euo pipefail`, absolute-path resolution via `SCRIPT_DIR`/`PROJECT_ROOT`, `.bash` extension
- Cache files: `/tmp/plcc-test-<name>.log` and `/tmp/plcc-test-<name>.log.meta`
- Stats log: `${PLCC_TEST_STATS_LOG:-/tmp/plcc-test-cache-stats.log}` (env-overridable for tests)
- Escape hatch env var: `PLCC_NO_TEST_CACHE=1`
- `_cache.bash` is sourced, not executed — no shebang, no `set -euo pipefail` (inherits caller's shell state)
- Bats tests live in `tests/bats/commands/`
- Run unit tests with: `bin/test/units.bash`
- Run bats commands tests with: `bin/test/commands.bash`

---

### Task 1: `bin/test/_cache.bash` — core caching helper

**Files:**
- Create: `bin/test/_cache.bash`
- Create: `tests/bats/commands/cache.bats`

**Interfaces:**
- Produces: `run_cached <cache-file> <command> [args...]` — sources into any bash script; exits with cached or live exit code

---

- [ ] **Step 1: Create the bats test file**

Create `tests/bats/commands/cache.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CACHE_HELPER="${PROJECT_ROOT}/bin/test/_cache.bash"

setup() {
    CACHE_DIR="$(mktemp -d)"
    CACHE_FILE="${CACHE_DIR}/plcc-test-units.log"
    export PLCC_TEST_STATS_LOG="${CACHE_DIR}/stats.log"
    unset PLCC_NO_TEST_CACHE
}

teardown() {
    rm -rf "${CACHE_DIR}"
}

@test "cache miss: runs command and creates cache and meta files" {
    run bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo hello 2>/dev/null"
    [ "$status" -eq 0 ]
    [[ "$output" == "hello" ]]
    [ -f "${CACHE_FILE}" ]
    [ -f "${CACHE_FILE}.meta" ]
}

@test "cache miss: output is stored in cache file" {
    bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo cached-output 2>/dev/null" || true
    grep -q "cached-output" "${CACHE_FILE}"
}

@test "cache hit: replays cached output without re-running command" {
    # Prime the cache
    bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo first-run 2>/dev/null" || true
    # Second run — command would print "second-run" but cache should return "first-run"
    run bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo second-run 2>/dev/null"
    [ "$status" -eq 0 ]
    [[ "$output" == "first-run" ]]
}

@test "cache hit: replays non-zero exit code" {
    bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' bash -c 'echo fail-output; exit 42' 2>/dev/null" || true
    run bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo should-not-run 2>/dev/null"
    [ "$status" -eq 42 ]
}

@test "cache miss: non-zero exit code is preserved" {
    run bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' bash -c 'exit 7' 2>/dev/null"
    [ "$status" -eq 7 ]
}

@test "stale cache: reruns command when git state changes" {
    # Prime the cache with a known (wrong) key
    bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo first-run 2>/dev/null" || true
    printf 'KEY=stalekey\nEXIT=0\n' > "${CACHE_FILE}.meta"
    # Next run should be a miss (stale key) and run the new command
    run bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo fresh-run 2>/dev/null"
    [[ "$output" == "fresh-run" ]]
}

@test "PLCC_NO_TEST_CACHE=1: runs command live without caching" {
    export PLCC_NO_TEST_CACHE=1
    run bash -c "export PLCC_NO_TEST_CACHE=1; source '${CACHE_HELPER}'; run_cached '${CACHE_FILE}' echo live-run 2>/dev/null"
    [ "$status" -eq 0 ]
    [[ "$output" == "live-run" ]]
    [ ! -f "${CACHE_FILE}" ]
}

@test "stats log: miss event is written" {
    bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo hello 2>/dev/null" || true
    grep -q " miss units" "${PLCC_TEST_STATS_LOG}"
}

@test "stats log: hit event is written" {
    bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo hello 2>/dev/null" || true
    bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo hello 2>/dev/null" || true
    grep -q " hit units" "${PLCC_TEST_STATS_LOG}"
}

@test "stats log: skip event is written with PLCC_NO_TEST_CACHE=1" {
    bash -c "export PLCC_NO_TEST_CACHE=1; source '${CACHE_HELPER}'; run_cached '${CACHE_FILE}' echo hello 2>/dev/null" || true
    grep -q " skip units" "${PLCC_TEST_STATS_LOG}"
}

@test "stderr: prints [cache miss] on miss" {
    run bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo hello 2>&1 >/dev/null"
    [[ "$output" == *"[cache miss] units"* ]]
}

@test "stderr: prints [cache hit] on hit" {
    bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo hello 2>/dev/null" || true
    run bash -c "source '${CACHE_HELPER}' && run_cached '${CACHE_FILE}' echo hello 2>&1 >/dev/null"
    [[ "$output" == *"[cache hit] units"* ]]
}

@test "stderr: prints [cache skip] with PLCC_NO_TEST_CACHE=1" {
    run bash -c "export PLCC_NO_TEST_CACHE=1; source '${CACHE_HELPER}'; run_cached '${CACHE_FILE}' echo hello 2>&1 >/dev/null"
    [[ "$output" == *"[cache skip] units"* ]]
}

@test "fallback: runs uncached when git is unavailable" {
    run bash -c "
        export PATH=/usr/bin:/bin  # strip git from PATH
        source '${CACHE_HELPER}'
        run_cached '${CACHE_FILE}' echo fallback-output 2>/dev/null
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "fallback-output" ]]
}
```

- [ ] **Step 2: Run tests to verify they all fail**

```bash
bin/test/commands.bash 2>&1 | grep -A3 "cache.bats"
```

Expected: failures like `_cache.bash: No such file or directory`

- [ ] **Step 3: Create `bin/test/_cache.bash`**

```bash
# Sourced by bin/test/*.bash scripts. Not executable.
# Provides run_cached <cache-file> <command> [args...].

_cache_log_event() {
    local event="$1" name="$2"
    local stats_log="${PLCC_TEST_STATS_LOG:-/tmp/plcc-test-cache-stats.log}"
    echo "[cache ${event}] ${name}" >&2
    printf '%s %s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%S)" "${event}" "${name}" \
        >> "${stats_log}"
}

_cache_key() {
    local head status
    head=$(git rev-parse HEAD 2>/dev/null) || return 1
    status=$(git status --porcelain 2>/dev/null) || return 1
    printf '%s\n%s' "${head}" "${status}" | sha256sum | cut -d' ' -f1
}

run_cached() {
    local cache_file="$1"
    shift
    local name
    name=$(basename "${cache_file}" .log)
    name="${name#plcc-test-}"

    if [[ "${PLCC_NO_TEST_CACHE:-}" == "1" ]]; then
        _cache_log_event "skip" "${name}"
        "$@"
        return
    fi

    local key
    if ! key=$(_cache_key); then
        "$@"
        return
    fi

    local meta="${cache_file}.meta"
    if [[ -f "${cache_file}" && -f "${meta}" ]]; then
        local stored_key stored_exit
        stored_key=$(grep '^KEY=' "${meta}" 2>/dev/null | cut -d= -f2-) || true
        stored_exit=$(grep '^EXIT=' "${meta}" 2>/dev/null | cut -d= -f2-) || true
        if [[ "${stored_key}" == "${key}" && "${stored_exit}" =~ ^[0-9]+$ ]]; then
            _cache_log_event "hit" "${name}"
            cat "${cache_file}"
            exit "${stored_exit}"
        fi
    fi

    _cache_log_event "miss" "${name}"
    local exit_code=0
    "$@" 2>&1 | tee "${cache_file}" || exit_code=$?
    printf 'KEY=%s\nEXIT=%s\n' "${key}" "${exit_code}" > "${meta}"
    exit "${exit_code}"
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
bin/test/commands.bash 2>&1 | grep -A3 "cache.bats"
```

Expected: all cache.bats tests pass

- [ ] **Step 5: Commit**

```bash
git add bin/test/_cache.bash tests/bats/commands/cache.bats
git commit -m "feat(097): add _cache.bash with run_cached helper"
```

---

### Task 2: `bin/test/cache-stats.bash` — stats summary script

**Files:**
- Create: `bin/test/cache-stats.bash`
- Create: `tests/bats/commands/cache-stats.bats`

**Interfaces:**
- Consumes: stats log at `${PLCC_TEST_STATS_LOG:-/tmp/plcc-test-cache-stats.log}`, one line per event: `<timestamp> <event> <script>`
- Produces: summary printed to stdout; exit 0 always

---

- [ ] **Step 1: Create the bats test file**

Create `tests/bats/commands/cache-stats.bats`:

```bash
#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CACHE_STATS="${PROJECT_ROOT}/bin/test/cache-stats.bash"

setup() {
    STATS_DIR="$(mktemp -d)"
    export PLCC_TEST_STATS_LOG="${STATS_DIR}/stats.log"
}

teardown() {
    rm -rf "${STATS_DIR}"
}

@test "cache-stats: prints 'no stats yet' when log is missing" {
    run bash "${CACHE_STATS}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"no stats yet"* ]]
}

@test "cache-stats: counts hits, misses, skips correctly" {
    printf '2026-06-18T10:00:00 hit units\n' >> "${PLCC_TEST_STATS_LOG}"
    printf '2026-06-18T10:01:00 miss units\n' >> "${PLCC_TEST_STATS_LOG}"
    printf '2026-06-18T10:02:00 skip e2e\n' >> "${PLCC_TEST_STATS_LOG}"
    run bash "${CACHE_STATS}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Hits: 1"* ]]
    [[ "$output" == *"Misses: 1"* ]]
    [[ "$output" == *"Skips: 1"* ]]
}

@test "cache-stats: computes hit rate" {
    printf '2026-06-18T10:00:00 hit units\n' >> "${PLCC_TEST_STATS_LOG}"
    printf '2026-06-18T10:01:00 hit units\n' >> "${PLCC_TEST_STATS_LOG}"
    printf '2026-06-18T10:02:00 miss units\n' >> "${PLCC_TEST_STATS_LOG}"
    run bash "${CACHE_STATS}"
    [[ "$output" == *"67%"* ]]
}

@test "cache-stats: shows per-script breakdown" {
    printf '2026-06-18T10:00:00 hit units\n' >> "${PLCC_TEST_STATS_LOG}"
    printf '2026-06-18T10:01:00 miss e2e\n' >> "${PLCC_TEST_STATS_LOG}"
    run bash "${CACHE_STATS}"
    [[ "$output" == *"units"* ]]
    [[ "$output" == *"e2e"* ]]
}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
bin/test/commands.bash 2>&1 | grep -A3 "cache-stats.bats"
```

Expected: failures — `cache-stats.bash` not found

- [ ] **Step 3: Create `bin/test/cache-stats.bash`**

```bash
#!/usr/bin/env bash
set -euo pipefail

STATS_LOG="${PLCC_TEST_STATS_LOG:-/tmp/plcc-test-cache-stats.log}"

if [[ ! -f "${STATS_LOG}" ]]; then
    echo "no stats yet"
    exit 0
fi

awk '
{
    event = $2
    script = $3
    total++
    events[event]++
    per_script_total[script]++
    per_script_event[script "_" event]++
}
END {
    hits   = events["hit"]   + 0
    misses = events["miss"]  + 0
    skips  = events["skip"]  + 0
    rate   = (total > 0) ? int(hits / total * 100 + 0.5) : 0
    printf "Total: %d  Hits: %d  Misses: %d  Skips: %d  Hit rate: %d%%\n",
        total, hits, misses, skips, rate
    print ""
    print "Per-script breakdown:"
    for (s in per_script_total) {
        h = per_script_event[s "_hit"]   + 0
        m = per_script_event[s "_miss"]  + 0
        k = per_script_event[s "_skip"]  + 0
        t = per_script_total[s]
        printf "  %-20s  total=%-4d  hits=%-4d  misses=%-4d  skips=%-4d\n",
            s, t, h, m, k
    }
}
' "${STATS_LOG}"
```

- [ ] **Step 4: Make executable and run tests**

```bash
chmod +x bin/test/cache-stats.bash
bin/test/commands.bash 2>&1 | grep -A3 "cache-stats.bats"
```

Expected: all cache-stats.bats tests pass

- [ ] **Step 5: Commit**

```bash
git add bin/test/cache-stats.bash tests/bats/commands/cache-stats.bats
git commit -m "feat(097): add cache-stats.bash summary script"
```

---

### Task 3: Update simple test scripts

Add caching to `units.bash`, `commands.bash`, `integration.bash`, `e2e.bash`, and `packaging.bash`. Each follows the same pattern: source the helper, wrap the main command(s) in `run_cached`.

**Files:**
- Modify: `bin/test/units.bash`
- Modify: `bin/test/commands.bash`
- Modify: `bin/test/integration.bash`
- Modify: `bin/test/e2e.bash`
- Modify: `bin/test/packaging.bash`

**Interfaces:**
- Consumes: `run_cached` from `bin/test/_cache.bash`

---

- [ ] **Step 1: Update `bin/test/units.bash`**

Replace:
```bash
#!/usr/bin/env bash

set -euo pipefail

echo "bin/test/units.bash"
echo "-------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

"${SCRIPT_DIR}/../install/pdm.bash"
pdm install
pdm test -v "$@"
```

With:
```bash
#!/usr/bin/env bash

set -euo pipefail

echo "bin/test/units.bash"
echo "-------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

run_cached /tmp/plcc-test-units.log \
    bash -c '"${SCRIPT_DIR}/../install/pdm.bash" && pdm install && pdm test -v "$@"' \
    -- "$@"
```

Wait — the above passes `$@` through to `pdm test`, but wrapping multiple commands in a `bash -c` string with `"$@"` is tricky. A cleaner approach: wrap in a local function.

Replace `bin/test/units.bash` with:
```bash
#!/usr/bin/env bash

set -euo pipefail

echo "bin/test/units.bash"
echo "-------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    "${SCRIPT_DIR}/../install/pdm.bash"
    pdm install
    pdm test -v "$@"
}

run_cached /tmp/plcc-test-units.log _run "$@"
```

- [ ] **Step 2: Update `bin/test/commands.bash`**

Replace the file with:
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
    "${PROJECT_ROOT}/bin/install/bats.bash"
    pdm install
    export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
    bats tests/bats/commands/
}

run_cached /tmp/plcc-test-commands.log _run
```

- [ ] **Step 3: Update `bin/test/integration.bash`**

Replace the file with:
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
    "${PROJECT_ROOT}/bin/install/bats.bash"
    pdm install
    export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
    bats tests/bats/integration/
}

run_cached /tmp/plcc-test-integration.log _run
```

- [ ] **Step 4: Update `bin/test/e2e.bash`**

Replace the file with:
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
    "${PROJECT_ROOT}/bin/install/bats.bash"
    pdm install
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

- [ ] **Step 5: Update `bin/test/packaging.bash`**

Add the source and wrapper at the top, wrap the body in `_run`, and call `run_cached`. The file is long — make these structural changes:

At the top, after the `cd "${PROJECT_ROOT}"` line, add:
```bash
# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
```

And just before the final `echo "packaging: all checks passed"` line, close the function and add:
```bash
}

run_cached /tmp/plcc-test-packaging.log _run
```

The complete updated `bin/test/packaging.bash`:
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/packaging.bash"
echo "-----------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    VENV=$(mktemp -d)
    trap 'rm -rf "${VENV}"' EXIT

    "${PROJECT_ROOT}/.venv/bin/python" -m venv "${VENV}"
    "${VENV}/bin/pip" install --quiet dist/*.whl

    for cmd in plcc-spec plcc-tokens plcc-trees plcc-model \
               plcc-lang-emit plcc-lang-build plcc-lang-list \
               plcc-diagram plcc-diagram-emit plcc-diagram-build plcc-diagram-run plcc-diagram-list \
               plcc-plantuml-diagram-emit plcc-plantuml-diagram-build plcc-plantuml-diagram-run \
               plcc-make plcc-scan plcc-parse plcc-rep; do
        test -x "${VENV}/bin/${cmd}" || { echo "FAIL: ${cmd} not installed"; exit 1; }
        echo "OK: ${cmd}"
    done

    export PATH="${VENV}/bin:${PATH}"

    LANG_LIST=$("${VENV}/bin/plcc-lang-list")
    echo "${LANG_LIST}" | grep -q "python" || { echo "FAIL: plcc-lang-list missing 'python'"; exit 1; }
    echo "${LANG_LIST}" | grep -q "java"   || { echo "FAIL: plcc-lang-list missing 'java'";   exit 1; }
    echo "OK: plcc-lang-list reports python and java"

    DIAGRAM_LIST=$("${VENV}/bin/plcc-diagram-list")
    echo "${DIAGRAM_LIST}" | grep -q "plantuml" || { echo "FAIL: plcc-diagram-list missing 'plantuml'"; exit 1; }
    echo "OK: plcc-diagram-list reports plantuml"

    WORK_DIR="$(mktemp -d)"
    trap 'rm -rf "${VENV}" "${WORK_DIR}"' EXIT
    (
        cd "${WORK_DIR}"
        cp "${PROJECT_ROOT}/tests/fixtures/trivial.plcc" spec.plcc
        plcc-make
        test -f build/spec.json   || { echo "FAIL: build/spec.json missing"; exit 1; }
        test -f build/model.json  || { echo "FAIL: build/model.json missing"; exit 1; }
    )
    DIAGRAM_DIR="$(mktemp -d)"
    trap 'rm -rf "${VENV}" "${WORK_DIR}" "${DIAGRAM_DIR}"' EXIT
    plcc-spec "${PROJECT_ROOT}/tests/fixtures/arith.plcc" | plcc-model | plcc-plantuml-diagram-emit --output="${DIAGRAM_DIR}"
    test -f "${DIAGRAM_DIR}/diagram.puml" || { echo "FAIL: diagram.puml missing"; exit 1; }
    echo "packaging: all checks passed"
}

run_cached /tmp/plcc-test-packaging.log _run
```

- [ ] **Step 6: Run units to verify nothing is broken**

```bash
bin/test/units.bash
```

Expected: 972 passed (or similar), `[cache miss] units` on stderr, `/tmp/plcc-test-units.log` created

- [ ] **Step 7: Run units a second time to verify cache hit**

```bash
bin/test/units.bash
```

Expected: output replayed instantly, `[cache hit] units` on stderr

- [ ] **Step 8: Commit**

```bash
git add bin/test/units.bash bin/test/commands.bash bin/test/integration.bash \
        bin/test/e2e.bash bin/test/packaging.bash
git commit -m "feat(097): add run_cached to simple test scripts"
```

---

### Task 4: Update composite test scripts

`functional.bash` and `all.bash` call other test scripts. Each sub-script now uses `run_cached` internally. The composites need the same treatment: source the helper, wrap their call sequence in a local function, and pass it to `run_cached`.

**Files:**
- Modify: `bin/test/functional.bash`
- Modify: `bin/test/all.bash`

**Interfaces:**
- Consumes: `run_cached` from `bin/test/_cache.bash`

---

- [ ] **Step 1: Update `bin/test/functional.bash`**

Replace the file with:
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/funcional.bash"
echo "-----------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    "${SCRIPT_DIR}/units.bash"
    "${SCRIPT_DIR}/commands.bash"
    "${SCRIPT_DIR}/integration.bash"
    "${SCRIPT_DIR}/e2e.bash"
}

run_cached /tmp/plcc-test-functional.log _run
```

- [ ] **Step 2: Update `bin/test/all.bash`**

Replace the file with:
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
    "${SCRIPT_DIR}/packaging.bash"
}

run_cached /tmp/plcc-test-all.log _run
```

- [ ] **Step 3: Run units to verify they still pass**

```bash
bin/test/units.bash
```

Expected: pass (cache hit if nothing changed)

- [ ] **Step 4: Commit**

```bash
git add bin/test/functional.bash bin/test/all.bash
git commit -m "feat(097): add run_cached to composite test scripts"
```

---

### Task 5: Update CI to disable caching

All test steps in `.github/workflows/ci.yml` must set `PLCC_NO_TEST_CACHE=1`. This prevents CI from ever reading or writing a cache (the `/tmp` dir is ephemeral per job anyway) and keeps logs free of cache noise.

**Files:**
- Modify: `.github/workflows/ci.yml`

---

- [ ] **Step 1: Update `.github/workflows/ci.yml`**

Add `env: PLCC_NO_TEST_CACHE: "1"` to each test step. Replace the test steps section with:

```yaml
      - name: Run unit tests
        env:
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/units.bash
      - name: Run command tests
        env:
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/commands.bash
      - name: Run integration tests
        env:
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/integration.bash
```

For the `languages-corpus` job:
```yaml
      - name: Run e2e corpus tests
        env:
          LANGUAGES_REPO_PATH: /tmp/languages
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/e2e.bash
```

For the `packaging` job:
```yaml
      - name: Run packaging smoke test
        env:
          PLCC_NO_TEST_CACHE: "1"
        run: bin/test/packaging.bash
```

- [ ] **Step 2: Run units to verify nothing broke**

```bash
bin/test/units.bash
```

Expected: pass

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci(097): disable test output cache in CI with PLCC_NO_TEST_CACHE"
```
