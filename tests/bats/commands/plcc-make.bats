#!/usr/bin/env bats

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "plcc-make is on PATH" { command -v plcc-make; }

@test "plcc-make --help exits 0" {
    run plcc-make --help
    [ "$status" -eq 0 ]
}

@test "plcc-make no args exits nonzero" {
    run plcc-make
    [ "$status" -ne 0 ]
}

@test "plcc-make plantuml_only grammar produces build artifacts" {
    run plcc-make "${FIXTURES}/plantuml_only.plcc"
    [ "$status" -eq 0 ]
    [ -f "${WORK_DIR}/build/spec.json" ]
    [ -f "${WORK_DIR}/build/model.json" ]
    ls "${WORK_DIR}/build/diagram/"*.puml
}
