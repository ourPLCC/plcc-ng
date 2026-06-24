#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

usage() {
    echo "Usage: $(basename "$0") <worktree-name>"
    echo "  worktree-name  name of the worktree under .worktrees/ or .claude/worktrees/, e.g. 084-no-banner-default"
    exit 1
}

[[ $# -lt 1 ]] && usage

WORKTREE_NAME="$1"

if [[ -d "${PROJECT_ROOT}/.worktrees/${WORKTREE_NAME}" ]]; then
    WORKTREE_PATH="${PROJECT_ROOT}/.worktrees/${WORKTREE_NAME}"
elif [[ -d "${PROJECT_ROOT}/.claude/worktrees/${WORKTREE_NAME}" ]]; then
    WORKTREE_PATH="${PROJECT_ROOT}/.claude/worktrees/${WORKTREE_NAME}"
else
    echo "Error: worktree '${WORKTREE_NAME}' not found under .worktrees/ or .claude/worktrees/" >&2
    exit 1
fi

BRANCH="$(git -C "${WORKTREE_PATH}" branch --show-current)"

git pull --prune
git worktree remove "${WORKTREE_PATH}"
git branch -d "${BRANCH}"
pdm install
