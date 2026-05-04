#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-python.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-python-emit is on PATH" { command -v plcc-python-emit; }

@test "plcc-python-emit produces main.py" {
    plcc-python-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    [ -f "${WORK_DIR}/main.py" ]
}

@test "plcc-python-emit accepts --verbose" {
    run bash -c "plcc-python-emit --output='${WORK_DIR}' --verbose=1 < '${MODEL_JSON}'"
    [ "$status" -eq 0 ]
}
