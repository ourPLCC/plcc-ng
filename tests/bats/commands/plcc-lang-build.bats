#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    OUTPUT_DIR="$(mktemp -d)"
}

teardown() {
    rm -rf "${OUTPUT_DIR}"
}

@test "plcc-lang-build is on PATH" { command -v plcc-lang-build; }

@test "plcc-lang-build exits 0 for language with no build command" {
    run plcc-lang-build --target=PlantUML --output="${OUTPUT_DIR}"
    [ "$status" -eq 0 ]
}
