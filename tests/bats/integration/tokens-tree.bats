#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    TREE_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/tree.schema.json"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() { rm -f "${SPEC_JSON}"; }

@test "tokens->tree pipeline produces valid tree JSONL" {
    result=$(echo '42' | plcc-tokens "${SPEC_JSON}" | plcc-tree --spec="${SPEC_JSON}")
    echo "$result" | head -1 | check-jsonschema --schemafile "${TREE_SCHEMA}" -
}

@test "lex error from tokens passes through tree unchanged" {
    result=$(echo 'xyz' | plcc-tokens "${SPEC_JSON}" | plcc-tree --spec="${SPEC_JSON}" 2>/dev/null)
    echo "$result" | head -1 | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='error'"
}
