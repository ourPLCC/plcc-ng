#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram is on PATH" { command -v plcc-diagram; }

@test "plcc-diagram --help exits 0" {
    run plcc-diagram --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram --help describes type discovery" {
    run plcc-diagram --help
    [[ "$output" =~ "installed diagram types" ]]
}

@test "plcc-diagram fails when spec file not found" {
    run bash -c "cd /tmp && plcc-diagram --spec=nonexistent.plcc"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "spec file not found" ]]
}
