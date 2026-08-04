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

# This page shows a specification but no commands, so there is nothing to
# reproduce beyond running it. input and expected-rep are authored in the
# fixture rather than transcribed from the page.
_use() {
    FIXTURE="${FIXTURES}/$1"
    cp "${FIXTURE}/spec.plcc" spec.plcc
}

@test "language guide overview Python: the example runs and exits 0" {
    _use lang-guide-index-python
    run plcc-rep < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}

@test "language guide overview Java: the example runs and exits 0" {
    _use lang-guide-index-java
    run plcc-rep < "${FIXTURE}/input"
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${FIXTURE}/expected-rep")" ]
}
