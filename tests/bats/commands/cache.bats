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
    local fake_bin
    fake_bin=$(mktemp -d)
    printf '#!/usr/bin/env bash\nexit 1\n' > "${fake_bin}/git"
    chmod +x "${fake_bin}/git"
    run bash -c "
        export PATH='${fake_bin}':\"${PATH}\"
        source '${CACHE_HELPER}'
        run_cached '${CACHE_FILE}' echo fallback-output 2>/dev/null
    "
    [ "$status" -eq 0 ]
    [[ "$output" == "fallback-output" ]]
    [ ! -f "${CACHE_FILE}" ]
    rm -rf "${fake_bin}"
}
