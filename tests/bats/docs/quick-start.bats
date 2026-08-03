#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures/docs"
    WORK_DIR="${BATS_TEST_TMPDIR}/work"
    mkdir -p "${WORK_DIR}"
    cd "${WORK_DIR}"
}

# Lay a fixture out the way docs/quick-start.md tells the reader to: a
# spec.plcc in the working directory, found by automatic discovery, with
# program text arriving on stdin.
_use() {
    FIXTURE="${FIXTURES}/$1"
    cp "${FIXTURE}/spec.plcc" spec.plcc
}

@test "quick-start Python: plcc-scan matches the documented output" {
    _use quick-start-python
    run plcc-scan < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-scan")" ]
}

@test "quick-start Python: plcc-parse matches the documented output" {
    _use quick-start-python
    run plcc-parse < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-parse")" ]
}

@test "quick-start Python: plcc-rep matches the documented output and exits 0" {
    _use quick-start-python
    run plcc-rep < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}

@test "quick-start Java: plcc-scan matches the documented output" {
    _use quick-start-java
    run plcc-scan < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-scan")" ]
}

@test "quick-start Java: plcc-parse matches the documented output" {
    _use quick-start-java
    run plcc-parse < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-parse")" ]
}

@test "quick-start Java: plcc-rep matches the documented output and exits 0" {
    _use quick-start-java
    run plcc-rep < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}
