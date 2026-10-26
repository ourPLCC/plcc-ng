#!/usr/bin/env bash
set -euo pipefail

# Install the Backlog.md version pinned in the shared dev clone's
# .backlog-version, unless it is already installed. With --check, install
# nothing: warn when the installed version differs, and always succeed, so a
# container start never fails on it. Idempotent.
#
# OURPLCC_DEV overrides the dev clone's path, for tests.

DEV="${OURPLCC_DEV:-/workspaces/dev}"
VERSION_FILE="${DEV}/.backlog-version"

installed_version() {
    if command -v backlog &>/dev/null; then
        backlog --version
    fi
}

if [[ "${1:-}" == "--check" ]]; then
    pinned="$(cat "${VERSION_FILE}" 2>/dev/null || true)"
    installed="$(installed_version)"
    if [[ "${installed}" != "${pinned}" ]]; then
        echo "backlog.bash: installed backlog is '${installed:-none}'," \
             "but ${VERSION_FILE} pins '${pinned:-nothing}';" \
             "run bin/install/backlog.bash" >&2
    fi
    exit 0
fi

if [[ ! -f "${VERSION_FILE}" ]]; then
    echo "backlog.bash: ${VERSION_FILE} is missing;" \
         "run bin/install/shared-clones.bash first" >&2
    exit 1
fi
pinned="$(cat "${VERSION_FILE}")"
# The version reaches npm's command line, so accept nothing but X.Y.Z.
if [[ ! "${pinned}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "backlog.bash: ${VERSION_FILE} holds '${pinned}', not a plain X.Y.Z version" >&2
    exit 1
fi

if [[ "$(installed_version)" == "${pinned}" ]]; then
    exit 0
fi
npm i -g "backlog.md@${pinned}"
