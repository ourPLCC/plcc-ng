#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

@test "plcc-version is on PATH" {
    command -v plcc-version
}

@test "plcc-version exits 0" {
    run plcc-version
    [ "$status" -eq 0 ]
}

@test "plcc-version prints plcc-ng followed by a version string" {
    run plcc-version
    [[ "$output" =~ ^plcc-ng\ .+ ]]
}
