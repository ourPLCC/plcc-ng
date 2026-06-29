#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-list is on PATH" { command -v plcc-diagram-list; }

@test "plcc-diagram-list exits 0" {
    run plcc-diagram-list
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-list finds syntax/plantuml" {
    run plcc-diagram-list
    [ "$status" -eq 0 ]
    [[ "$output" =~ "syntax/plantuml" ]]
}
