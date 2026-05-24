#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-run is on PATH" { command -v plcc-diagram-run; }

@test "plcc-diagram-run --help exits 0" {
    run plcc-diagram-run --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-run requires --input" {
    run plcc-diagram-run
    [ "$status" -ne 0 ]
}
