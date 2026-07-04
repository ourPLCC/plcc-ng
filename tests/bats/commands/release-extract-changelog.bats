#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
EXTRACT="${PROJECT_ROOT}/bin/release/extract-changelog.bash"

setup() {
    WORK_DIR="$(mktemp -d)"
    export CHANGELOG_FILE="${WORK_DIR}/CHANGELOG.md"
    cat > "${CHANGELOG_FILE}" <<'EOF'
# CHANGELOG


## v0.1.10 (2026-07-04)

### Bug Fixes

- newest fix entry


## v0.1.1 (2026-07-03)

### Features

- middle feature entry


## v0.1.0 (2026-07-01)

### Features

- oldest feature entry
EOF
}

teardown() {
    rm -rf "${WORK_DIR}"
}

@test "extract-changelog: extracts the newest section" {
    run bash "${EXTRACT}" 0.1.10
    [ "$status" -eq 0 ]
    [[ "$output" == *"newest fix entry"* ]]
}

@test "extract-changelog: extracts a middle section" {
    run bash "${EXTRACT}" 0.1.1
    [ "$status" -eq 0 ]
    [[ "$output" == *"middle feature entry"* ]]
}

@test "extract-changelog: extracts the oldest section (ends at EOF)" {
    run bash "${EXTRACT}" 0.1.0
    [ "$status" -eq 0 ]
    [[ "$output" == *"oldest feature entry"* ]]
}

@test "extract-changelog: output excludes neighboring sections" {
    run bash "${EXTRACT}" 0.1.1
    [ "$status" -eq 0 ]
    [[ "$output" != *"newest fix entry"* ]]
    [[ "$output" != *"oldest feature entry"* ]]
}

@test "extract-changelog: output excludes the version heading line" {
    run bash "${EXTRACT}" 0.1.1
    [ "$status" -eq 0 ]
    [[ "$output" != *"## v0.1.1"* ]]
}

@test "extract-changelog: does not trim or pad output content" {
    run bash "${EXTRACT}" 0.1.1
    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "### Features" ]
    [ "${lines[1]}" = "- middle feature entry" ]
}

@test "extract-changelog: version is not treated as a prefix" {
    # v0.1.1 must not match the v0.1.10 heading; entry content proves which
    # section was found.
    run bash "${EXTRACT}" 0.1.1
    [[ "$output" != *"newest fix entry"* ]]
    [[ "$output" == *"middle feature entry"* ]]
}

@test "extract-changelog: fails with a diagnostic on an unknown version" {
    run bash "${EXTRACT}" 9.9.9
    [ "$status" -ne 0 ]
    [[ "$output" == *"no section for version 'v9.9.9'"* ]]
}

@test "extract-changelog: fails with usage when called without arguments" {
    run bash "${EXTRACT}"
    [ "$status" -ne 0 ]
    [[ "$output" == *"Usage:"* ]]
}
