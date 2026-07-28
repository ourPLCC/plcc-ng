#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"
    OUTPUT_DIR="${BATS_TEST_TMPDIR}/output"
    mkdir -p "${OUTPUT_DIR}"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

@test "plcc-model | plcc-lang-emit --target=Python produces output" {
    run bash -c "plcc-model '${SPEC_JSON}' | plcc-lang-emit --target=Python --output='${OUTPUT_DIR}'"
    [ "$status" -eq 0 ]
}
