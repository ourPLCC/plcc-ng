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

@test "no bats test file calls mktemp" {
    local bats_dir
    bats_dir="$(git rev-parse --show-toplevel)/tests/bats"

    local offenders
    offenders="$(grep -rn 'mktemp' "${bats_dir}" --include='*.bats' \
        | grep -v "^${BATS_TEST_FILENAME}:" || true)"

    if [ -n "${offenders}" ]; then
        printf 'Do not call mktemp in bats tests. Name a path under\n' >&2
        printf 'BATS_TEST_TMPDIR instead; bats removes it after the test.\n\n' >&2
        printf '%s\n' "${offenders}" >&2
        return 1
    fi
}
