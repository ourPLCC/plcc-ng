#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram is on PATH" { command -v plcc-diagram; }

@test "plcc-diagram --help exits 0" {
    run plcc-diagram --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram fails when grammar file not found" {
    run bash -c "cd /tmp && plcc-diagram --grammar=nonexistent.plcc"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "grammar file not found" ]]
}
