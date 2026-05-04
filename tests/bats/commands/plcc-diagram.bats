#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    MODEL_JSON="$(mktemp)"
    OUTPUT_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/arith.plcc" | plcc-model > "${MODEL_JSON}"
}

teardown() {
    rm -f "${MODEL_JSON}"
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-diagram is on PATH" { command -v plcc-diagram; }

@test "plcc-diagram creates diagram.puml with default plantuml format" {
    run bash -c "cat '${MODEL_JSON}' | plcc-diagram --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
    [ -f "${OUTPUT_DIR}/diagram.puml" ]
}

@test "plcc-diagram --format=plantuml creates diagram.puml" {
    run bash -c "cat '${MODEL_JSON}' | plcc-diagram --output='${OUTPUT_DIR}' --format=plantuml"
    [ "$status" -eq 0 ]
    [ -f "${OUTPUT_DIR}/diagram.puml" ]
}

@test "plcc-diagram fails for unknown format" {
    run bash -c "cat '${MODEL_JSON}' | plcc-diagram --output='${OUTPUT_DIR}' --format=nonexistent"
    [ "$status" -ne 0 ]
}
