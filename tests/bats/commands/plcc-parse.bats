#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-parse is on PATH" { command -v plcc-parse; }

@test "plcc-parse --help exits 0" {
    run plcc-parse --help
    [ "$status" -eq 0 ]
}

@test "plcc-parse parses input and prints tree" {
    run bash -c "echo '42' | plcc-parse '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse reads from source file" {
    run plcc-parse "${FIXTURES}/trivial.plcc" "${FIXTURES}/trivial_input.txt"
    [ "$status" -eq 0 ]
    [[ "$output" == *"program"* ]]
}

@test "plcc-parse accepts --verbose" {
    run bash -c "echo '42' | plcc-parse --verbose=1 '${FIXTURES}/trivial.plcc'"
    [ "$status" -eq 0 ]
}

@test "plcc-parse includes location on token leaves" {
    run bash -c "echo '42' | plcc-parse '${FIXTURES}/arith.plcc'"
    [ "$status" -eq 0 ]
    [[ "$output" =~ NUM\ \'42\'\ \[1:1\] ]]
}
