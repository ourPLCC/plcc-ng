# 178 - nothing enforces bats_require_minimum_version in bats files

**Type:** test
**Date:** 2026-07-29

## Description

Bats tests name temporary paths under `BATS_TEST_TMPDIR`, a variable the
bats runner provides and cleans up itself (see
[CONTRIBUTING.md](../../CONTRIBUTING.md) and issue
[177](done/177-bats-helpers-leak-temp-dirs.md)). That variable only exists
on bats 1.4.0 and later. Each file guards against an older runner by
declaring `bats_require_minimum_version 1.5.0`, which turns a too-old bats
into a clear startup failure.

Nothing enforces the declaration. `tests/bats/commands/bats-temp-dirs.bats`
lints that no bats file calls `mktemp`, but a new file can use
`BATS_TEST_TMPDIR` without declaring the version floor and the lint stays
green. On an older bats the variable is unset, so a path like
`"${BATS_TEST_TMPDIR}/work"` silently becomes `/work` — the test writes
outside the sandbox, or fails in a way that points nowhere near the cause.
That silent degradation is exactly what the declaration exists to prevent.

`tests/bats/integration/spec-model.bats` is currently the only bats file
without the declaration. It allocates no temporaries and does not reference
`BATS_TEST_TMPDIR`, so it is harmless today — but it shows the gap is real
rather than hypothetical.

## Steps to Reproduce

1. Add a new file under `tests/bats/` that uses `${BATS_TEST_TMPDIR}` but
   omits `bats_require_minimum_version 1.5.0`.
2. Run `bats tests/bats/commands/bats-temp-dirs.bats`.
3. The lint passes: it only looks for `mktemp`.

## Notes

The natural home is a second test in
`tests/bats/commands/bats-temp-dirs.bats`, next to the existing `mktemp`
lint — same scan, same failure-message style, naming the missing
declaration and the file.

Decide whether the check should cover every bats file or only those
referencing `BATS_TEST_TMPDIR`. Covering every file is simpler to reason
about and would require adding the line to `spec-model.bats`; scoping it to
files that use the variable ties the requirement to the actual hazard. The
first is probably right — the declaration is cheap, and a uniform rule has
no exceptions to maintain.

Raised by the final review of issue 177. Design context:
[2026-07-28-177-bats-temp-dirs-design.md](../specs/2026-07-28-177-bats-temp-dirs-design.md).
