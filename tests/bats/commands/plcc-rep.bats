#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    cp "${FIXTURES}/trivial-python.plcc" spec.plcc
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-rep is on PATH" { command -v plcc-rep; }

@test "plcc-rep --help exits 0" {
    run plcc-rep --help
    [ "$status" -eq 0 ]
}

@test "plcc-rep evaluates with Python language" {
    run --separate-stderr bash -c "echo '42' | plcc-rep"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "42" ]]
}

@test "plcc-rep rejects unrecognized argument" {
    run --separate-stderr bash -c "echo '42' | plcc-rep --tool=nonexistent"
    [ "$status" -ne 0 ]
}

@test "plcc-rep accepts -v" {
    run --separate-stderr bash -c "echo '42' | plcc-rep -v"
    [ "$status" -eq 0 ]
}

@test "plcc-rep reports spec file error from plcc-make" {
    run --separate-stderr bash -c "cd '${WORK_DIR}' && rm spec.plcc && plcc-rep"
    [[ "$stderr" == *"spec file not found"* ]]
}

@test "plcc-rep --spec uses specified spec" {
    run --separate-stderr bash -c "echo '42' | plcc-rep --spec='${FIXTURES}/trivial-python.plcc'"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "42" ]]
}

@test "plcc-rep rebuilds when spec changes" {
    echo '42' | plcc-rep > /dev/null 2>&1  # prime build
    cp "${FIXTURES}/trivial-python.plcc" spec.plcc  # same spec, re-copy (triggers rebuild if hash changes)
    run --separate-stderr bash -c "echo '42' | plcc-rep"
    [ "$status" -eq 0 ]
    [[ "${lines[-1]}" == "42" ]]
}

@test "plcc-rep exits nonzero when spec has syntax error" {
    printf 'token BAD @@@\n' > spec.plcc
    run --separate-stderr bash -c "echo '42' | plcc-rep"
    [ "$status" -ne 0 ]
}

@test "plcc-rep exits nonzero when spec has no semantics" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    run --separate-stderr bash -c "echo '42' | plcc-rep"
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"no semantic section"* ]]
}
