#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-plantuml-diagram-run is on PATH" {
    command -v plcc-plantuml-diagram-run
}

@test "plcc-plantuml-diagram-run --help exits 0" {
    run plcc-plantuml-diagram-run --help
    [ "$status" -eq 0 ]
}

@test "plcc-plantuml-diagram-run requires --input" {
    run plcc-plantuml-diagram-run
    [ "$status" -ne 0 ]
}
