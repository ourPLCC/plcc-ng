#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    PROJECT_ROOT="$(git rev-parse --show-toplevel)"
    SCRIPT="${PROJECT_ROOT}/bin/install/backlog.bash"
    export OURPLCC_DEV="${BATS_TEST_TMPDIR}/dev"
    mkdir -p "${OURPLCC_DEV}"
    NPM_LOG="${BATS_TEST_TMPDIR}/npm.log"
    STUB_BIN="${BATS_TEST_TMPDIR}/bin"
    mkdir -p "${STUB_BIN}"
    cat > "${STUB_BIN}/npm" <<EOF
#!/usr/bin/env bash
echo "\$*" >> "${NPM_LOG}"
EOF
    chmod +x "${STUB_BIN}/npm"
    # Only the stubs and the system tools: the real backlog and npm live
    # elsewhere, so a test that adds no backlog stub sees none installed.
    export PATH="${STUB_BIN}:/usr/bin:/bin"
}

pin() {
    echo "$1" > "${OURPLCC_DEV}/.backlog-version"
}

installed() {
    cat > "${STUB_BIN}/backlog" <<EOF
#!/usr/bin/env bash
echo "$1"
EOF
    chmod +x "${STUB_BIN}/backlog"
}

@test "installs the pinned version" {
    pin 1.53.0
    installed 1.52.0
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(cat "${NPM_LOG}")" = "i -g backlog.md@1.53.0" ]
}

@test "installs the pinned version when backlog is not installed" {
    pin 1.53.0
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(cat "${NPM_LOG}")" = "i -g backlog.md@1.53.0" ]
}

@test "skips install when already at the pinned version" {
    pin 1.53.0
    installed 1.53.0
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ ! -e "${NPM_LOG}" ]
}

@test "rejects a version that is not X.Y.Z" {
    pin '1.53.0; rm -rf /'
    installed 1.52.0
    run "${SCRIPT}"
    [ "$status" -eq 1 ]
    [ ! -e "${NPM_LOG}" ]
}

@test "fails when the version file is missing" {
    installed 1.52.0
    run "${SCRIPT}"
    [ "$status" -eq 1 ]
    [ ! -e "${NPM_LOG}" ]
}

@test "--check warns on a mismatch" {
    pin 1.53.0
    installed 1.52.0
    run "${SCRIPT}" --check
    [ "$status" -eq 0 ]
    [[ "$output" == *1.52.0* ]]
    [[ "$output" == *1.53.0* ]]
    [ ! -e "${NPM_LOG}" ]
}

@test "--check is silent when versions match" {
    pin 1.53.0
    installed 1.53.0
    run "${SCRIPT}" --check
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "--check warns but succeeds when backlog --version fails" {
    pin 1.53.0
    cat > "${STUB_BIN}/backlog" <<EOF
#!/usr/bin/env bash
exit 1
EOF
    chmod +x "${STUB_BIN}/backlog"
    run "${SCRIPT}" --check
    [ "$status" -eq 0 ]
    [ -n "$output" ]
}

@test "--check warns when backlog is not installed" {
    pin 1.53.0
    run "${SCRIPT}" --check
    [ "$status" -eq 0 ]
    [ -n "$output" ]
    [ ! -e "${NPM_LOG}" ]
}
