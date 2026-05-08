#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial-java.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
}

teardown() { rm -rf "${WORK_DIR}" "${SPEC_JSON}" "${MODEL_JSON}"; }

@test "plcc-java-emit is on PATH" { command -v plcc-java-emit; }

@test "plcc-java-emit produces Program.java" {
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    [ -f "${WORK_DIR}/Program.java" ]
}

@test "plcc-java-emit produces Main.java" {
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    [ -f "${WORK_DIR}/Main.java" ]
}

@test "plcc-java-emit copies runtime directory" {
    plcc-java-emit --output="${WORK_DIR}" < "${MODEL_JSON}"
    [ -f "${WORK_DIR}/runtime/Node.java" ]
    [ -f "${WORK_DIR}/runtime/Token.java" ]
    [ -f "${WORK_DIR}/runtime/Registry.java" ]
    [ -f "${WORK_DIR}/runtime/Deserializer.java" ]
    ls "${WORK_DIR}/runtime/org.json"*.jar
}

@test "plcc-java-emit accepts -v" {
    run bash -c "plcc-java-emit --output='${WORK_DIR}' -v < '${MODEL_JSON}'"
    [ "$status" -eq 0 ]
}
