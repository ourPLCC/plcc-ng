#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
}

@test "plcc-validate-semantic is on PATH" {
    command -v plcc-validate-semantic
}

@test "plcc-validate-semantic --help exits 0 and prints Usage" {
    run plcc-validate-semantic --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"Usage"* ]]
}

@test "plcc-validate-semantic exits 0 for valid spec with semantic section" {
    run bash -c "plcc-spec '${FIXTURES}/trivial-python.plcc' | plcc-validate-semantic"
    [ "$status" -eq 0 ]
}

@test "plcc-validate-semantic exits 0 for valid spec without semantic section" {
    run bash -c "plcc-spec '${FIXTURES}/trivial.plcc' | plcc-validate-semantic"
    [ "$status" -eq 0 ]
}

@test "plcc-validate-semantic exits 1 for spec with invalid class name" {
    SPEC_JSON=$(mktemp)
    trap "rm -f '${SPEC_JSON}'" EXIT
    cat > "${SPEC_JSON}" <<'EOF'
{
  "semantics": {
    "language": "Java",
    "codeFragmentList": [{
      "targetLocator": {
        "line": {"string": "%%{\n", "number": 5, "file": "bad.plcc"},
        "className": "%%{",
        "modifier": null
      },
      "block": null
    }]
  }
}
EOF
    run --separate-stderr bash -c "plcc-validate-semantic < '${SPEC_JSON}'"
    [ "$status" -eq 1 ]
    [ -n "$stderr" ]
}

@test "plcc-validate-semantic error references offending line" {
    SPEC_JSON=$(mktemp)
    trap "rm -f '${SPEC_JSON}'" EXIT
    cat > "${SPEC_JSON}" <<'EOF'
{
  "semantics": {
    "language": "Java",
    "codeFragmentList": [{
      "targetLocator": {
        "line": {"string": "%%{\n", "number": 5, "file": "bad.plcc"},
        "className": "%%{",
        "modifier": null
      },
      "block": null
    }]
  }
}
EOF
    run --separate-stderr bash -c "plcc-validate-semantic < '${SPEC_JSON}'"
    [[ "$stderr" == *"bad.plcc"* ]]
    [[ "$stderr" == *":5:"* ]]
}

@test "plcc-validate-semantic hint mentions %%% for %% prefix" {
    SPEC_JSON=$(mktemp)
    trap "rm -f '${SPEC_JSON}'" EXIT
    cat > "${SPEC_JSON}" <<'EOF'
{
  "semantics": {
    "language": "Java",
    "codeFragmentList": [{
      "targetLocator": {
        "line": {"string": "%%{\n", "number": 3, "file": "bad.plcc"},
        "className": "%%{",
        "modifier": null
      },
      "block": null
    }]
  }
}
EOF
    run --separate-stderr bash -c "plcc-validate-semantic < '${SPEC_JSON}'"
    [[ "$stderr" == *"%%%"* ]]
}
