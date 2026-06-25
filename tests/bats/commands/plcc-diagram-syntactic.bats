#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-syntactic is on PATH" { command -v plcc-diagram-syntactic; }

@test "plcc-diagram-syntactic --help exits 0" {
    run plcc-diagram-syntactic --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-syntactic fails when spec file not found" {
    run bash -c "cd /tmp && plcc-diagram-syntactic --spec=nonexistent.plcc"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "spec file not found" ]]
}
