#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

PROJECT_ROOT="$(git rev-parse --show-toplevel)"

setup() {
    FAKE_BIN="$(mktemp -d)"
    CAPTURED_ARGS="${FAKE_BIN}/captured-args"
    cat > "${FAKE_BIN}/bats" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$@" > "${CAPTURED_ARGS}"
exit 0
EOF
    chmod +x "${FAKE_BIN}/bats"
    export PATH="${FAKE_BIN}:${PATH}"
    export SKIP_SETUP=1
    export PLCC_NO_TEST_CACHE=1
}

teardown() {
    rm -rf "${FAKE_BIN}"
    unset SKIP_SETUP
    unset PLCC_NO_TEST_CACHE
}

@test "commands.bash: path argument narrows bats invocation to that path" {
    "${PROJECT_ROOT}/bin/test/commands.bash" "tests/bats/commands/plcc-make.bats"
    [ "$(cat "${CAPTURED_ARGS}")" = "tests/bats/commands/plcc-make.bats" ]
}

@test "commands.bash: no argument runs the whole tier directory" {
    "${PROJECT_ROOT}/bin/test/commands.bash"
    [ "$(cat "${CAPTURED_ARGS}")" = "tests/bats/commands/" ]
}

@test "integration.bash: path argument narrows bats invocation to that path" {
    "${PROJECT_ROOT}/bin/test/integration.bash" "tests/bats/integration/ll1-tree.bats"
    [ "$(cat "${CAPTURED_ARGS}")" = "tests/bats/integration/ll1-tree.bats" ]
}

@test "integration.bash: no argument runs the whole tier directory" {
    "${PROJECT_ROOT}/bin/test/integration.bash"
    [ "$(cat "${CAPTURED_ARGS}")" = "tests/bats/integration/" ]
}

@test "e2e.bash: path argument bypasses the default file list" {
    "${PROJECT_ROOT}/bin/test/e2e.bash" "tests/bats/e2e/happy-path.bats"
    [ "$(cat "${CAPTURED_ARGS}")" = "tests/bats/e2e/happy-path.bats" ]
}

@test "e2e.bash: no argument runs the default file list, excluding java and haskell roundtrip" {
    "${PROJECT_ROOT}/bin/test/e2e.bash"
    run cat "${CAPTURED_ARGS}"
    [[ "$output" == *"tests/bats/e2e/"* ]]
    [[ "$output" != *"languages-java.bats"* ]]
    [[ "$output" != *"haskell_roundtrip.bats"* ]]
}
