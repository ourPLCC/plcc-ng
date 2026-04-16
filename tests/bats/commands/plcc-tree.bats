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

teardown() { rm -f "${SPEC_JSON}" "${LL1_JSON}"; }

@test "plcc-tree is on PATH" { command -v plcc-tree; }

@test "plcc-tree --help exits 0" {
    run plcc-tree --help
    [ "$status" -eq 0 ]
}

@test "plcc-tree requires --ll1" {
    run bash -c "echo '{}' | plcc-tree"
    [ "$status" -ne 0 ]
}

@test "plcc-tree dispatches to plcc-parser-table by default" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${TREE_SCHEMA}" -
}

@test "plcc-tree errors on missing parser plugin" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}' --parser=nonexistent 2>&1"
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}

@test "plcc-tree passes error records through" {
    ERROR='{"kind":"error","stage":"plcc-tokens","source":{"file":null,"line":1,"column":1}}'
    run bash -c "echo '${ERROR}' | plcc-tree --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert 'error' in json.dumps(r)"
}

@test "plcc-tree accepts --verbose without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --ll1='${LL1_JSON}' --verbose=1"
    [ "$status" -eq 0 ]
}
