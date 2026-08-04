#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

# bats' default `run` merges stderr into stdout, so every "$output" comparison
# below asserts the command emitted nothing beyond the documented text on either
# stream. That is deliberate and stricter than the page's claim: a stray banner
# or deprecation notice on stderr should fail this tier, not slip past it. If one
# does, fix the new output — do not reach for --separate-stderr.

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures/docs"
    WORK_DIR="${BATS_TEST_TMPDIR}/work"
    mkdir -p "${WORK_DIR}"
    cd "${WORK_DIR}"
}

# docs/language-guide/examples.md names its files subtract.plcc and samples,
# and passes both explicitly on the command line. Fixtures are stored under
# the uniform spec.plcc/input names, so rename on the way in.
_use() {
    FIXTURE="${FIXTURES}/$1"
    cp "${FIXTURE}/spec.plcc" subtract.plcc
    cp "${FIXTURE}/input" samples
}

@test "subtraction example Python: plcc-scan matches the documented output" {
    _use lang-guide-examples-python
    run plcc-scan -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-scan")" ]
}

@test "subtraction example Python: plcc-parse matches the documented output" {
    _use lang-guide-examples-python
    run plcc-parse -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-parse")" ]
}

@test "subtraction example Python: plcc-rep matches the documented output and exits 0" {
    _use lang-guide-examples-python
    run plcc-rep -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}

@test "subtraction example Java: plcc-scan matches the documented output" {
    _use lang-guide-examples-java
    run plcc-scan -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-scan")" ]
}

@test "subtraction example Java: plcc-parse matches the documented output" {
    _use lang-guide-examples-java
    run plcc-parse -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-parse")" ]
}

@test "subtraction example Java: plcc-rep matches the documented output and exits 0" {
    _use lang-guide-examples-java
    run plcc-rep -s subtract.plcc samples
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}
