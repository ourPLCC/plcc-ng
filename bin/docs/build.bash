#!/usr/bin/env bash
set -euo pipefail

# Build the documentation site with --strict, so a broken link or a nav entry
# pointing at a file that does not exist fails instead of warning. Uses
# mkdocs-strict.yml, which drops the kroki plugin: rendering diagrams needs the
# network, nav and link integrity does not, and this gate must not depend on a
# third-party service being up. See mkdocs-strict.yml for the details.
#
# Set SKIP_SETUP=1 to skip `pdm install` when the venv is already current.

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

if [[ -z "${SKIP_SETUP:-}" ]]; then
    "${PROJECT_ROOT}/bin/install/pdm.bash"
    pdm install
fi

export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
mkdocs build --strict --config-file mkdocs-strict.yml "$@"
