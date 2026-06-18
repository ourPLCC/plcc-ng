#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/integration.bash"
echo "-------------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    cd "${PROJECT_ROOT}"
    "${PROJECT_ROOT}/bin/install/bats.bash"
    pdm install
    export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
    bats tests/bats/integration/
}

run_cached /tmp/plcc-test-integration.log _run
