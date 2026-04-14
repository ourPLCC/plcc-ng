#!/usr/bin/env bats

@test "plcc-lang-list is on PATH" { command -v plcc-lang-list; }

@test "plcc-lang-list exits 0" {
    run plcc-lang-list
    [ "$status" -eq 0 ]
}

@test "plcc-lang-list finds plantuml" {
    run plcc-lang-list
    [[ "$output" == *"plantuml"* ]]
}
