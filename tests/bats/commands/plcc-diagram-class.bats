#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-class is on PATH" { command -v plcc-diagram-class; }

@test "plcc-diagram-class --help exits 0" {
    run plcc-diagram-class --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-class fails when spec file not found" {
    run bash -c "cd /tmp && plcc-diagram-class --spec=nonexistent.plcc"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "spec file not found" ]]
}
