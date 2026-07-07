#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

PROJECT_ROOT="$(git rev-parse --show-toplevel)"

# close.bash resolves its project root from its own location, so exercise it
# from a throwaway git repo holding copies of the scripts and a minimal
# dev-docs tree.
setup() {
    REPO="$(mktemp -d)"
    ROADMAP="${REPO}/dev-docs/roadmap.md"
    mkdir -p "${REPO}/bin/issues" "${REPO}/dev-docs/issues/done"
    cp "${PROJECT_ROOT}"/bin/issues/*.bash "${REPO}/bin/issues/"

    cat > "${REPO}/dev-docs/issues/001-first-bug.md" <<'EOF'
# 1 - first-bug

See also issue [005](done/005-already-done.md) and issue
[003](003-a-feature.md). Related design doc:
[v1.0 criteria](../v1.0-criteria.md).
EOF
    echo '# 2 - second-bug' > "${REPO}/dev-docs/issues/002-second-bug.md"
    echo '# 3 - a-feature' > "${REPO}/dev-docs/issues/003-a-feature.md"
    echo '006' > "${REPO}/dev-docs/issues/.next-id.txt"

    echo '# 5 - already-done' > "${REPO}/dev-docs/issues/done/005-already-done.md"
    echo '# v1.0 criteria' > "${REPO}/dev-docs/v1.0-criteria.md"

    mkdir -p "${REPO}/dev-docs/specs"
    cat > "${REPO}/dev-docs/specs/2026-01-01-example-design.md" <<'EOF'
# Example design

Fixes issue [1](../issues/001-first-bug.md) using the same approach as
issue [2](../issues/002-second-bug.md).
EOF

    cat > "${ROADMAP}" <<'EOF'
# Roadmap

## Open Issues

### Fixes

- **[#1](issues/001-first-bug.md) — First bug**
  Summary of first bug.
- **[#2](issues/002-second-bug.md) — Second bug**
  Summary of second bug.

### Features

- **[#3](issues/003-a-feature.md) — A feature**
  Summary of the feature.
EOF

    git -C "${REPO}" -c init.defaultBranch=main init -q
    git -C "${REPO}" add -A
    git -C "${REPO}" -c user.email=test@test -c user.name=test commit -qm init
}

teardown() {
    rm -rf "${REPO}"
}

@test "closing an issue keeps the adjacent entry in the same group" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    grep -q '^- \*\*\[#2\](issues/002-second-bug.md)' "${ROADMAP}"
    grep -q 'Summary of second bug.' "${ROADMAP}"
    grep -q '^### Fixes' "${ROADMAP}"
}

@test "closing an issue removes its entry and continuation line" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    ! grep -q '001-first-bug' "${ROADMAP}"
    ! grep -q 'Summary of first bug.' "${ROADMAP}"
    [ -f "${REPO}/dev-docs/issues/done/001-first-bug.md" ]
}

@test "closing the only issue in a group removes its heading" {
    run "${REPO}/bin/issues/close.bash" 3
    [ "$status" -eq 0 ]
    ! grep -q '^### Features' "${ROADMAP}"
    grep -q '^### Fixes' "${ROADMAP}"
    grep -q '^- \*\*\[#1\](issues/001-first-bug.md)' "${ROADMAP}"
    grep -q '^- \*\*\[#2\](issues/002-second-bug.md)' "${ROADMAP}"
}

@test "closing the second of two adjacent entries keeps the first" {
    run "${REPO}/bin/issues/close.bash" 2
    [ "$status" -eq 0 ]
    grep -q '^- \*\*\[#1\](issues/001-first-bug.md)' "${ROADMAP}"
    grep -q 'Summary of first bug.' "${ROADMAP}"
    grep -q '^### Fixes' "${ROADMAP}"
    ! grep -q '002-second-bug' "${ROADMAP}"
}

@test "closing an issue rewrites an external link to the issue's done/ path" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    grep -qF '(../issues/done/001-first-bug.md)' "${REPO}/dev-docs/specs/2026-01-01-example-design.md"
    ! grep -qF '(../issues/001-first-bug.md)' "${REPO}/dev-docs/specs/2026-01-01-example-design.md"
}

@test "closing an issue leaves an unrelated external link untouched" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    grep -qF '(../issues/002-second-bug.md)' "${REPO}/dev-docs/specs/2026-01-01-example-design.md"
}

@test "closing an issue strips the done/ prefix from an already-closed sibling link" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    grep -qF '(005-already-done.md)' "${REPO}/dev-docs/issues/done/001-first-bug.md"
    ! grep -qF '(done/005-already-done.md)' "${REPO}/dev-docs/issues/done/001-first-bug.md"
}

@test "closing an issue adds a leading ../ to a link that already climbs above issues/" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    grep -qF '(../../v1.0-criteria.md)' "${REPO}/dev-docs/issues/done/001-first-bug.md"
}

@test "closing an issue adds a leading ../ to a bare link to a still-open sibling" {
    run "${REPO}/bin/issues/close.bash" 1
    [ "$status" -eq 0 ]
    grep -qF '(../003-a-feature.md)' "${REPO}/dev-docs/issues/done/001-first-bug.md"
}
