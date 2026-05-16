#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    TREE_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/tree.schema.json"
    SPEC_JSON="$(mktemp)"
    LL1_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-ll1 < "${SPEC_JSON}" > "${LL1_JSON}"
}

teardown() { rm -f "${SPEC_JSON}" "${LL1_JSON}"; }

@test "plcc-tokens | plcc-trees with ll1 produces schema-valid tree" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-trees --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${TREE_SCHEMA}" -
}

@test "plcc-tokens | plcc-trees with ll1 produces tree with rule=program" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-trees --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['rule']=='program'"
}

@test "plcc-tokens | plcc-trees with ll1 output has source span" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-trees --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | python3 -c "
import json,sys
r=json.load(sys.stdin)
assert 'endLine' in r['source'], r['source']
"
}
