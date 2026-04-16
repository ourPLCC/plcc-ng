#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    TREE_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/tree.schema.json"
    SPEC_JSON="$(mktemp)"
    LL1_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-ll1 "${SPEC_JSON}" > "${LL1_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}" "${LL1_JSON}"
}

@test "plcc-parser-table is on PATH" { command -v plcc-parser-table; }

@test "plcc-parser-table --help exits 0" {
    run plcc-parser-table --help
    [ "$status" -eq 0 ]
}

@test "plcc-parser-table requires --ll1" {
    run bash -c "echo '{}' | plcc-parser-table"
    [ "$status" -ne 0 ]
}

@test "plcc-parser-table produces schema-valid tree" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${TREE_SCHEMA}" -
}

@test "plcc-parser-table accepts --verbose without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' --verbose=1"
    [ "$status" -eq 0 ]
}

@test "plcc-parser-table accepts --verbose-format without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' --verbose=1 --verbose-format=json"
    [ "$status" -eq 0 ]
}
