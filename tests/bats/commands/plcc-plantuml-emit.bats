#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    MODEL_JSON="$(mktemp)"
    OUTPUT_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-model "${SPEC_JSON}" > "${MODEL_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}" "${MODEL_JSON}"
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-plantuml-emit is on PATH" { command -v plcc-plantuml-emit; }

@test "plcc-plantuml-emit creates a .puml file" {
    run bash -c "cat '${MODEL_JSON}' | plcc-plantuml-emit --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
    ls "${OUTPUT_DIR}"/*.puml
}

@test "plcc-plantuml-emit puml contains class name" {
    bash -c "cat '${MODEL_JSON}' | plcc-plantuml-emit --output='${OUTPUT_DIR}'"
    grep -r 'Program' "${OUTPUT_DIR}"/*.puml
}
