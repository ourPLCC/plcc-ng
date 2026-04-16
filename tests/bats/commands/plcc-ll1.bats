#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/ll1.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() { rm -f "${SPEC_JSON}"; }

@test "plcc-ll1 is on PATH" { command -v plcc-ll1; }

@test "plcc-ll1 --help exits 0" {
    run plcc-ll1 --help
    [ "$status" -eq 0 ]
}

@test "plcc-ll1 produces schema-valid output" {
    run plcc-ll1 "${SPEC_JSON}"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-ll1 reads from stdin" {
    run bash -c "cat '${SPEC_JSON}' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-ll1 accepts --verbose without error" {
    run plcc-ll1 --verbose=1 "${SPEC_JSON}"
    [ "$status" -eq 0 ]
}

@test "plcc-ll1 accepts --verbose-format without error" {
    run plcc-ll1 --verbose=1 --verbose-format=json "${SPEC_JSON}"
    [ "$status" -eq 0 ]
}
