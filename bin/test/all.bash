#!/usr/bin/env bash
set -euo pipefail

echo "bin/test/all.bash"
echo "-----------------"

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

"${SCRIPT_DIR}/functional.bash"
"${SCRIPT_DIR}/packaging.bash"
