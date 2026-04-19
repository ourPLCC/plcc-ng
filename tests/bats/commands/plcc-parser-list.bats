#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-parser-list is on PATH" { command -v plcc-parser-list; }

@test "plcc-parser-list finds plcc-parser-table" {
    run plcc-parser-list
    [ "$status" -eq 0 ]
    [[ "$output" == *"table"* ]]
}

@test "plcc-parser-list accepts --verbose" {
    run plcc-parser-list --verbose=1
    [ "$status" -eq 0 ]
}

@test "plcc-parser-list accepts --verbose-format" {
    run plcc-parser-list --verbose=1 --verbose-format=json
    [ "$status" -eq 0 ]
}
