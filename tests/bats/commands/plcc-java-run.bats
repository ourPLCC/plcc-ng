#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="${BATS_TEST_TMPDIR}/work"
    mkdir -p "${WORK_DIR}"
    SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"
    MODEL_JSON="${BATS_TEST_TMPDIR}/model.json"
    plcc-spec "${FIXTURES}/trivial-java.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    plcc-java-build --output="${WORK_DIR}"
}

@test "plcc-java-run is on PATH" { command -v plcc-java-run; }

@test "plcc-java-run evaluates parse-tree JSONL" {
    TREE='{"kind":"tree","rule":"Program","children":[["num",{"kind":"token","name":"NUM","lexeme":"42"}]]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"42"* ]]
    [[ "$output" == *'"kind"'* ]]
    [[ "$output" == *'"result"'* ]]
}
