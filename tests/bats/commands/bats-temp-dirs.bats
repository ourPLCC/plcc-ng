#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "bats removes BATS_TEST_TMPDIR after a test" {
    local probe="${BATS_TEST_TMPDIR}/inner.bats"
    local record="${BATS_TEST_TMPDIR}/recorded"

    cat > "${probe}" << EOF
@test "inner records its tmpdir" {
    printf '%s' "\${BATS_TEST_TMPDIR}" > "${record}"
}
EOF

    # 3>&- closes bats' TAP pass-through fd. Without it the nested run
    # writes its own TAP to fd 3 and corrupts this run's test count.
    run bats "${probe}" 3>&-
    [ "$status" -eq 0 ]
    [ -s "${record}" ]

    local inner
    inner="$(cat "${record}")"
    [ ! -e "${inner}" ]
}
