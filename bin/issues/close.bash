#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

ISSUES_DIR="dev-docs/issues"
DONE_DIR="${ISSUES_DIR}/done"
ROADMAP="dev-docs/roadmap.md"

usage() {
    echo "Usage: $(basename "$0") <id>"
    echo "  id  issue number, e.g. 135"
    echo
    echo "Moves the issue file to ${DONE_DIR}/, removes its entry from the"
    echo "Open Issues section of ${ROADMAP}, and checks its box in any"
    echo "milestone task list. Stages the changes; you review and commit."
    exit 1
}

[[ $# -ne 1 ]] && usage

padded=$(printf '%03d' "$(( 10#$1 ))")

matches=( "${ISSUES_DIR}/${padded}"-*.md )
if [[ ! -e "${matches[0]}" ]]; then
    # Unpadded IDs (e.g. 112) predate zero-padding in new.bash.
    matches=( "${ISSUES_DIR}/$(( 10#$1 ))"-*.md )
fi
if [[ ! -e "${matches[0]}" ]]; then
    done_matches=( "${DONE_DIR}/${padded}"-*.md "${DONE_DIR}/$(( 10#$1 ))"-*.md )
    for m in "${done_matches[@]}"; do
        [[ -e "${m}" ]] && { echo "error: issue $1 is already closed: ${m}" >&2; exit 1; }
    done
    echo "error: no open issue matching '${ISSUES_DIR}/${padded}-*.md'" >&2
    exit 1
fi
if [[ ${#matches[@]} -gt 1 ]]; then
    echo "error: multiple files match issue $1: ${matches[*]}" >&2
    exit 1
fi

issue_file="${matches[0]}"
basename="${issue_file##*/}"

git mv "${issue_file}" "${DONE_DIR}/${basename}"

# Roadmap, pass 1: in milestone task lists, check the box and repoint the
# link at done/. Runs before pass 2 so the entry-removal match below only
# sees the Open Issues bullet.
sed -i \
    -e "s|\[ \] \(\[#[0-9]*\](issues/\)${basename})|[x] \1done/${basename})|" \
    "${ROADMAP}"

# Roadmap, pass 2: drop the issue's Open Issues entry — the bullet line plus
# its indented continuation lines, so back-to-back neighbors are untouched —
# then drop any "###" heading whose section is now empty.
awk -v link="(issues/${basename})" '
    skip { if ($0 ~ /^[ \t]/) next; skip = 0 }
    /^- / && index($0, link) { skip = 1; next }
    { lines[n++] = $0 }
    END {
        for (i = 0; i < n; i++) {
            if (lines[i] ~ /^### /) {
                j = i + 1
                while (j < n && lines[j] == "") j++
                if (j >= n || lines[j] ~ /^##/) { i = j - 1; continue }
            }
            keep[m++] = lines[i]
        }
        for (k = 0; k < m; k++) {
            if (keep[k] == "") { blank = 1; continue }
            if (printed && blank) print ""
            print keep[k]
            blank = 0; printed = 1
        }
    }
' "${ROADMAP}" > "${ROADMAP}.tmp"
mv "${ROADMAP}.tmp" "${ROADMAP}"
git add "${ROADMAP}"

bin/issues/check.bash

echo "closed: ${DONE_DIR}/${basename}"
echo "Review ${ROADMAP} (milestone rationale text is not auto-edited), then commit:"
echo "  docs(issues): close issue $(( 10#$1 )) (<short title>), update roadmap"
