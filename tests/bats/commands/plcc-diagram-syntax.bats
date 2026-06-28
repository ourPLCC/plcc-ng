#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-syntax is on PATH" { command -v plcc-diagram-syntax; }

@test "plcc-diagram-syntax --help exits 0" {
    run plcc-diagram-syntax --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-syntax fails when spec file not found" {
    run bash -c "cd /tmp && plcc-diagram-syntax --spec=nonexistent.plcc"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "spec file not found" ]]
}
