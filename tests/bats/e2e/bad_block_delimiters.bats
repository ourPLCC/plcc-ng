#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-make --through=model exits nonzero for spec with bad block delimiters" {
    run --separate-stderr plcc-make --spec="${FIXTURES}/bad-delimiters.plcc" --through=model
    [ "$status" -ne 0 ]
}

@test "plcc-make error mentions the offending line content" {
    run --separate-stderr plcc-make --spec="${FIXTURES}/bad-delimiters.plcc" --through=model
    [[ "$stderr" == *"%%{"* ]]
}

@test "plcc-make error does not mention FileNotFoundError" {
    run --separate-stderr plcc-make --spec="${FIXTURES}/bad-delimiters.plcc" --through=model
    [[ "$stderr" != *"FileNotFoundError"* ]]
}

@test "plcc-make --through=scan succeeds for spec with bad block delimiters" {
    run plcc-make --spec="${FIXTURES}/bad-delimiters.plcc" --through=scan
    [ "$status" -eq 0 ]
}
