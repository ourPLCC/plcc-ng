#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    cp "${FIXTURES}/trivial.plcc" spec.plcc
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-parse is on PATH" { command -v plcc-parse; }

@test "plcc-parse --help exits 0" {
    run plcc-parse --help
    [ "$status" -eq 0 ]
}

@test "plcc-parse parses input and prints tree" {
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Program"* ]]
}

@test "plcc-parse reads from source file" {
    run plcc-parse "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Program"* ]]
}

@test "plcc-parse accepts -v" {
    run bash -c "echo '42' | plcc-parse -v"
    [ "$status" -eq 0 ]
}

@test "plcc-parse includes location on token leaves" {
    cp "${FIXTURES}/arith.plcc" spec.plcc
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" =~ NUM\ \'42\'\ \[-:1:1\] ]]
}

@test "plcc-parse reports spec file error from plcc-make" {
    run --separate-stderr bash -c "cd '${WORK_DIR}' && rm spec.plcc && plcc-parse"
    [[ "$stderr" == *"spec file not found"* ]]
}

@test "plcc-parse accepts '-' as stdin" {
    run bash -c "echo '42' | plcc-parse -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Program"* ]]
}

@test "plcc-parse --spec uses specified spec" {
    run bash -c "echo '42' | plcc-parse --spec='${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Program"* ]]
}

@test "plcc-parse exits nonzero when spec has syntax error" {
    printf 'token BAD @@@\n' > spec.plcc
    run --separate-stderr bash -c "echo '42' | plcc-parse"
    [ "$status" -ne 0 ]
}

@test "plcc-parse triggers rebuild when spec changes" {
    echo '42' | plcc-parse > /dev/null
    cp "${FIXTURES}/arith.plcc" spec.plcc
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" =~ NUM ]]
}

@test "plcc-parse works with lexical+syntactic spec and no semantics" {
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Program"* ]]
}

@test "plcc-parse no algorithm terms in output on success" {
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" != *"predict"* ]]
    [[ "$output" != *"shift"* ]]
    [[ "$output" != *"complete"* ]]
}

@test "plcc-parse shows partial tree before error on parse failure" {
    cat > spec.plcc << 'SPEC'
token NUM '\d+'
token PLUS '\+'
skip WS '\s+'
%
<Program> ::= <Expr>
<Expr> ::= NUM PLUS NUM
SPEC
    run bash -c "cd '${WORK_DIR}' && echo '1 +' | plcc-parse"
    [ "$status" -ne 0 ]
    [[ "$output" == *"Program"* ]]
    [[ "$output" == *"NUM"* ]]
    [[ "$output" != *"predict"* ]]
}

@test "plcc-parse partial tree appears before error message" {
    cat > spec.plcc << 'SPEC'
token NUM '\d+'
token PLUS '\+'
skip WS '\s+'
%
<Program> ::= <Expr>
<Expr> ::= NUM PLUS NUM
SPEC
    run bash -c "cd '${WORK_DIR}' && echo '1 +' | plcc-parse"
    [ "$status" -ne 0 ]
    rule_line=$(echo "$output" | grep -n "^Program$" | head -1 | cut -d: -f1)
    error_line=$(echo "$output" | grep -n "error:" | head -1 | cut -d: -f1)
    [ "$rule_line" -lt "$error_line" ]
}

@test "plcc-parse pipe with two sentences produces two trees" {
    run bash -c "printf '3\n4\n' | plcc-parse"
    [ "$status" -eq 0 ]
    count=$(echo "$output" | grep -c "^Program")
    [ "$count" -eq 2 ]
}

@test "plcc-parse pipe with one sentence exits 0 and prints one tree" {
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    count=$(echo "$output" | grep -c "^Program")
    [ "$count" -eq 1 ]
}

@test "plcc-parse splits multiple sentences on same line" {
    run bash -c "printf '3 4\n' | plcc-parse"
    [ "$status" -eq 0 ]
    count=$(echo "$output" | grep -c "^Program")
    [ "$count" -eq 2 ]
}
