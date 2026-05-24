#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-build is on PATH" { command -v plcc-diagram-build; }

@test "plcc-diagram-build --help exits 0" {
    run plcc-diagram-build --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-build requires --input and --output" {
    run plcc-diagram-build
    [ "$status" -ne 0 ]
}
