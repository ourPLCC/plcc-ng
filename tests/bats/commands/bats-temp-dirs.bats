#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "bats removes BATS_TEST_TMPDIR when the run ends" {
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
    if [ ! -d "${bats_dir}" ] || [ ! -r "${bats_dir}" ]; then
        printf 'Expected a readable bats test directory at %s but found none.\n' "${bats_dir}" >&2
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
        printf 'BATS_TEST_TMPDIR instead; bats removes it when the run ends.\n\n' >&2
        printf '%s\n' "${offenders}" >&2
        return 1
    fi
}

@test "every bats test file declares the required bats version" {
    local required='bats_require_minimum_version 1.5.0'
    local bats_dir
    bats_dir="$(git rev-parse --show-toplevel)/tests/bats"

    if [ ! -d "${bats_dir}" ] || [ ! -r "${bats_dir}" ]; then
        printf 'Expected a readable bats test directory at %s but found none.\n' "${bats_dir}" >&2
        return 1
    fi

    # This lint needs no self-exclusion, unlike the mktemp one above: its own
    # file already satisfies the rule it enforces.
    #
    # sed prints nothing for a file shorter than three lines, which compares
    # unequal to ${required} and is correctly reported. No special case needed.
    local offenders='' scanned=0 file
    while IFS= read -r -d '' file; do
        scanned=$(( scanned + 1 ))
        if [ "$(sed -n '3p' -- "${file}")" != "${required}" ]; then
            offenders+="${file}"$'\n'
        fi
    done < <(find "${bats_dir}" -name '*.bats' -type f -print0 | sort -z)

    # A readable directory with no .bats files inside would leave ${offenders}
    # empty and report a false PASS. Same reasoning as the guard above: fail
    # loudly rather than silently check nothing.
    if [ "${scanned}" -eq 0 ]; then
        printf 'Found no .bats files under %s. This lint checked nothing.\n' "${bats_dir}" >&2
        return 1
    fi

    if [ -n "${offenders}" ]; then
        printf 'Every bats test file must declare the bats version floor, as\n' >&2
        printf 'line 3, exactly:\n\n    %s\n\n' "${required}" >&2
        printf 'BATS_TEST_TMPDIR requires bats 1.4.0 or later. Without the\n' >&2
        printf 'declaration an older runner leaves it unset, and paths under it\n' >&2
        printf 'silently resolve outside the sandbox instead of failing.\n\n' >&2
        printf 'Missing the declaration:\n\n%s' "${offenders}" >&2
        return 1
    fi
}
