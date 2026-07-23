#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/funcional.bash"
echo "-----------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    "${SCRIPT_DIR}/../install/pdm.bash"
    pdm install
    "${SCRIPT_DIR}/../install/bats.bash"

    local path="${1:-}"
    if [[ -z "${path}" ]]; then
        SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash"
        return
    fi

    case "${path}" in
        tests/bats/commands*)    SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash" "${path}" ;;
        tests/bats/integration*) SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash" "${path}" ;;
        tests/bats/e2e*)         SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash" "${path}" ;;
        *)                       SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash" "${path}" ;;
    esac
}

run_cached /tmp/plcc-test-functional.log _run "$@"
