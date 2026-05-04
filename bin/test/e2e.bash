#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/e2e.bash"
echo "-----------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

"${PROJECT_ROOT}/bin/install/bats.bash"
pdm install
export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"

bats $(find tests/bats/e2e/ -name "*.bats" ! -name "languages-java.bats" | sort)

if [ -n "${LANGUAGES_REPO_PATH:-}" ]; then
    "${PROJECT_ROOT}/bin/install/java.bash"
    echo ""
    echo "Running Java corpus tests (LANGUAGES_REPO_PATH=${LANGUAGES_REPO_PATH})"
    bats tests/bats/e2e/languages-java.bats
fi
