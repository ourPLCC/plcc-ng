#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-diagram-mermaid-run is on PATH" {
    command -v plcc-diagram-mermaid-run
}

@test "plcc-diagram-mermaid-run --help exits 0" {
    run plcc-diagram-mermaid-run --help
    [ "$status" -eq 0 ]
}

@test "plcc-diagram-mermaid-run requires --input" {
    run plcc-diagram-mermaid-run
    [ "$status" -ne 0 ]
}
