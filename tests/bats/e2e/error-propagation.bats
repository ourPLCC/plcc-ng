#!/usr/bin/env bats

# Tests that in-band errors pass through the pipeline without breaking it.

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
}

teardown() { rm -f "${SPEC_JSON}"; }

@test "lex error flows in-band through tokens->tree without crashing" {
    # 'abc' is not a valid NUM token — should produce an in-band error
    result=$(echo 'abc' | plcc-tokens "${SPEC_JSON}" | plcc-tree --spec="${SPEC_JSON}" 2>/dev/null)
    # Pipeline exit status should be 0 (error is in-band, not a tool failure)
    echo "${result}" | head -1 | python3 -c "
import json, sys
line = sys.stdin.readline().strip()
r = json.loads(line)
assert r['kind'] == 'error', f'Expected error record, got: {r}'
print('OK: error record present in-band')
"
}

@test "lex error does not produce stderr output from pipeline" {
    stderr_out=$(echo 'abc' | plcc-tokens "${SPEC_JSON}" 2>&1 1>/dev/null)
    [ -z "${stderr_out}" ]
}
