#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/token.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() {
    rm -f "${SPEC_JSON}"
}

@test "plcc-tokens is on PATH" {
    command -v plcc-tokens
}

@test "plcc-tokens --help exits 0" {
    run plcc-tokens --help
    [ "$status" -eq 0 ]
}

@test "plcc-tokens outputs token JSONL for trivial input" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
    # Validate the first (and only) token record against the schema
    echo "$output" | head -1 | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-tokens token record has kind=token" {
    result=$(echo '42' | plcc-tokens "${SPEC_JSON}" | head -1)
    echo "$result" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='token', f\"expected kind=token, got {r['kind']}\""
}

@test "plcc-tokens lex error exits nonzero and writes error to stderr" {
    run --separate-stderr bash -c "echo 'xyz' | plcc-tokens '${SPEC_JSON}'"
    [ "$status" -ne 0 ]
    # stderr carries the error message
    [[ "$stderr" == *"error"* ]]
    [[ "$stderr" == *"plcc-tokens"* ]]
    # stdout has no error records
    for line in $output; do
        [ -z "$line" ] && continue
        echo "$line" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='token', f\"unexpected kind={r['kind']} on stdout\""
    done
}
