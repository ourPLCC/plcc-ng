#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
MAIN_ROOT="$( cd "$( git -C "${PROJECT_ROOT}" rev-parse --git-common-dir )/.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

export PATH="${MAIN_ROOT}/.venv/bin:${PATH}"
mkdocs serve
