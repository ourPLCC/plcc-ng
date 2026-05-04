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

@test "plcc-lang-emit is on PATH" { command -v plcc-lang-emit; }

@test "plcc-lang-emit missing plugin exits nonzero with message" {
    run --separate-stderr bash -c "cat '${MODEL_JSON}' | plcc-lang-emit --target=NoSuchLang9999 --output='${OUTPUT_DIR}'"
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"No emitter"* ]]
}

@test "plcc-lang-emit Python produces output" {
    run bash -c "cat '${MODEL_JSON}' | plcc-lang-emit --target=Python --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
}
