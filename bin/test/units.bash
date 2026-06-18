#!/usr/bin/env bash

set -euo pipefail

echo "bin/test/units.bash"
echo "-------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# shellcheck source=bin/test/_cache.bash
source "${SCRIPT_DIR}/_cache.bash"

_run() {
    "${SCRIPT_DIR}/../install/pdm.bash"
    pdm install
    pdm test -v "$@"
}

run_cached /tmp/plcc-test-units.log _run "$@"
