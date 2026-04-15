#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

"${SCRIPT_DIR}/../install/pdm.bash"
pdm install
pdm test -v "$@"
