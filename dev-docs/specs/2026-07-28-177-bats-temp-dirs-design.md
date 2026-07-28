# 177 — bats tests use `BATS_TEST_TMPDIR` instead of `mktemp`

**Date:** 2026-07-28
**Issue:** [177](../issues/177-bats-helpers-leak-temp-dirs.md)

## Problem

Bats tests create temporary files and directories with `mktemp` and remove them
by hand. Forty-two files do this across 102 call sites, using three different
cleanup mechanisms — `teardown()`, `trap … EXIT` inside a test body, and
`trap … RETURN` inside a helper function — plus a fourth non-mechanism, a bare
`rm` as the last line of the test body.

Most of it works. Verified against the pinned bats: an EXIT trap set in a test
body fires even when the test fails, and a RETURN trap set in a helper fires
when the helper returns. Files relying on either are correct today.

Two groups are not.

1. **One unconditional leak.** `setup_arbno_build` and
   `setup_mid_body_arbno_build` in `tests/bats/e2e/plcc-rep.bats` each
   `mktemp -d` a build directory, while `teardown()` removes only the `WORK_DIR`
   that `setup()` created. Nothing else covers them. Six directories leak per
   run of that file, each holding a complete `plcc-ng/` build tree. This is the
   defect issue 177 was filed for.

2. **Six latent leaks.** Cleanup is the last line of the test body, so it runs
   only when it is not needed — bats aborts a body at the first failing command:
   `cache.bats` (`fake_bin`), `plcc-haskell-emit.bats` (`out`, three tests),
   `plcc-tokens.bats` (`tmp`, `VERBOSITY_SPEC_JSON`),
   `plcc-parse-errors.bats` (`tmp`), `happy-path.bats` (`FULL_DIR`), and
   `java-emit.bats:88` (`SPEC_JSON`, `LL1_JSON`). These leak exactly when a
   test fails, which is when the debris is least welcome.

The measured cost is consistent with that diagnosis. One development container
had 518 leftover `tmp.*` directories totalling 32M, 134 of them holding a
`plcc-ng/` build tree — about twenty-two runs' worth of the `plcc-rep.bats`
leak, plus failure-path debris.

The deeper problem is the variety itself. Four mechanisms for one concern means
a reviewer must check each new test against the right one, and the two failure
modes above are what that costs.

## Approach

Bats supplies this feature. It exports three temporary directories and removes
each at the end of its scope:

- `BATS_TEST_TMPDIR` — unique per test.
- `BATS_FILE_TMPDIR` — shared by the tests in one file.
- `BATS_SUITE_TMPDIR` — shared by the whole run.

Cleanup belongs to the runner, so it happens whether the test passes, fails, or
aborts partway. `--no-tempdir-cleanup` preserves the directories for debugging.
`bin/install/bats.bash` pins 1.11.0, so all three are available.

Verified against the pinned version: a test that writes into `BATS_TEST_TMPDIR`
finds the directory gone after the run, and the `/tmp` entry count is unchanged.

We therefore write no cleanup code of our own. An earlier draft of this design
proposed a `tests/bats/helpers/temp.bash` that registered allocations in an
array and removed them from a helper-owned `teardown()`. That is a
reimplementation of the above, with its own failure mode: `load` runs before the
test file's own definitions, so a file that defines `teardown()` after loading
the helper silently overrides the cleanup. The approach is rejected.

## Design

### Conversion

Every `mktemp` call in `tests/bats/**/*.bats` becomes a path under
`BATS_TEST_TMPDIR`:

| Before | After |
| --- | --- |
| `WORK_DIR="$(mktemp -d)"` | `WORK_DIR="${BATS_TEST_TMPDIR}/work"` and `mkdir -p "${WORK_DIR}"` |
| `SPEC_JSON="$(mktemp)"` | `SPEC_JSON="${BATS_TEST_TMPDIR}/spec.json"` |
| `BAD_SPEC="$(mktemp --suffix=.plcc)"` | `BAD_SPEC="${BATS_TEST_TMPDIR}/bad.plcc"` |

All four cleanup mechanisms go with it. A `teardown()` that only removed
temporaries is deleted; one that does more keeps its remaining work. Every
`trap … EXIT` and `trap … RETURN` whose only job was removing a temporary is
deleted, as is every inline `rm` at the end of a test body.

Two `teardown()` bodies survive, for work unrelated to temporaries:
`cache.bats` keeps `rm -f "${DIRTY_FILE}"` (a file it creates in the repository
root, not a temporary), and `test-scripts-path-filter.bats` keeps its
`unset SKIP_SETUP` and `unset PLCC_NO_TEST_CACHE`.

Names replace `mktemp` randomness: `spec.json` and `model.json` read better than
`tmp.4Xk9Qm` in a failure trace, and they document what each path holds.

Scope is all 42 files that call `mktemp`, not only the seven with a real or
latent leak. The other 35 are correct today but hand-rolled; converting them
lets the guard below run without an allowlist, and allowlists of files exempted
from a lint tend to outlive their justification. The gain there is deletion:
those files stop carrying cleanup code for a job the runner already does.

`BATS_TEST_TMPDIR` is the right scope in every case here, because each of these
allocations happens in `setup()` or in a test body, both of which already run
per test. No file needs `BATS_FILE_TMPDIR` or `BATS_SUITE_TMPDIR`.

Two call sites need care rather than substitution:

- `haskell_roundtrip.bats` has
  `OUT_DIR="${HASKELL_ROUNDTRIP_OUT_DIR:-$(mktemp -d)}"`. The environment
  override is a feature and stays; only the fallback changes to
  `"${BATS_TEST_TMPDIR}/out"`. Its `teardown()` then goes away entirely: the
  guard around removing `OUT_DIR` existed precisely to avoid deleting a
  caller-supplied directory, and once the fallback lives under
  `BATS_TEST_TMPDIR` the runner removes it while leaving an overridden path
  untouched.
- Files under `bin/` also call `mktemp`. They are not bats tests, are not
  covered by the runner's cleanup, and are out of scope.

### Version guard

Every converted file gets `bats_require_minimum_version 1.5.0` if it lacks it —
currently `happy-path.bats`, `spec-tokens.bats`, and `model-lang-emit.bats`.
Without it, an older bats leaves `BATS_TEST_TMPDIR` unset and a path like
`"${BATS_TEST_TMPDIR}/work"` silently becomes `/work`. The declaration converts
that into a clear startup failure. 1.5.0 is the value already used throughout
the repository, and the pinned 1.11.0 satisfies it.

### Guard test

`tests/bats/commands/bats-temp-dirs.bats` holds two tests:

1. **No bats test file calls `mktemp`.** Scans `tests/bats/**/*.bats`, excluding
   itself via `$BATS_TEST_FILENAME`, and fails listing every offending file and
   line. The failure message names `BATS_TEST_TMPDIR` as the replacement, so the
   lint teaches the convention at the point of violation.
2. **Bats removes `BATS_TEST_TMPDIR` after a test.** Runs a generated one-test
   bats file that records its `BATS_TEST_TMPDIR`, then asserts the directory is
   gone. This is a canary on the property the whole design rests on: if the
   version pin in `bin/install/bats.bash` ever moves to a release that changes
   this behaviour, this test fails rather than the leak returning unnoticed.

It lives in `tests/bats/commands/` because that tier already holds meta-tests of
repository tooling (`test-scripts-path-filter.bats`, `issues-close.bats`,
`release-verify.bats`) and an existing runner picks the directory up with no
change to `bin/test/`.

### Documentation

`CONTRIBUTING.md` gains a short paragraph in its testing section: bats tests
allocate temporary paths under `BATS_TEST_TMPDIR` and never call `mktemp`; bats
removes the directory itself, so tests need no cleanup code.

## Testing

The conversion is behaviour-preserving, so the existing suites are the test: a
converted file must pass exactly as before. The units, commands, integration,
and e2e tiers run in this environment via `bin/test/functional.bash`.

`haskell.bats`, `haskell_roundtrip.bats`, and `languages-java.bats` need ghc or
`LANGUAGES_REPO_PATH` and cannot be executed here. They will be converted and
reviewed by inspection, and reported as such rather than as passing.

Beyond the suites passing, the leak itself is checked directly: count `tmp.*`
entries in `/tmp` before and after a full functional run and confirm the count
is unchanged.

## Consequences

Tests get shorter. Most converted files lose their `teardown()` entirely, and
the ones that keep it do so for a real reason. New tests cannot reintroduce the
leak without failing the guard, and the failure names the fix. The cost is a
large mechanical diff across 42 files, reviewed as a single sweep.
