#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-parser-list is on PATH" { command -v plcc-parser-list; }

@test "plcc-parser-list finds plcc-parser-table" {
    run plcc-parser-list
    [ "$status" -eq 0 ]
    [[ "$output" == *"table"* ]]
}
