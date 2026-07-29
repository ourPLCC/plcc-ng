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
    plcc-python-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
}

@test "plcc-python-run is on PATH" { command -v plcc-python-run; }

@test "plcc-python-run evaluates parse-tree JSONL and returns eval record" {
    TREE='{"kind":"tree","rule":"Program","children":[["num",{"kind":"token","name":"NUM","lexeme":"42"}]]}'
    run bash -c "echo '${TREE}' | plcc-python-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"value"'* ]]
    [[ "$output" == *'42'* ]]
}

@test "plcc-python-run exits 0 on empty input" {
    run bash -c "echo '' | plcc-python-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
}
