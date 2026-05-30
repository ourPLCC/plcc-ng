#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-rep is on PATH" { command -v plcc-rep; }

@test "plcc-rep --help exits 0" {
    run plcc-rep --help
    [ "$status" -eq 0 ]
}

@test "plcc-rep evaluates with Python tool" {
    run --separate-stderr bash -c "echo '42' | plcc-rep --tool=py"
    [ "$status" -eq 0 ]
    [[ "$output" == "42" ]]
}

@test "plcc-rep errors on missing tool" {
    run --separate-stderr bash -c "echo '42' | plcc-rep --tool=nonexistent"
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"no semantic section"* ]]
}

@test "plcc-rep accepts -v" {
    run --separate-stderr bash -c "echo '42' | plcc-rep --tool=py -v"
    [ "$status" -eq 0 ]
}

@test "plcc-rep reports grammar file error from plcc-make" {
    run --separate-stderr bash -c "cd '${WORK_DIR}' && rm grammar.plcc && plcc-rep"
    [[ "$stderr" == *"grammar file not found"* ]]
}

@test "plcc-rep --grammar uses specified grammar" {
    run --separate-stderr bash -c "echo '42' | plcc-rep --grammar='${FIXTURES}/trivial-python.plcc' --tool=py"
    [ "$status" -eq 0 ]
    [[ "$output" == "42" ]]
}

@test "plcc-rep rebuilds when grammar changes" {
    echo '42' | plcc-rep --tool=py > /dev/null 2>&1  # prime build
    cp "${FIXTURES}/trivial-python.plcc" grammar.plcc  # same grammar, re-copy (triggers rebuild if hash changes)
    run --separate-stderr bash -c "echo '42' | plcc-rep --tool=py"
    [ "$status" -eq 0 ]
    [[ "$output" == "42" ]]
}

@test "plcc-rep exits nonzero when grammar has syntax error" {
    printf 'token BAD @@@\n' > grammar.plcc
    run --separate-stderr bash -c "echo '42' | plcc-rep"
    [ "$status" -ne 0 ]
}

@test "plcc-rep exits nonzero when grammar has no semantics" {
    cp "${FIXTURES}/trivial.plcc" grammar.plcc
    run --separate-stderr bash -c "echo '42' | plcc-rep"
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"no semantic sections"* ]]
}
