#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    PROJECT_ROOT="$(git rev-parse --show-toplevel)"
    SCRIPT="${PROJECT_ROOT}/bin/install/claude-imports.bash"
    export HOME="${BATS_TEST_TMPDIR}/home"
    mkdir -p "${HOME}"
    CONFIG="${HOME}/.claude.json"
}

flag() {
    jq -r --arg p "${PROJECT_ROOT}" ".projects[\$p].$1" "${CONFIG}"
}

@test "approves external imports when no config exists" {
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(flag hasClaudeMdExternalIncludesApproved)" = "true" ]
    [ "$(flag hasClaudeMdExternalIncludesWarningShown)" = "true" ]
}

@test "approves external imports and keeps existing settings" {
    jq -n --arg p "${PROJECT_ROOT}" '{
        userID: "u1",
        projects: {
            ($p): {allowedTools: ["x"], hasClaudeMdExternalIncludesApproved: false},
            "/elsewhere": {hasClaudeMdExternalIncludesApproved: false}
        }
    }' > "${CONFIG}"

    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(flag hasClaudeMdExternalIncludesApproved)" = "true" ]
    [ "$(flag hasClaudeMdExternalIncludesWarningShown)" = "true" ]
    [ "$(flag 'allowedTools[0]')" = "x" ]
    [ "$(jq -r .userID "${CONFIG}")" = "u1" ]
    [ "$(jq -r '.projects["/elsewhere"].hasClaudeMdExternalIncludesApproved' "${CONFIG}")" = "false" ]
}

@test "leaves the config readable only by its owner" {
    run "${SCRIPT}"
    [ "$status" -eq 0 ]
    [ "$(stat -c %a "${CONFIG}")" = "600" ]
}
