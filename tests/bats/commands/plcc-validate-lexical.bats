#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-validate-lexical is on PATH" {
    command -v plcc-validate-lexical
}

@test "plcc-validate-lexical --help exits 0 and prints Usage" {
    run plcc-validate-lexical --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
}

@test "plcc-validate-lexical exits 0 for valid spec" {
    run bash -c "plcc-spec '${FIXTURES}/trivial.plcc' | plcc-validate-lexical"
    [ "$status" -eq 0 ]
}

@test "plcc-validate-lexical exits 0 for spec with semantic section" {
    run bash -c "plcc-spec '${FIXTURES}/trivial-python.plcc' | plcc-validate-lexical"
    [ "$status" -eq 0 ]
}
