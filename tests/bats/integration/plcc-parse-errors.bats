#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-parse: lex error reports plcc-tokens, not plcc-tree cascade" {
    tmp=$(mktemp -d)
    cat > "$tmp/trivial.plcc" <<'EOF'
token NUM '\d+'
%
<program> ::= NUM
%
% diagram PlantUML
EOF
    run --separate-stderr bash -c "echo 'abc' | plcc-parse '$tmp/trivial.plcc'"
    [ "$status" -ne 0 ]
    # User-facing error: plcc-tokens is responsible, rendered via reformat_child_events
    [[ "$stderr" == *"plcc-tokens"* ]]
    [[ "$stderr" == *"error"* ]]
    # plcc-tree's cascading error must NOT appear
    ! [[ "$stderr" == *"plcc-tree:"*"error"* ]]
    rm -rf "$tmp"
}
