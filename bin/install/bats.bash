#!/usr/bin/env bash
set -euo pipefail

BATS_VERSION="1.11.0"
INSTALL_DIR="${HOME}/.local/lib/bats"
BIN_DIR="${HOME}/.local/bin"

versions() {
    SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
    "${SCRIPT_DIR}/../versions.bash"
}

if command -v bats &>/dev/null && bats --version | grep -q "${BATS_VERSION}"; then
    versions
    exit 0
fi

mkdir -p "${INSTALL_DIR}" "${BIN_DIR}"
TMPDIR=$(mktemp -d)
trap 'rm -rf "${TMPDIR}"' EXIT

git clone --depth 1 --branch "v${BATS_VERSION}" \
    https://github.com/bats-core/bats-core.git "${TMPDIR}/bats"
"${TMPDIR}/bats/install.sh" "${HOME}/.local"

versions
