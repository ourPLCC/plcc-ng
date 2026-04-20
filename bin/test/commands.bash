#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/commands.bash"
echo "----------------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"

cd "${PROJECT_ROOT}"

"${PROJECT_ROOT}/bin/install/bats.bash"
pdm install
export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"

bats tests/bats/commands/
