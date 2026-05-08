#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-parser-list is on PATH" { command -v plcc-parser-list; }

@test "plcc-parser-list finds plcc-parser-table" {
    run plcc-parser-list
    [ "$status" -eq 0 ]
    [[ "$output" == *"table"* ]]
}

@test "plcc-parser-list accepts -v" {
    run plcc-parser-list -v
    [ "$status" -eq 0 ]
}

@test "plcc-parser-list accepts --verbose-format" {
    run plcc-parser-list -v --verbose-format=json
    [ "$status" -eq 0 ]
}
