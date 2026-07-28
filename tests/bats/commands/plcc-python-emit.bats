#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="${BATS_TEST_TMPDIR}/work"
    mkdir -p "${WORK_DIR}"
    SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"
    MODEL_JSON="${BATS_TEST_TMPDIR}/model.json"
    plcc-spec "${FIXTURES}/trivial-python.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
}

@test "plcc-python-emit is on PATH" { command -v plcc-python-emit; }

@test "plcc-python-emit produces main.py" {
    plcc-python-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    [ -f "${WORK_DIR}/main.py" ]
}

@test "plcc-python-emit accepts -v" {
    run bash -c "plcc-python-emit --output='${WORK_DIR}' -v < '${MODEL_JSON}'"
    [ "$status" -eq 0 ]
}
