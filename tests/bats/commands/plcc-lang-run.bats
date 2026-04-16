#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-python.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-python-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
}

teardown() { rm -f "${SPEC_JSON}" "${MODEL_JSON}"; rm -rf "${WORK_DIR}"; }

@test "plcc-lang-run is on PATH" { command -v plcc-lang-run; }

@test "plcc-lang-run --help exits 0" {
    run plcc-lang-run --help
    [ "$status" -eq 0 ]
}

@test "plcc-lang-run dispatches to plcc-python-run" {
    TREE='{"kind":"tree","rule":"program","children":[]}'
    run bash -c "echo '${TREE}' | plcc-lang-run --target=Python --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"evaluated"* ]]
}

@test "plcc-lang-run exits 0 for missing runner (no-op)" {
    run plcc-lang-run --target=PlantUML --output="${WORK_DIR}" < /dev/null
    [ "$status" -eq 0 ]
}
