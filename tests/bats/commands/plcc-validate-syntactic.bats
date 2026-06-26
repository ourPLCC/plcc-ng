#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-validate-syntactic is on PATH" {
    command -v plcc-validate-syntactic
}

@test "plcc-validate-syntactic --help exits 0 and prints Usage" {
    run plcc-validate-syntactic --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
}

@test "plcc-validate-syntactic exits 0 for valid spec" {
    run bash -c "plcc-spec '${FIXTURES}/trivial.plcc' | plcc-validate-syntactic"
    [ "$status" -eq 0 ]
}

@test "plcc-validate-syntactic exits 0 for valid arith spec" {
    run bash -c "plcc-spec '${FIXTURES}/arith.plcc' | plcc-validate-syntactic"
    [ "$status" -eq 0 ]
}

@test "plcc-validate-syntactic exits 1 for spec with undefined terminal" {
    SPEC_JSON=$(mktemp)
    trap "rm -f '${SPEC_JSON}'" EXIT
    cat > "${SPEC_JSON}" <<'EOF'
{
  "lexical": {"ruleList": []},
  "syntax": {"rules": [{
    "line": {"string": "<Program> ::= UNDEFINED\n", "number": 3, "file": "bad.plcc"},
    "lhs": {"name": "Program", "altName": null, "isTerminal": false, "isCapturing": false},
    "rhsSymbolList": [{"name": "UNDEFINED", "isTerminal": true, "isCapturing": false}]
  }]}
}
EOF
    run --separate-stderr bash -c "plcc-validate-syntactic < '${SPEC_JSON}'"
    [ "$status" -eq 1 ]
    [ -n "$stderr" ]
}

@test "plcc-validate-syntactic error references offending line" {
    SPEC_JSON=$(mktemp)
    trap "rm -f '${SPEC_JSON}'" EXIT
    cat > "${SPEC_JSON}" <<'EOF'
{
  "lexical": {"ruleList": []},
  "syntax": {"rules": [{
    "line": {"string": "<Program> ::= UNDEFINED\n", "number": 3, "file": "bad.plcc"},
    "lhs": {"name": "Program", "altName": null, "isTerminal": false, "isCapturing": false},
    "rhsSymbolList": [{"name": "UNDEFINED", "isTerminal": true, "isCapturing": false}]
  }]}
}
EOF
    run --separate-stderr bash -c "plcc-validate-syntactic < '${SPEC_JSON}'"
    [[ "$stderr" == *"bad.plcc"* ]]
    [[ "$stderr" == *":3:"* ]]
}
