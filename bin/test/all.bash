#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/all.bash"
echo "-----------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    "${SCRIPT_DIR}/functional.bash"
    "${SCRIPT_DIR}/e2e_haskell_roundtrip.bash"
    "${SCRIPT_DIR}/packaging.bash"
}

run_cached /tmp/plcc-test-all.log _run
