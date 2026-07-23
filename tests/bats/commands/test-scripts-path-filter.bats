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

setup_functional_stub_tree() {
    STUB_ROOT="$(mktemp -d)"
    mkdir -p "${STUB_ROOT}/bin/test" "${STUB_ROOT}/bin/install"
    cp "${PROJECT_ROOT}/bin/test/functional.bash" "${STUB_ROOT}/bin/test/functional.bash"
    cp "${PROJECT_ROOT}/bin/test/_cache.bash" "${STUB_ROOT}/bin/test/_cache.bash"
    ROUTE_LOG="${STUB_ROOT}/route-log"
    for tier in units commands integration e2e; do
        cat > "${STUB_ROOT}/bin/test/${tier}.bash" <<EOF
#!/usr/bin/env bash
printf '${tier} %s\n' "\$*" >> "${ROUTE_LOG}"
EOF
        chmod +x "${STUB_ROOT}/bin/test/${tier}.bash"
    done
    for installer in pdm bats; do
        cat > "${STUB_ROOT}/bin/install/${installer}.bash" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
        chmod +x "${STUB_ROOT}/bin/install/${installer}.bash"
    done
    FAKE_PDM_BIN="$(mktemp -d)"
    printf '#!/usr/bin/env bash\nexit 0\n' > "${FAKE_PDM_BIN}/pdm"
    chmod +x "${FAKE_PDM_BIN}/pdm"
    export PATH="${FAKE_PDM_BIN}:${PATH}"
}

@test "functional.bash: commands-tier path routes only to commands.bash" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash" "tests/bats/commands/plcc-make.bats"
    [ "$(cat "${ROUTE_LOG}")" = "commands tests/bats/commands/plcc-make.bats" ]
}

@test "functional.bash: integration-tier path routes only to integration.bash" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash" "tests/bats/integration/ll1-tree.bats"
    [ "$(cat "${ROUTE_LOG}")" = "integration tests/bats/integration/ll1-tree.bats" ]
}

@test "functional.bash: e2e-tier path routes only to e2e.bash" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash" "tests/bats/e2e/happy-path.bats"
    [ "$(cat "${ROUTE_LOG}")" = "e2e tests/bats/e2e/happy-path.bats" ]
}

@test "functional.bash: non-bats-tier path routes only to units.bash" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash" "src/plcc/cmd/make_test.py"
    [ "$(cat "${ROUTE_LOG}")" = "units src/plcc/cmd/make_test.py" ]
}

@test "functional.bash: no argument runs all four sub-scripts" {
    setup_functional_stub_tree
    "${STUB_ROOT}/bin/test/functional.bash"
    run cat "${ROUTE_LOG}"
    [[ "$output" == *"units "* ]]
    [[ "$output" == *"commands "* ]]
    [[ "$output" == *"integration "* ]]
    [[ "$output" == *"e2e "* ]]
}
