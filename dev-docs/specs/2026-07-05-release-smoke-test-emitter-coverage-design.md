# Release smoke test emitter coverage — design

**Issue:** [137](../issues/137-release-smoke-test-emitter-coverage.md)
**Date:** 2026-07-05

## Problem

The "Smoke test TestPyPI install" step in `.github/workflows/release.yml` installs the
published package into a clean venv and runs `plcc-make --spec=tests/fixtures/trivial.plcc`,
checking only that `plcc-ng/spec.json` is written. None of the four emitters (Python, Java,
Haskell, JavaScript) is ever invoked, so a published wheel missing emitter runtime package
data (e.g. `runtime/*.js`, `runtime/*.hs`, `runtime/org.json-*.jar`) would pass the smoke
test and ship broken. `bin/test/packaging.bash` has the same gap locally.

## Decision summary

- **Depth:** emit-only. Run each emitter and assert key files exist. No per-language
  build/run in the release path — builds add toolchain assumptions and release-blocking
  flakiness (the Haskell cabal build takes minutes and needs the network), while emit alone
  already exercises the missing-package-data failure mode: emitters copy their `runtime/`
  package data into the output directory.
- **Structure:** one shared script, `bin/test/smoke.bash`, called from both `release.yml`
  (after the TestPyPI install) and `bin/test/packaging.bash` (after the wheel install).
- **Fixture:** `tests/fixtures/trivial.plcc` drives all four emitters (verified — a spec
  with no language-specific code sections emits successfully for every target). No new
  fixtures needed.
- **Dispatch:** invoke emitters through `plcc-lang-emit --target=<lang>`, not
  `plcc-<lang>-emit` directly, so the smoke test also exercises language discovery in the
  installed package.
- **Languages:** the four are hard-coded. This is a v1 release gate (issue 112), not a
  plugin enumeration.

## `bin/test/smoke.bash`

Assumes the `plcc-*` entry points are already on `PATH` (installed from a wheel or from
TestPyPI — the script doesn't care which). Follows the existing `bin/test/` style
(`set -euo pipefail`, `PROJECT_ROOT` derivation, loud `FAIL:` messages, exit 1).

Checks, in order:

1. `plcc-make --spec="$PROJECT_ROOT/tests/fixtures/trivial.plcc"` in a temp dir;
   `plcc-ng/spec.json` and `plcc-ng/model.json` must exist (preserves the current
   release-workflow check and the `model.json` check from `packaging.bash`).
2. For each language, `plcc-spec trivial.plcc | plcc-model | plcc-lang-emit
   --target=<lang> --output=<tmpdir>`, then assert one generated file plus runtime
   package-data files:

   | Language   | Generated      | Runtime package data                           |
   |------------|----------------|------------------------------------------------|
   | python     | `Program.py`   | `runtime/base.py`                              |
   | java       | `Program.java` | `runtime/Token.java`, `runtime/org.json-*.jar` |
   | javascript | `Program.js`   | `runtime/base.js`                              |
   | haskell    | `Program.hs`   | `Token.hs`, `interpreter.cabal`                |

Each failed assertion prints `FAIL: <lang>: <file> missing` and exits 1.

The script does not use the test-output cache (`_cache.bash`): its result depends on which
package is installed on `PATH`, not on git state, so caching would be incorrect.

## Call sites

1. **`.github/workflows/release.yml`** — the "Smoke test TestPyPI install" step keeps its
   install-with-retry loop, then replaces the inline `plcc-make`/`test -f` lines with a
   call to `bin/test/smoke.bash`.
2. **`bin/test/packaging.bash`** — replaces its trivial `plcc-make` block (the
   `WORK_DIR` section) with a call to `bin/test/smoke.bash`. The entry-point checks,
   `plcc-lang-list`/`plcc-diagram-list` checks, and the diagram-emit check stay.

## Testing and verification

- No pytest/bats tests for the script itself, consistent with other `bin/test/` scripts.
- Verification: `PLCC_NO_TEST_CACHE=1 bin/test/packaging.bash` — runs the new script
  against a real wheel install, the release-time code path minus TestPyPI.
- `actionlint` on the workflow change if available; `bin/test/units.bash` to confirm no
  regressions.

## Close-out

`bin/issues/close.bash 137` as the final commit of the branch.
