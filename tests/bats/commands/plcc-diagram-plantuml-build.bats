#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-plantuml-build is on PATH" {
    command -v plcc-diagram-plantuml-build
}

@test "plcc-diagram-plantuml-build --help exits 0" {
    run plcc-diagram-plantuml-build --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-plantuml-build requires --input and --output" {
    run plcc-diagram-plantuml-build
    [ "$status" -ne 0 ]
}
