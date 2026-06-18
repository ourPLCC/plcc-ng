#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
CACHE_STATS="${PROJECT_ROOT}/bin/test/cache/stats.bash"

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
