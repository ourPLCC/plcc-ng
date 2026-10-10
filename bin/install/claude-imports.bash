#!/usr/bin/env bash
set -euo pipefail

# Approve AGENTS.md's imports from ../dev for this repo, so Claude Code loads
# the org guide. Claude Code skips unapproved outside imports silently and
# does not reliably ask, and ~/.claude.json does not survive a container
# rebuild. Run before any Claude Code session starts: a running session can
# overwrite ~/.claude.json. Idempotent.

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
CONFIG="${HOME}/.claude.json"

current='{}'
if [[ -s "${CONFIG}" ]]; then
    current="$(cat "${CONFIG}")"
fi

tmp="$(mktemp "${CONFIG}.XXXXXX")"
jq --arg p "${PROJECT_ROOT}" '.projects[$p] += {
    hasClaudeMdExternalIncludesApproved: true,
    hasClaudeMdExternalIncludesWarningShown: true
}' <<< "${current}" > "${tmp}"
chmod 600 "${tmp}"
mv "${tmp}" "${CONFIG}"
