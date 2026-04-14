#!/usr/bin/env bats

@test "plcc-lang-build is on PATH" { command -v plcc-lang-build; }

@test "plcc-lang-build exits 0 for language with no build command" {
    run plcc-lang-build --target=PlantUML --output=/tmp
    [ "$status" -eq 0 ]
}
