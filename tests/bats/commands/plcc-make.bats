#!/usr/bin/env bats

bats_require_minimum_version 1.5.0

setup() {
    FIXTURES="$(git rev-parse --show-toplevel)/tests/fixtures"
    WORK_DIR="$(mktemp -d)"
    cd "${WORK_DIR}"
}

teardown() {
    rm -rf "${WORK_DIR}"
}

# ── Basic interface ────────────────────────────────────────────────────────────

@test "plcc-make is on PATH" { command -v plcc-make; }

@test "plcc-make --help exits 0" {
    run plcc-make --help
    [ "$status" -eq 0 ]
}

@test "plcc-make with no spec.plcc exits nonzero" {
    run --separate-stderr plcc-make
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"spec file not found"* ]]
}

@test "plcc-make --spec with missing file exits nonzero" {
    run --separate-stderr plcc-make --spec=no-such-file.plcc
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"spec file not found"* ]]
}

@test "plcc-make defaults to spec.plcc in CWD" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

@test "plcc-make --spec uses specified path" {
    run plcc-make --through=scan "--spec=${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

@test "plcc-make accepts -v" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    run plcc-make -v --through=scan
    [ "$status" -eq 0 ]
}

# ── Build artifacts ────────────────────────────────────────────────────────────

@test "plcc-make full build produces spec.json ll1.json model.json" {
    cp "${FIXTURES}/trivial-python.plcc" spec.plcc
    run plcc-make
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
    [ -f build/ll1.json ]
    [ -f build/model.json ]
}

@test "plcc-make full build writes .spec-hash sentinel" {
    cp "${FIXTURES}/trivial-python.plcc" spec.plcc
    run plcc-make
    [ "$status" -eq 0 ]
    [ -f "build/.spec-hash" ]
}

@test "plcc-make --through=scan creates spec.json but not ll1.json" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
    [ ! -f build/ll1.json ]
}

@test "plcc-make --through=parse creates spec.json and ll1.json but not model.json" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    run plcc-make --through=parse
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
    [ -f build/ll1.json ]
    [ ! -f build/model.json ]
}

# ── Staleness: fast path ───────────────────────────────────────────────────────

@test "plcc-make does not rebuild when spec is unchanged" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    plcc-make --through=parse
    rm build/ll1.json          # manually remove artifact
    plcc-make --through=parse  # spec unchanged → fast path
    [ ! -f build/ll1.json ]    # not rebuilt confirms fast path taken
}

@test "plcc-make --through=all fast-paths when all-level sentinel present" {
    cp "${FIXTURES}/trivial-python.plcc" spec.plcc
    plcc-make
    rm build/ll1.json          # manually corrupt build/
    plcc-make                  # spec unchanged, sentinel at 'all' level → fast path
    [ ! -f build/ll1.json ]    # not rebuilt confirms fast path taken
}

# ── Staleness: slow path ───────────────────────────────────────────────────────

@test "plcc-make rebuilds when spec changes" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    plcc-make --through=scan
    first_spec=$(cat build/spec.json)

    cp "${FIXTURES}/trivial-python.plcc" spec.plcc  # different spec
    plcc-make --through=scan
    second_spec=$(cat build/spec.json)

    [ "$first_spec" != "$second_spec" ]
}

@test "plcc-make --through=scan then --through=all completes full build" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    plcc-make --through=scan
    [ ! -f build/ll1.json ]

    plcc-make  # spec unchanged but level insufficient (scan < all)
    [ -f build/ll1.json ]
}

@test "plcc-make --through=all then --through=scan fast-paths" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    plcc-make
    rm build/ll1.json
    plcc-make --through=scan  # all >= scan → fast path
    [ ! -f build/ll1.json ]   # not rebuilt confirms fast path
}

# ── Staleness: failure handling ────────────────────────────────────────────────

@test "plcc-make deletes sentinel when plcc-spec fails" {
    cp "${FIXTURES}/trivial-python.plcc" spec.plcc
    plcc-make
    [ -f "build/.spec-hash" ]

    printf 'token BAD @@@\n' > spec.plcc  # syntax error
    run plcc-make
    [ "$status" -ne 0 ]
    [ ! -f "build/.spec-hash" ]
}

@test "plcc-make re-fails on repeated call with broken spec" {
    printf 'token BAD @@@\n' > spec.plcc
    run plcc-make
    [ "$status" -ne 0 ]
    run plcc-make
    [ "$status" -ne 0 ]
}

@test "plcc-make rebuilds after broken spec is fixed" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    plcc-make --through=scan

    printf 'token BAD @@@\n' > spec.plcc
    run plcc-make --through=scan
    [ "$status" -ne 0 ]

    cp "${FIXTURES}/trivial-python.plcc" spec.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

# ── Partial specs ──────────────────────────────────────────────────────────────

@test "plcc-make --through=scan succeeds with lexical-only spec" {
    cp "${FIXTURES}/lexical-only.plcc" spec.plcc
    run plcc-make --through=scan
    [ "$status" -eq 0 ]
    [ -f build/spec.json ]
}

@test "plcc-make --through=parse succeeds with lexical-only spec" {
    cp "${FIXTURES}/lexical-only.plcc" spec.plcc
    run plcc-make --through=parse
    [ "$status" -eq 0 ]
    [ -f build/ll1.json ]
}

@test "plcc-make full build succeeds with lexical+syntactic spec and no semantics" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    run plcc-make
    [ "$status" -eq 0 ]
    [ -f build/ll1.json ]
    [ -f build/model.json ]
}

# ── Sticky spec ────────────────────────────────────────────────────────────────

@test "plcc-make writes build/.spec after successful build" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    plcc-make --through=scan
    [ -f "build/.spec" ]
    [[ "$(cat build/.spec)" == "spec.plcc" ]]
}

@test "plcc-make with --spec writes that path to build/.spec" {
    run plcc-make --through=scan "--spec=${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    [[ "$(cat build/.spec)" == "${FIXTURES}/trivial.plcc" ]]
}

@test "plcc-make without --spec uses stored spec" {
    # Build from an absolute path spec, then invoke plcc-make with no args
    # → should use stored path, not look for spec.plcc in CWD
    run plcc-make --through=scan "--spec=${FIXTURES}/trivial.plcc"
    [ "$status" -eq 0 ]
    [[ "$(cat build/.spec)" == "${FIXTURES}/trivial.plcc" ]]
    # Now run with no --spec from a dir with no spec.plcc
    run --separate-stderr plcc-make --through=scan
    [ "$status" -eq 0 ]
    [[ "$(cat build/.spec)" == "${FIXTURES}/trivial.plcc" ]]
}

@test "plcc-make with --spec differing from stored wipes build" {
    cp "${FIXTURES}/trivial.plcc" spec.plcc
    plcc-make --through=scan
    cp "${FIXTURES}/trivial-python.plcc" other.plcc
    plcc-make --through=scan --spec=other.plcc
    # build/ was wiped and rebuilt from other.plcc
    [[ "$(cat build/.spec)" == "other.plcc" ]]
}

@test "plcc-make stored spec missing gives error to stderr with hint" {
    mkdir -p build
    echo "ghost.plcc" > build/.spec
    run --separate-stderr plcc-make
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"spec file not found"* ]]
    [[ "$stderr" == *"ghost.plcc"* ]]
    [[ "$stderr" == *"--spec"* ]]
}

@test "plcc-make no build/.spec no --spec falls back to spec.plcc" {
    run --separate-stderr plcc-make
    [ "$status" -ne 0 ]
    [[ "$stderr" == *"spec.plcc"* ]]
}

@test "plcc-make writes build/.spec even when plcc-spec fails" {
    printf 'token BAD @@@\n' > bad.plcc
    run plcc-make --spec=bad.plcc
    [ "$status" -ne 0 ]
    [ -f "build/.spec" ]
    [[ "$(cat build/.spec)" == "bad.plcc" ]]
}
