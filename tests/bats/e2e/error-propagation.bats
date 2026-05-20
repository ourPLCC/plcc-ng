#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

# Tests that lex errors are emitted as error records on plcc-tokens stdout.

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    LL1_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-ll1 < "${SPEC_JSON}" > "${LL1_JSON}"
}

teardown() { rm -f "${SPEC_JSON}" "${LL1_JSON}"; }

@test "lex error causes plcc-tokens to exit 0" {
    run bash -c "echo 'abc' | plcc-tokens '${SPEC_JSON}'"
    [ "$status" -eq 0 ]
}

@test "lex error writes error record to stdout" {
    run --separate-stderr bash -c "echo 'abc' | plcc-tokens '${SPEC_JSON}'"
    [ -z "$stderr" ]
    while IFS= read -r line || [ -n "$line" ]; do
        [ -z "$line" ] && continue
        echo "$line" | python3 -c "import json,sys; r=json.load(sys.stdin); exit(0) if r.get('name')=='eof' else None; assert r['kind']=='error', f\"expected kind=error, got {r['kind']}\""
    done <<< "$output"
}

@test "lex error record has expected fields" {
    result=$(echo '@' | plcc-tokens "${SPEC_JSON}" | head -1)
    echo "$result" | python3 -c "
import json, sys
r = json.load(sys.stdin)
assert r['kind'] == 'error'
assert r['stage'] == 'plcc-tokens'
assert r['severity'] == 'error'
assert r['lexeme'] == '@'
assert 'source' in r
assert r['message'] == "unrecognized character '@'"
"
}
