#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/model.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}"
}

@test "plcc-model is on PATH" {
    command -v plcc-model
}

@test "plcc-model --help exits 0" {
    run plcc-model --help
    [ "$status" -eq 0 ]
}

@test "plcc-model output validates against model schema" {
    run plcc-model "${SPEC_JSON}"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-model output has Program class" {
    result=$(plcc-model "${SPEC_JSON}")
    echo "$result" | python3 -c "
import json, sys
m = json.load(sys.stdin)
names = [c['name'] for c in m['classes']]
assert 'Program' in names, f'Expected Program in {names}'
"
}

@test "plcc-model reads from stdin with -" {
    run bash -c "cat '${SPEC_JSON}' | plcc-model -"
    [ "$status" -eq 0 ]
}
