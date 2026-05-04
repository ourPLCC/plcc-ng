#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
    mkdir -p build
    plcc-spec "${FIXTURES}/trivial-python.plcc" > build/spec.json
    plcc-ll1 < build/spec.json > build/ll1.json
    plcc-spec "${FIXTURES}/trivial-python.plcc" | plcc-model | plcc-python-emit --output=build/py
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
    run bash -c "echo '42' | plcc-rep --tool=py '${FIXTURES}/trivial-python.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == "42" ]]
}

@test "plcc-rep errors on missing tool" {
    run bash -c "echo '42' | plcc-rep --tool=nonexistent '${FIXTURES}/trivial-python.plcc' 2>&1"
    [ "$status" -ne 0 ]
    [[ "$output" == *"no semantic section"* ]]
}

@test "plcc-rep accepts --verbose" {
    run bash -c "echo '42' | plcc-rep --tool=py --verbose=1 '${FIXTURES}/trivial-python.plcc'"
    [ "$status" -eq 0 ]
}
