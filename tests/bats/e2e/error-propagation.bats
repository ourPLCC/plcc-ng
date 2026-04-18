#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

# Tests that lex errors cause plcc-tokens to exit nonzero and write to stderr.

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    LL1_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-ll1 "${SPEC_JSON}" > "${LL1_JSON}"
}

teardown() { rm -f "${SPEC_JSON}" "${LL1_JSON}"; }

@test "lex error causes plcc-tokens to exit nonzero" {
    run bash -c "echo 'abc' | plcc-tokens '${SPEC_JSON}'"
    [ "$status" -ne 0 ]
}

@test "lex error writes error message to stderr" {
    run --separate-stderr bash -c "echo 'abc' | plcc-tokens '${SPEC_JSON}'"
    [[ "$stderr" == *"error"* ]]
    [[ "$stderr" == *"plcc-tokens"* ]]
}

@test "lex error produces no error records on stdout" {
    run --separate-stderr bash -c "echo 'abc' | plcc-tokens '${SPEC_JSON}'"
    for line in $output; do
        [ -z "$line" ] && continue
        echo "$line" | python3 -c "import json,sys; r=json.load(sys.stdin); assert r['kind']=='token', f\"unexpected kind={r['kind']} on stdout\""
    done
}
