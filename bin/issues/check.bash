#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/../.." &> /dev/null && pwd )"
cd "${PROJECT_ROOT}"

ISSUES_DIR="dev-docs/issues"
DONE_DIR="${ISSUES_DIR}/done"
ROADMAP="dev-docs/roadmap.md"
NEXT_ID_FILE="${ISSUES_DIR}/.next-id.txt"

failures=0
fail() {
    echo "FAIL: $*" >&2
    failures=$(( failures + 1 ))
}

open_count=0
max_id=0

# Every open issue file has an Open Issues entry in the roadmap.
for f in "${ISSUES_DIR}"/[0-9]*.md; do
    [[ -e "${f}" ]] || break
    open_count=$(( open_count + 1 ))
    basename="${f##*/}"
    id=$(( 10#${basename%%-*} ))
    (( id > max_id )) && max_id=${id}
    grep -q "^- \*\*\[#${id}\](issues/${basename})" "${ROADMAP}" \
        || fail "open issue ${basename} has no Open Issues entry in ${ROADMAP}"
done

# Closed issues also count toward the highest ID ever assigned.
for f in "${DONE_DIR}"/[0-9]*.md; do
    [[ -e "${f}" ]] || break
    basename="${f##*/}"
    id=$(( 10#${basename%%-*} ))
    (( id > max_id )) && max_id=${id}
done

# Every roadmap link resolves, and open/done paths agree with the filesystem.
while IFS= read -r link; do
    path="${ISSUES_DIR}/${link#issues/}"
    [[ -e "${path}" ]] || { fail "roadmap links ${link} but ${path} does not exist"; continue; }
    if [[ "${link}" != issues/done/* && -e "${DONE_DIR}/${link#issues/}" ]]; then
        fail "roadmap links ${link} as open but the issue is closed"
    fi
done < <(grep -o '(issues/[^)]*\.md)' "${ROADMAP}" | tr -d '()' | sort -u)

# Milestone task lists: unchecked items link open issues, checked items done/.
while IFS= read -r line; do
    fail "unchecked milestone item links a closed issue: ${line}"
done < <(grep -n '^[0-9]*\. \[ \] .*(issues/done/' "${ROADMAP}" || true)
while IFS= read -r line; do
    fail "checked milestone item links an open issue: ${line}"
done < <(grep -n '^[0-9]*\. \[x\] .*(issues/[0-9]' "${ROADMAP}" || true)

# The ID counter is ahead of every issue ever filed.
next_id=$(( 10#$(cat "${NEXT_ID_FILE}") ))
(( next_id > max_id )) \
    || fail "${NEXT_ID_FILE} is ${next_id} but issue ${max_id} already exists"

if (( failures > 0 )); then
    echo "${failures} check(s) failed" >&2
    exit 1
fi
echo "OK: ${open_count} open issues, roadmap consistent, next id ${next_id}"
