# 177 - bats tests hand-roll temp cleanup

**Type:** test
**Date:** 2026-07-28

## Description

Bats tests create temporary files and directories with `mktemp` and clean them
up by hand, using four different mechanisms across 42 files and 102 call
sites: `teardown()`, `trap … EXIT` inside a test body, `trap … RETURN` inside a
helper function, and a bare `rm` as the last line of a test body.

`setup_arbno_build` and `setup_mid_body_arbno_build` in
`tests/bats/e2e/plcc-rep.bats` are covered by none of them — each `mktemp -d`s
a build directory that the file's `teardown()` never removes — and leak six
directories per run, each holding a complete `plcc-ng/` build tree.

While implementing the fix we discovered a second, larger problem: an in-body
`trap … EXIT` does not fire in a bats file that also defines `teardown()` —
bats installs its own EXIT trap to drive teardown, replacing the test's. Every
allocation cleaned up this way looked correct but leaked on every run, not
only on failure. `EMPTY_DIR` in `plcc-rep.bats` was one such case, bringing
that file's measured leak to seven directories per run (six holding build
trees, one empty). The same pattern recurs in `java-emit.bats`,
`python-emit.bats`, and `happy-path.bats`.

Six further files clean up on the last line of the test body, so they leak
whenever the test fails before reaching that line — exactly when the debris is
least welcome.

## Steps to Reproduce

1. Note `/tmp` entries before a run: `ls -d /tmp/tmp.* | wc -l`.
2. Run `bats tests/bats/e2e/plcc-rep.bats`.
3. Note `/tmp` entries after: `ls -d /tmp/tmp.* | wc -l`.
4. Observe `leaked=7`: six `tmp.XXXXXXXXXX` directories each containing a
   stale `plcc-ng/` build tree (from `setup_arbno_build` and
   `setup_mid_body_arbno_build`), plus one empty directory (`EMPTY_DIR`, whose
   `trap … EXIT` never fires because the file defines `teardown()`).

After the fix, the same measurement is 0, independently verified.

## Notes

Bats supplies `BATS_TEST_TMPDIR`, `BATS_FILE_TMPDIR`, and `BATS_SUITE_TMPDIR`
and removes each at the end of its scope regardless of whether the test
passes, fails, or aborts partway. The fix is to delete the hand-rolled cleanup
and allocate under `BATS_TEST_TMPDIR` instead of extending any of the four
existing mechanisms.

Full corrected analysis, the rejected alternative (a shared cleanup helper,
which has its own `teardown()`-override failure mode), and the conversion
design: [dev-docs/specs/2026-07-28-177-bats-temp-dirs-design.md](../specs/2026-07-28-177-bats-temp-dirs-design.md).
