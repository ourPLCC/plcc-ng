#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/tree.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() { rm -f "${SPEC_JSON}"; }

@test "plcc-tree is on PATH" { command -v plcc-tree; }

@test "plcc-tree outputs tree JSONL" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-tree --spec='${SPEC_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | head -1 | check-jsonschema --schemafile "${SCHEMA}" -
}

@test "plcc-tree passes error records through" {
    ERROR=$(python3 -c "import json; print(json.dumps({'kind':'error','stage':'plcc-tokens','source':{'file':None,'line':1,'column':1}}))")
    result=$(echo "${ERROR}" | plcc-tree --spec="${SPEC_JSON}" 2>/dev/null)
    echo "$result" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='error', f\"expected kind=error, got {r['kind']}\""
}
