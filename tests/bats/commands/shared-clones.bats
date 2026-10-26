#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    PROJECT_ROOT="$(git rev-parse --show-toplevel)"
    SCRIPT="${PROJECT_ROOT}/bin/install/shared-clones.bash"

    export GIT_AUTHOR_NAME=test GIT_AUTHOR_EMAIL=test@example.com
    export GIT_COMMITTER_NAME=test GIT_COMMITTER_EMAIL=test@example.com
    export TMPDIR="${BATS_TEST_TMPDIR}/tmp"
    mkdir -p "${TMPDIR}"

    export OURPLCC_DEV_URL="${BATS_TEST_TMPDIR}/dev.git"
    export OURPLCC_CHANGE_REQUESTS_URL="${BATS_TEST_TMPDIR}/cr.git"
    export OURPLCC_DEV="${BATS_TEST_TMPDIR}/dev"
    export OURPLCC_CHANGE_REQUESTS="${BATS_TEST_TMPDIR}/cr"
    export OURPLCC_LOCK_DIR="${OURPLCC_DEV}"
    mkdir -p "${OURPLCC_DEV}" "${OURPLCC_CHANGE_REQUESTS}"

    seed "${OURPLCC_DEV_URL}" .githooks/pre-commit
    seed "${OURPLCC_CHANGE_REQUESTS_URL}" backlog/config.yml
}

# seed BARE FILE: create a bare repo whose main holds one commit adding FILE.
seed() {
    git init -q --bare -b main "$1"
    upstream_commit "$1" "$2"
}

# upstream_commit BARE FILE: push a new commit touching FILE to BARE's main.
upstream_commit() {
    local work="${BATS_TEST_TMPDIR}/work-$RANDOM"
    git clone -q "$1" "${work}" 2>/dev/null
    git -C "${work}" checkout -q -B main
    mkdir -p "$(dirname "${work}/$2")"
    echo "$RANDOM" >> "${work}/$2"
    git -C "${work}" add -A
    git -C "${work}" commit -q -m "change $2"
    git -C "${work}" push -q origin main
}

head_of() {
    git -C "$1" rev-parse "${2:-HEAD}"
}

@test "clones both repos into empty directories" {
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(head_of "${OURPLCC_DEV}")" = "$(head_of "${OURPLCC_DEV_URL}" main)" ]
    [ "$(head_of "${OURPLCC_CHANGE_REQUESTS}")" = "$(head_of "${OURPLCC_CHANGE_REQUESTS_URL}" main)" ]
}

@test "points change-requests' hooks at dev's .githooks" {
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(git -C "${OURPLCC_CHANGE_REQUESTS}" config core.hooksPath)" = "${OURPLCC_DEV}/.githooks" ]
}

@test "leaves existing clones in place" {
    "${SCRIPT}"
    touch "${OURPLCC_CHANGE_REQUESTS}/marker"
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ -e "${OURPLCC_CHANGE_REQUESTS}/marker" ]
}

@test "recovers from an interrupted clone" {
    git init -q "${OURPLCC_DEV}"
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(head_of "${OURPLCC_DEV}")" = "$(head_of "${OURPLCC_DEV_URL}" main)" ]
    leftover=("${TMPDIR}"/ourplcc-dev-leftover.*)
    [ -d "${leftover[0]}/.git" ]
    [[ "$output" == *"${leftover[0]}"* ]]
}

@test "moves stray files aside before cloning" {
    echo stray > "${OURPLCC_CHANGE_REQUESTS}/stray.txt"
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(head_of "${OURPLCC_CHANGE_REQUESTS}")" = "$(head_of "${OURPLCC_CHANGE_REQUESTS_URL}" main)" ]
    leftover=("${TMPDIR}"/ourplcc-change-requests-leftover.*)
    [ -f "${leftover[0]}/stray.txt" ]
    [ ! -e "${OURPLCC_CHANGE_REQUESTS}/stray.txt" ]
}

@test "fast-forwards dev's main when clean" {
    "${SCRIPT}"
    upstream_commit "${OURPLCC_DEV_URL}" bin/check.py
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(head_of "${OURPLCC_DEV}")" = "$(head_of "${OURPLCC_DEV_URL}" main)" ]
}

@test "does not move dev when its tree is dirty" {
    "${SCRIPT}"
    before="$(head_of "${OURPLCC_DEV}")"
    echo edit >> "${OURPLCC_DEV}/.githooks/pre-commit"
    upstream_commit "${OURPLCC_DEV_URL}" bin/check.py
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(head_of "${OURPLCC_DEV}")" = "${before}" ]
}

@test "does not move dev when it is on another branch" {
    "${SCRIPT}"
    before="$(head_of "${OURPLCC_DEV}")"
    git -C "${OURPLCC_DEV}" checkout -q -b topic
    upstream_commit "${OURPLCC_DEV_URL}" bin/check.py
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(head_of "${OURPLCC_DEV}" main)" = "${before}" ]
    [ "$(git -C "${OURPLCC_DEV}" branch --show-current)" = topic ]
}

@test "does not move dev when it has local commits" {
    "${SCRIPT}"
    echo local >> "${OURPLCC_DEV}/.githooks/pre-commit"
    git -C "${OURPLCC_DEV}" commit -q -am local
    before="$(head_of "${OURPLCC_DEV}")"
    upstream_commit "${OURPLCC_DEV_URL}" bin/check.py
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(head_of "${OURPLCC_DEV}")" = "${before}" ]
    [ -n "$output" ]
}

@test "never pulls change-requests" {
    "${SCRIPT}"
    before="$(head_of "${OURPLCC_CHANGE_REQUESTS}")"
    upstream_commit "${OURPLCC_CHANGE_REQUESTS_URL}" backlog/config.yml
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(head_of "${OURPLCC_CHANGE_REQUESTS}")" = "${before}" ]
    [ "$(head_of "${OURPLCC_CHANGE_REQUESTS}" origin/main)" = "${before}" ]
}

@test "warns but succeeds when the fetch fails" {
    "${SCRIPT}"
    git -C "${OURPLCC_DEV}" remote set-url origin "${BATS_TEST_TMPDIR}/missing.git"
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ -n "$output" ]
}

@test "fails when a clone fails" {
    export OURPLCC_DEV_URL="${BATS_TEST_TMPDIR}/missing.git"
    run "${SCRIPT}"
    [ "$status" -eq 1 ]
    [[ "$output" == *shared-clones.bash* ]]
}

@test "times out when another holder has the lock" {
    flock "${OURPLCC_LOCK_DIR}" sleep 5 >/dev/null 2>&1 3>&- &
    while flock -n "${OURPLCC_LOCK_DIR}" true; do sleep 0.1; done
    OURPLCC_LOCK_WAIT=1 run "${SCRIPT}"
    [ "$status" -eq 1 ]
    [[ "$output" == *lock* ]]
}
