#!/usr/bin/env bats

@test "plcc-scan is on PATH" { command -v plcc-scan; }
@test "plcc-parse is on PATH" { command -v plcc-parse; }
@test "plcc-rep is on PATH" { command -v plcc-rep; }

@test "plcc-scan exits nonzero with not-implemented message" {
    run plcc-scan
    [ "$status" -ne 0 ]
    [[ "${output}${stderr}" =~ [Nn]ot.*[Ii]mplemented ]]
}

@test "plcc-parse exits nonzero" {
    run plcc-parse
    [ "$status" -ne 0 ]
}

@test "plcc-rep exits nonzero" {
    run plcc-rep
    [ "$status" -ne 0 ]
}
