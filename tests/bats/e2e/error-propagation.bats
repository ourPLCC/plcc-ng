#!/usr/bin/env bats

# Tests that in-band errors pass through the pipeline without breaking it.

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    SPEC_JSON="$(mktemp)"
    LL1_JSON="$(mktemp)"
    plcc-spec "${FIXTURES}/trivial.plcc" > "${SPEC_JSON}"
    plcc-ll1 "${SPEC_JSON}" > "${LL1_JSON}"
}

teardown() { rm -f "${SPEC_JSON}" "${LL1_JSON}"; }

@test "lex error flows in-band through tokens->tree without crashing" {
    # 'abc' is not a valid NUM token — should produce an in-band error
    result=$(echo 'abc' | plcc-tokens "${SPEC_JSON}" | plcc-tree --ll1="${LL1_JSON}" 2>/dev/null)
    # Pipeline exit status should be 0 (error is in-band, not a tool failure)
    echo "${result}" | head -1 | python3 -c "
import json, sys
line = sys.stdin.readline().strip()
r = json.loads(line)
assert 'error' in json.dumps(r), f'Expected error in output, got: {r}'
print('OK: error present in-band')
"
}

@test "lex error does not produce stderr output from pipeline" {
    stderr_out=$(echo 'abc' | plcc-tokens "${SPEC_JSON}" 2>&1 1>/dev/null)
    [ -z "${stderr_out}" ]
}
