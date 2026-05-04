#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    LL1_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/ll1.schema.json"
}

@test "plcc-spec | plcc-ll1 produces schema-valid ll1 JSON" {
    run bash -c "plcc-spec '${FIXTURES}/trivial.plcc' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${LL1_SCHEMA}" -
}
