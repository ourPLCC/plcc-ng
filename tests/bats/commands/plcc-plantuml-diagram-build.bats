#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-plantuml-diagram-build is on PATH" {
    command -v plcc-plantuml-diagram-build
}

@test "plcc-plantuml-diagram-build --help exits 0" {
    run plcc-plantuml-diagram-build --help
    [ "$status" -eq 0 ]
}

@test "plcc-plantuml-diagram-build requires --input and --output" {
    run plcc-plantuml-diagram-build
    [ "$status" -ne 0 ]
}
