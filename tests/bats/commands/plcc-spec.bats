#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/spec.schema.json"
    BAD_SPEC="$(mktemp --suffix=.plcc)"
}

teardown() {
    rm -f "${BAD_SPEC}"
}

@test "plcc-spec is on PATH" {
    command -v plcc-spec
}

@test "plcc-spec --help exits 0 and prints Usage" {
    run plcc-spec --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
}

@test "plcc-spec no args exits nonzero" {
    run plcc-spec
    [ "$status" -ne 0 ]
}

@test "plcc-spec trivial grammar outputs valid JSON" {
    run plcc-spec "${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    echo "$output" | python3 -m json.tool > /dev/null
}

@test "plcc-spec trivial grammar output validates against spec schema" {
    run plcc-spec "${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-spec bad grammar exits nonzero and writes to stderr" {
    echo "num 'bad'" > "${BAD_SPEC}"
    run --separate-stderr plcc-spec "${BAD_SPEC}"
    [ "$status" -ne 0 ]
    [ -n "$stderr" ]
}

@test "plcc-spec malformed syntactic rule: stderr includes source line and caret" {
    printf "token NUM '\\\\d+'\n%%\n<Program>IfStmt ::= NUM\n" > "${BAD_SPEC}"
    run --separate-stderr plcc-spec "${BAD_SPEC}"
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"<Program>IfStmt ::= NUM"* ]]
    [[ "$stderr" == *"         ^"* ]]
}
