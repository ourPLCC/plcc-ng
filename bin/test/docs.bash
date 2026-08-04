#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/docs.bash"
echo "------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    cd "${PROJECT_ROOT}"
    if [[ -z "${SKIP_SETUP:-}" ]]; then
        "${PROJECT_ROOT}/bin/install/bats.bash"
        pdm install
    fi
    export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
    if [ -n "${1:-}" ]; then
        bats "$1"
        return
    fi
    pdm run pytest -qq tests/docs/
    bats tests/bats/docs/
}

run_cached /tmp/plcc-test-docs.log _run "$@"
