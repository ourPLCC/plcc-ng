#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    OUTPUT_DIR="$(mktemp -d)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}"
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-model | plcc-lang-emit produces puml file" {
    run bash -c "plcc-model '${SPEC_JSON}' | plcc-lang-emit --target=PlantUML --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
    ls "${OUTPUT_DIR}"/*.puml
}
