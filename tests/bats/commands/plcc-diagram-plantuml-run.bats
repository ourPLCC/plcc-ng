#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-plantuml-run is on PATH" {
    command -v plcc-diagram-plantuml-run
}

@test "plcc-diagram-plantuml-run --help exits 0" {
    run plcc-diagram-plantuml-run --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-plantuml-run requires --input" {
    run plcc-diagram-plantuml-run
    [ "$status" -ne 0 ]
}
