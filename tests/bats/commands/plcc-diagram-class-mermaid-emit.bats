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

@test "plcc-diagram-class-mermaid-emit is on PATH" {
    command -v plcc-diagram-class-mermaid-emit
}

@test "plcc-diagram-class-mermaid-emit emits classDiagram" {
    run bash -c "cat '${MODEL_JSON}' | plcc-diagram-class-mermaid-emit"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "classDiagram" ]]
}
