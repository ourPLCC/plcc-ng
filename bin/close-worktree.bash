#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

usage() {
    echo "Usage: $(basename "$0") <worktree-name>"
    echo "  worktree-name  name of the worktree under .worktrees/, e.g. 084-no-banner-default"
    exit 1
}

[[ $# -lt 1 ]] && usage

WORKTREE_NAME="$1"
WORKTREE_PATH="${PROJECT_ROOT}/.worktrees/${WORKTREE_NAME}"

BRANCH="$(git -C "${WORKTREE_PATH}" branch --show-current)"

git pull --prune
git worktree remove "${WORKTREE_PATH}"
git branch -d "${BRANCH}"
pdm install
