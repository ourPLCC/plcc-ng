#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    TOKEN_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/token.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() { rm -f "${SPEC_JSON}"; }

@test "plcc-spec output feeds plcc-tokens successfully" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
}

@test "spec->tokens pipeline output validates against token schema" {
    result=$(echo '42' | plcc-tokens "${SPEC_JSON}")
    echo "$result" | head -1 | check-jsonschema --schemafile "${TOKEN_SCHEMA}" -
}
