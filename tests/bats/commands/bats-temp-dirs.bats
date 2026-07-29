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

    # Fail loudly rather than silently checking nothing: without this guard,
    # a missing/unreadable bats_dir makes the first grep below error out, and
    # since neither `set -o pipefail` nor `set -e` catches a mid-pipeline
    # failure here, the `|| true` on the pipeline would swallow it and this
    # test would report a false PASS.
    if [ ! -d "${bats_dir}" ]; then
        printf 'Expected bats test directory at %s but found none.\n' "${bats_dir}" >&2
        return 1
    fi

    # awk's index() does a literal substring check at position 1, i.e. an
    # exact "starts with this file's path, then a colon" match. This avoids
    # feeding BATS_TEST_FILENAME (which contains '.' from '.bats' and from
    # this checkout's own path segments) into a grep basic regex, where '.'
    # would match any character instead of a literal dot.
    local offenders
    offenders="$(grep -rn 'mktemp' "${bats_dir}" --include='*.bats' \
        | awk -v self="${BATS_TEST_FILENAME}:" 'index($0, self) != 1' || true)"

    if [ -n "${offenders}" ]; then
        printf 'Do not call mktemp in bats tests. Name a path under\n' >&2
        printf 'BATS_TEST_TMPDIR instead; bats removes it after the test.\n\n' >&2
        printf '%s\n' "${offenders}" >&2
        return 1
    fi
}
