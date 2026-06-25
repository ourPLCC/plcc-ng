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

@test "plcc-diagram-class-plantuml-emit is on PATH" {
    command -v plcc-diagram-class-plantuml-emit
}

@test "plcc-diagram-class-plantuml-emit creates diagram.puml" {
    run bash -c "cat '${MODEL_JSON}' | plcc-diagram-class-plantuml-emit --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
    [ -f "${OUTPUT_DIR}/diagram.puml" ]
}

@test "diagram.puml contains ExprRest" {
    bash -c "cat '${MODEL_JSON}' | plcc-diagram-class-plantuml-emit --output='${OUTPUT_DIR}'"
    grep 'ExprRest' "${OUTPUT_DIR}/diagram.puml"
}

@test "diagram.puml contains inheritance arrow" {
    bash -c "cat '${MODEL_JSON}' | plcc-diagram-class-plantuml-emit --output='${OUTPUT_DIR}'"
    grep 'ExprRest <|-- AddRest' "${OUTPUT_DIR}/diagram.puml"
}
