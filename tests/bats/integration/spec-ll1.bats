#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    LL1_SCHEMA="$(git rev-parse --show-toplevel)/src/plcc/schemas/ll1.schema.json"
}

@test "plcc-spec | plcc-ll1 produces schema-valid ll1 JSON" {
    run bash -c "plcc-spec '${FIXTURES}/trivial.plcc' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${LL1_SCHEMA}" -
}

# --- repetition rules (**=) ---------------------------------------------
#
# Three body shapes, three paths through _handle_arbno in
# src/plcc/ll1/spec_json_decoder.py: a separator form, a non-capturing
# terminal between two capturing symbols, and a non-capturing terminal
# leading the body. Issue 174 dropped every non-capturing terminal from
# arbno.<nt>.rhs, which in the leading case also shifted
# arbno.<nt>.lookahead onto the wrong symbol.

@test "plcc-spec | plcc-ll1 on a separator arbno grammar produces schema-valid ll1 JSON" {
    run bash -c "plcc-spec '${FIXTURES}/trivial-arbno.plcc' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${LL1_SCHEMA}" -
}

@test "separator arbno: rhs, separator, and lookahead are correct" {
    result=$(plcc-spec "${FIXTURES}/trivial-arbno.plcc" | plcc-ll1)
    echo "$result" | python3 -c "
import json, sys
arbno = json.load(sys.stdin)['arbno']
assert arbno['Rands'] == {
    'rhs': [{'field': 'exprList', 'symbol': 'Expr', 'is_terminal': False}],
    'separator': 'COMMA',
    'lookahead': ['NUM', 'PLUS'],
}, arbno['Rands']
"
}

@test "mid-body-terminal arbno: plcc-spec | plcc-ll1 produces schema-valid ll1 JSON" {
    run bash -c "plcc-spec '${FIXTURES}/arbno-mid-body-terminal.plcc' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${LL1_SCHEMA}" -
}

@test "mid-body-terminal arbno: rhs keeps the non-capturing terminal (issue 174)" {
    result=$(plcc-spec "${FIXTURES}/arbno-mid-body-terminal.plcc" | plcc-ll1)
    echo "$result" | python3 -c "
import json, sys
arbno = json.load(sys.stdin)['arbno']
assert arbno['Decls']['rhs'] == [
    {'field': 'symbolList', 'symbol': 'SYMBOL', 'is_terminal': True},
    {'field': None, 'symbol': 'EQUALS', 'is_terminal': True},
    {'field': 'expList', 'symbol': 'Exp', 'is_terminal': False},
], arbno['Decls']['rhs']
"
}

@test "mid-body-terminal arbno: lookahead is the first body symbol" {
    result=$(plcc-spec "${FIXTURES}/arbno-mid-body-terminal.plcc" | plcc-ll1)
    echo "$result" | python3 -c "
import json, sys
arbno = json.load(sys.stdin)['arbno']
assert arbno['Decls']['lookahead'] == ['SYMBOL'], arbno['Decls']['lookahead']
"
}

@test "leading-terminal arbno: plcc-spec | plcc-ll1 produces schema-valid ll1 JSON" {
    run bash -c "plcc-spec '${FIXTURES}/arbno-leading-terminal.plcc' | plcc-ll1"
    [ "$status" -eq 0 ]
    echo "$output" | check-jsonschema --schemafile "${LL1_SCHEMA}" -
}

@test "leading-terminal arbno: rhs keeps the leading non-capturing terminal (issue 174)" {
    result=$(plcc-spec "${FIXTURES}/arbno-leading-terminal.plcc" | plcc-ll1)
    echo "$result" | python3 -c "
import json, sys
arbno = json.load(sys.stdin)['arbno']
assert arbno['Items']['rhs'] == [
    {'field': None, 'symbol': 'BANG', 'is_terminal': True},
    {'field': 'expList', 'symbol': 'Exp', 'is_terminal': False},
], arbno['Items']['rhs']
"
}

@test "leading-terminal arbno: lookahead is the leading terminal, not the first capture (issue 174)" {
    result=$(plcc-spec "${FIXTURES}/arbno-leading-terminal.plcc" | plcc-ll1)
    echo "$result" | python3 -c "
import json, sys
arbno = json.load(sys.stdin)['arbno']
assert arbno['Items']['lookahead'] == ['BANG'], arbno['Items']['lookahead']
"
}
