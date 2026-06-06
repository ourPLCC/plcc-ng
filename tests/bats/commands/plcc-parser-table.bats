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

@test "plcc-parser-table accepts -v without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' -v"
    [ "$status" -eq 0 ]
}

@test "plcc-parser-table accepts --verbose-format without error" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' -v --verbose-format=json"
    [ "$status" -eq 0 ]
}

@test "plcc-parser-table output has kind=tree" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='tree', r['kind']"
}

@test "plcc-parser-table output has rule=Program" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['rule']=='Program', r['rule']"
}

@test "plcc-parser-table output has source span" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | python3 -c "
import json,sys
r=json.load(sys.stdin)
src=r['source']
assert 'line' in src and 'endLine' in src, src
"
}

@test "plcc-parser-table passes lex error records through and exits 0" {
    run bash -c "echo 'not_a_num' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    echo "$output" | python3 -c "
import json, sys
records = [json.loads(l) for l in sys.stdin if l.strip()]
assert len(records) >= 1, 'expected at least one output record'
assert all(r['kind'] == 'error' for r in records), f'all records should be errors, got {records}'
"
}

@test "plcc-parser-table --trace emits parse-step JSONL records" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"kind": "parse-step"'* ]] || [[ "$output" == *'"kind":"parse-step"'* ]]
}

@test "plcc-parser-table --trace parse-step records come before tree record" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' --trace"
    [ "$status" -eq 0 ]
    first_step=$(echo "$output" | grep -n "parse-step" | head -1 | cut -d: -f1)
    tree_line=$(echo "$output" | grep -n '"kind":"tree"\|"kind": "tree"' | head -1 | cut -d: -f1)
    [ "$first_step" -lt "$tree_line" ]
}

@test "plcc-parser-table without --trace no parse-step on success" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}'"
    [ "$status" -eq 0 ]
    [[ "$output" != *"parse-step"* ]]
}

@test "plcc-parser-table -t is short for --trace" {
    run bash -c "echo '42' | plcc-tokens '${SPEC_JSON}' | plcc-parser-table --ll1='${LL1_JSON}' -t"
    [ "$status" -eq 0 ]
    [[ "$output" == *"parse-step"* ]]
}
