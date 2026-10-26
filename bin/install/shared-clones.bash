#!/usr/bin/env bash
# Clone ourPLCC/dev and ourPLCC/change-requests into the shared named volumes
# every ourPLCC container mounts at /workspaces/dev and
# /workspaces/change-requests, point change-requests' hooks at dev's reviewed
# .githooks, and fast-forward dev's main when it is clean. Never pulls
# change-requests: dev's bin/push.bash does. Holds a lock on the ourplcc-dev
# volume's mount point, the same lock bin/push.bash takes. Run from
# postCreateCommand and postStartCommand. Idempotent; rerun it to recover from
# a failed clone.
#
# The OURPLCC_* variables below are for tests.
set -euo pipefail

DEV="${OURPLCC_DEV:-/workspaces/dev}"
CHANGE_REQUESTS="${OURPLCC_CHANGE_REQUESTS:-/workspaces/change-requests}"
DEV_URL="${OURPLCC_DEV_URL:-https://github.com/ourPLCC/dev}"
CHANGE_REQUESTS_URL="${OURPLCC_CHANGE_REQUESTS_URL:-https://github.com/ourPLCC/change-requests}"
LOCK_DIR="${OURPLCC_LOCK_DIR:-/workspaces/dev}"

say() {
    echo "shared-clones.bash: $*" >&2
}

die() {
    say "$@"
    exit 1
}

# Re-run under the lock. -o keeps the lock's descriptor in flock alone, so a
# child that outlives this script (git maintenance, detached by fetch) does
# not hold it; -w turns a stuck holder into an error.
if [[ -z "${OURPLCC_SHARED_CLONES_LOCKED:-}" ]]; then
    status=0
    OURPLCC_SHARED_CLONES_LOCKED=1 flock -o -w "${OURPLCC_LOCK_WAIT:-120}" -E 75 \
        "${LOCK_DIR}" bash "${BASH_SOURCE[0]}" "$@" || status=$?
    [[ "${status}" -ne 75 ]] \
        || die "timed out waiting for the lock on ${LOCK_DIR};" \
               "another clone or push holds it. Rerun bin/install/shared-clones.bash"
    exit "${status}"
fi
unset OURPLCC_SHARED_CLONES_LOCKED

# ensure_clone NAME URL DIR: make DIR, a volume's mount point, a clone of URL.
ensure_clone() {
    local name="$1" url="$2" dir="$3"
    # Docker creates a new volume owned by root.
    [[ -O "${dir}" ]] || sudo chown "$(id -u):$(id -g)" "${dir}"
    if git -C "${dir}" rev-parse --verify --quiet HEAD &>/dev/null; then
        return
    fi
    # The mount point itself cannot move, and git clone needs it empty, so an
    # interrupted clone's remains go to a temporary directory.
    if [[ -n "$(ls -A "${dir}")" ]]; then
        local leftover
        leftover="$(mktemp -d "${TMPDIR:-/tmp}/ourplcc-${name}-leftover.XXXXXX")"
        (shopt -s dotglob && mv "${dir}"/* "${leftover}/")
        say "moved what was in ${dir} to ${leftover}"
    fi
    git clone --quiet "${url}" "${dir}" \
        || die "could not clone ${url} into ${dir};" \
               "rerun bin/install/shared-clones.bash once you are online"
}

ensure_clone dev "${DEV_URL}" "${DEV}"
ensure_clone change-requests "${CHANGE_REQUESTS_URL}" "${CHANGE_REQUESTS}"

git -C "${CHANGE_REQUESTS}" config core.hooksPath "${DEV}/.githooks"

# Keep every container on dev's reviewed tooling and rules, but never touch
# work in progress there.
if [[ "$(git -C "${DEV}" symbolic-ref --quiet --short HEAD || true)" != main \
    || -n "$(git -C "${DEV}" status --porcelain)" ]]; then
    say "${DEV} is not a clean checkout of main; not updating it"
elif ! git -C "${DEV}" fetch --quiet origin; then
    say "could not fetch ${DEV}; it may be out of date"
elif ! git -C "${DEV}" merge --ff-only --quiet origin/main; then
    say "could not fast-forward ${DEV}'s main to origin/main;" \
        "it has commits of its own"
fi
