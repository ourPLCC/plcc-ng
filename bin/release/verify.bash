#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"

# Verify a published release: PyPI serves the version, the GitHub
# Release exists, the versioned docs are deployed, and (unless
# --no-install) the package installs from real PyPI and passes
# bin/test/smoke.bash. Deliberately not cached via bin/test/_cache.bash:
# the result depends on PyPI, GitHub, and the docs site, not git state.

RETRY_DELAY="${PLCC_VERIFY_RETRY_DELAY:-15}"
RETRY_ATTEMPTS=5

usage() {
    echo "Usage: $(basename "$0") [--no-install] <tag>"
    echo "  tag           release tag with the leading 'v', e.g. v0.65.0"
    echo "  --no-install  skip the real-PyPI install + smoke test"
    echo
    echo "Verifies a published release. Checks, in order: PyPI has the"
    echo "version, the GitHub Release exists, the docs site lists the"
    echo "version as 'latest', and (unless --no-install) 'pip install' from"
    echo "PyPI into a throwaway venv passes bin/test/smoke.bash."
    echo "PLCC_VERIFY_RETRY_DELAY overrides the retry delay (default 15s)."
    exit 1
}

NO_INSTALL=""
TAG=""
for arg in "$@"; do
    case "${arg}" in
        --no-install) NO_INSTALL=1 ;;
        -*) usage ;;
        *) [[ -n "${TAG}" ]] && usage
           TAG="${arg}" ;;
    esac
done
[[ -z "${TAG}" ]] && usage
[[ "${TAG}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || usage

VERSION="${TAG#v}"
MAJOR_MINOR="$(echo "${VERSION}" | cut -d. -f1,2)"

echo "bin/release/verify.bash ${TAG}"
echo "------------------------------"

# 1. PyPI has the version (retry: the index can lag the upload).
pypi_ok=""
for attempt in $(seq 1 "${RETRY_ATTEMPTS}"); do
    if curl -fsS -o /dev/null "https://pypi.org/pypi/plcc-ng/${VERSION}/json"; then
        pypi_ok=1
        break
    fi
    if [[ "${attempt}" -lt "${RETRY_ATTEMPTS}" ]]; then
        echo "PyPI does not serve ${VERSION} yet (attempt ${attempt}/${RETRY_ATTEMPTS}); retrying in ${RETRY_DELAY}s"
        sleep "${RETRY_DELAY}"
    fi
done
[[ -n "${pypi_ok}" ]] || { echo "FAIL: plcc-ng ${VERSION} not on PyPI"; exit 1; }
echo "OK: PyPI has plcc-ng ${VERSION}"

# 2. The GitHub Release exists (curl, not gh: anonymous read of a public
# repo needs no auth or tooling).
curl -fsS -o /dev/null "https://api.github.com/repos/ourPLCC/plcc-ng/releases/tags/${TAG}" \
    || { echo "FAIL: GitHub Release ${TAG} missing"; exit 1; }
echo "OK: GitHub Release ${TAG} exists"

# 3. Versioned docs deployed: mike's versions.json lists MAJOR.MINOR and
# points the 'latest' alias at it.
VERSIONS_JSON="$(curl -fsS "https://ourplcc.github.io/plcc-ng/versions.json")" \
    || { echo "FAIL: could not fetch docs versions.json"; exit 1; }
echo "${VERSIONS_JSON}" | python3 -c "
import json, sys
want = '${MAJOR_MINOR}'
entries = json.load(sys.stdin)
entry = next((e for e in entries if e['version'] == want), None)
if entry is None:
    sys.exit('FAIL: docs version ' + want + ' not deployed')
if 'latest' not in entry.get('aliases', []):
    sys.exit('FAIL: docs latest alias is not on ' + want)
" || exit 1
echo "OK: docs ${MAJOR_MINOR} deployed with latest alias"

if [[ -n "${NO_INSTALL}" ]]; then
    echo "verify: all checks passed for ${TAG} (install skipped)"
    exit 0
fi

# 4. Install from real PyPI into a throwaway venv and smoke test. This
# is the only place the artifact served by real PyPI (rather than
# TestPyPI, which CI smoke-tests) is ever exercised.
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT
python3 -m venv "${WORK_DIR}/venv"
installed=""
for attempt in $(seq 1 "${RETRY_ATTEMPTS}"); do
    if "${WORK_DIR}/venv/bin/pip" install --quiet --no-cache-dir "plcc-ng==${VERSION}"; then
        installed=1
        break
    fi
    if [[ "${attempt}" -lt "${RETRY_ATTEMPTS}" ]]; then
        echo "PyPI install not ready (attempt ${attempt}/${RETRY_ATTEMPTS}); retrying in ${RETRY_DELAY}s"
        sleep "${RETRY_DELAY}"
    fi
done
[[ -n "${installed}" ]] || { echo "FAIL: pip install plcc-ng==${VERSION} from PyPI failed"; exit 1; }
echo "OK: installed plcc-ng==${VERSION} from PyPI"

export PATH="${WORK_DIR}/venv/bin:${PATH}"
"${PROJECT_ROOT}/bin/test/smoke.bash"

echo "verify: all checks passed for ${TAG}"
