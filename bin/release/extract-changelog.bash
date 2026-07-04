#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"

usage() {
    echo "Usage: $(basename "$0") <version>"
    echo "  version  release version without the leading 'v', e.g. 0.65.0"
    echo
    echo "Prints the CHANGELOG.md section for the given version to stdout,"
    echo "excluding the version heading line. Exits non-zero if the version"
    echo "has no section. Reads \$CHANGELOG_FILE if set (for tests)."
    exit 1
}

[[ $# -ne 1 ]] && usage

VERSION="$1"
CHANGELOG="${CHANGELOG_FILE:-${PROJECT_ROOT}/CHANGELOG.md}"

if ! awk -v ver="${VERSION}" '
    BEGIN { header = "## v" ver " ("; found = 0; printing = 0; n = 0 }
    printing && /^## / { printing = 0 }
    printing { lines[n++] = $0 }
    !printing && index($0, header) == 1 { found = 1; printing = 1 }
    END {
        if (!found) exit 1
        while (n > 0 && lines[n - 1] == "") n--
        i = 0
        while (i < n && lines[i] == "") i++
        for (; i < n; i++) print lines[i]
    }
' "${CHANGELOG}"; then
    echo "error: no section for version 'v${VERSION}' in ${CHANGELOG}" >&2
    exit 1
fi
