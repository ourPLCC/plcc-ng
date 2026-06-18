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
    SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash"
}

run_cached /tmp/plcc-test-functional.log _run
