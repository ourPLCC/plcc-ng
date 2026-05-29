#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
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
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse reads from source file" {
    run plcc-parse "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse accepts -v" {
    run bash -c "echo '42' | plcc-parse -v"
    [ "$status" -eq 0 ]
}

@test "plcc-parse includes location on token leaves" {
    cp "${FIXTURES}/arith.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" =~ NUM\ \'42\'\ \[-:1:1\] ]]
}

@test "plcc-parse brief usage mentions --help" {
    run --separate-stderr bash -c "cd '${WORK_DIR}' && rm grammar.plcc && plcc-parse"
    [[ "$stderr" == *"--help"* ]]
}

@test "plcc-parse accepts '-' as stdin" {
    run bash -c "echo '42' | plcc-parse -"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse --grammar-file uses specified grammar" {
    run bash -c "echo '42' | plcc-parse --grammar-file='${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse exits nonzero when grammar has syntax error" {
    printf 'token BAD @@@\n' > grammar.plcc
    run --separate-stderr bash -c "echo '42' | plcc-parse"
    [ "$status" -ne 0 ]
}

@test "plcc-parse triggers rebuild when grammar changes" {
    echo '42' | plcc-parse > /dev/null
    cp "${FIXTURES}/arith.plcc" grammar.plcc
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" =~ NUM ]]
}

@test "plcc-parse works with lexical+syntactic grammar and no semantics" {
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse --trace shows predict in output" {
    run bash -c "echo '42' | plcc-parse --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"predict"* ]]
}

@test "plcc-parse --trace shows shift in output" {
    run bash -c "echo '42' | plcc-parse --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"shift"* ]]
    [[ "$output" == *"42"* ]]
}

@test "plcc-parse --trace shows complete in output" {
    run bash -c "echo '42' | plcc-parse --trace"
    [ "$status" -eq 0 ]
    [[ "$output" == *"complete"* ]]
}

@test "plcc-parse --trace trace appears before tree" {
    run bash -c "echo '42' | plcc-parse --trace"
    [ "$status" -eq 0 ]
    predict_line=$(echo "$output" | grep -n "predict" | head -1 | cut -d: -f1)
    program_line=$(echo "$output" | grep -n "^program" | head -1 | cut -d: -f1)
    [ "$predict_line" -lt "$program_line" ]
}

@test "plcc-parse -t is short for --trace" {
    run bash -c "echo '42' | plcc-parse -t"
    [ "$status" -eq 0 ]
    [[ "$output" == *"predict"* ]]
}

@test "plcc-parse no trace on success without --trace" {
    run bash -c "echo '42' | plcc-parse"
    [ "$status" -eq 0 ]
    [[ "$output" != *"predict"* ]]
    [[ "$output" != *"shift"* ]]
    [[ "$output" != *"complete"* ]]
}

@test "plcc-parse shows trace on parse failure without --trace" {
    cp "${FIXTURES}/arith.plcc" grammar.plcc
    run bash -c "cd '${WORK_DIR}' && echo '1 +' | plcc-parse"
    [ "$status" -ne 0 ]
    [[ "$output" == *"predict"* ]]
    [[ "$output" == *"shift"* ]]
}

@test "plcc-parse failure trace appears before error message" {
    cp "${FIXTURES}/arith.plcc" grammar.plcc
    run bash -c "cd '${WORK_DIR}' && echo '1 +' | plcc-parse"
    [ "$status" -ne 0 ]
    predict_line=$(echo "$output" | grep -n "predict" | head -1 | cut -d: -f1)
    error_line=$(echo "$output" | grep -n "error:" | head -1 | cut -d: -f1)
    [ "$predict_line" -lt "$error_line" ]
}
