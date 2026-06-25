#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-mermaid-build is on PATH" {
    command -v plcc-diagram-mermaid-build
}

@test "plcc-diagram-mermaid-build --help exits 0" {
    run plcc-diagram-mermaid-build --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-mermaid-build requires --input and --output" {
    run plcc-diagram-mermaid-build
    [ "$status" -ne 0 ]
}
