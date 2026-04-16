#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    if ! command -v javac &>/dev/null; then skip "JDK not available"; fi
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-java.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    plcc-java-build --output="${WORK_DIR}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-java-run is on PATH" { command -v plcc-java-run; }

@test "plcc-java-run evaluates parse-tree JSONL" {
    TREE='{"kind":"tree","rule":"program","children":[]}'
    run bash -c "echo '${TREE}' | plcc-java-run --output='${WORK_DIR}'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"evaluated: program (tree)"* ]]
}
