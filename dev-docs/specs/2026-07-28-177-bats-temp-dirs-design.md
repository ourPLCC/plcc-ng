# 177 — bats tests use `BATS_TEST_TMPDIR` instead of `mktemp`

**Date:** 2026-07-28
**Issue:** [177](../issues/177-bats-helpers-leak-temp-dirs.md)

## Problem

Bats tests create temporary files and directories with `mktemp` and rely on a
hand-written `teardown()` to remove them. That contract is unenforced, and it is
broken in thirteen files:

| File | Temps never removed |
| --- | --- |
| `tests/bats/commands/cache.bats` | `fake_bin` |
| `tests/bats/commands/plcc-haskell-emit.bats` | `out` |
| `tests/bats/commands/plcc-tokens.bats` | `VERBOSITY_SPEC_JSON`, `tmp` |
| `tests/bats/commands/plcc-validate-semantic.bats` | `SPEC_JSON` |
| `tests/bats/commands/plcc-validate-syntactic.bats` | `SPEC_JSON` |
| `tests/bats/e2e/happy-path.bats` | `DIAGRAM_DIR`, `FULL_DIR` |
| `tests/bats/e2e/haskell.bats` | `SPEC_JSON`, `MODEL_JSON` |
| `tests/bats/e2e/haskell_roundtrip.bats` | `SPEC_JSON`, `MODEL_JSON`, `LL1_JSON` |
| `tests/bats/e2e/languages-java.bats` | `build_dir`, `ll1_json` |
| `tests/bats/e2e/plcc-rep.bats` | `ARBNO_DIR`, `MID_BODY_DIR` |
| `tests/bats/integration/java-emit.bats` | `SPEC_JSON`, `LL1_JSON`, `NULL_DIR`, `NO_SEM_DIR` |
| `tests/bats/integration/plcc-parse-errors.bats` | `tmp` |
| `tests/bats/integration/python-emit.bats` | `LL1_JSON`, `TREE_FILE`, `NO_SEM_DIR` |

Two distinct mistakes produce this:

1. **A helper allocates, but `teardown()` does not know about it.** The case
   issue 177 was filed for: `setup_arbno_build` and `setup_mid_body_arbno_build`
   in `plcc-rep.bats` each `mktemp -d` a build directory, while `teardown()`
   removes only the `WORK_DIR` that `setup()` created.
2. **Cleanup is the last line of the test body.** `plcc-haskell-emit.bats` ends
   its tests with `rm -rf "$out"`. Bats aborts a test body at the first failing
   command, so this line runs only when it is not needed.

The cost is measurable. One development container had 518 leftover `tmp.*`
directories totalling 32M, 134 of them holding a complete `plcc-ng/` build tree.

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

A `teardown()` that only removed temporaries is deleted. One that does more
keeps its remaining work. Inline `rm -rf` at the end of a test body and the
`trap … EXIT` in `plcc-rep.bats` are deleted.

Names replace `mktemp` randomness: `spec.json` and `model.json` read better than
`tmp.4Xk9Qm` in a failure trace, and they document what each path holds.

Scope is all 42 files that call `mktemp`, not only the 13 that leak. The
remaining 29 are correct today but written the old way; converting them lets the
guard below run without an allowlist. Allowlists of files exempted from a lint
tend to outlive their justification.

`BATS_TEST_TMPDIR` is the right scope in every case here, because each of these
allocations happens in `setup()` or in a test body, both of which already run
per test. No file needs `BATS_FILE_TMPDIR` or `BATS_SUITE_TMPDIR`.

Two call sites need care rather than substitution:

- `haskell_roundtrip.bats` has
  `OUT_DIR="${HASKELL_ROUNDTRIP_OUT_DIR:-$(mktemp -d)}"`. The environment
  override is a feature and stays; only the fallback changes to
  `"${BATS_TEST_TMPDIR}/out"`.
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
