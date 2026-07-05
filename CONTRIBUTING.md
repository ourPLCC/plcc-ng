# Contributing to plcc-ng

This document is the practical guide for working in this repository: the commands you run, the test tiers, and the conventions that keep work consistent. Read it before making changes.

For architectural context, see [dev-docs/specs/2026-04-12-multi-lang-pipeline.md](dev-docs/specs/2026-04-12-multi-lang-pipeline.md) (architectural spec). Open work is tracked in [dev-docs/roadmap.md](dev-docs/roadmap.md); the issue workflow behind it is described in [dev-docs/issue-conventions.md](dev-docs/issue-conventions.md). This document does not duplicate them.

## Common commands

All operational commands live in [bin/](bin/). **Before writing a new script, check [bin/](bin/) first — the script you need probably already exists.**

### Build

| Command | What it does |
|---|---|
| [bin/build/package.bash](bin/build/package.bash) | Run `pdm install` and `pdm build` to produce a wheel in `dist/`. Self-installs `pdm` if missing. |

### Install helpers

| Command | What it does |
|---|---|
| [bin/install/pdm.bash](bin/install/pdm.bash) | Install `pdm` via pip if not already on PATH. Idempotent. |
| [bin/install/bats.bash](bin/install/bats.bash) | Install the pinned `bats` version under `~/.local/` if not already present. Idempotent. |

### Test

| Command | What it does | When to use |
|---|---|---|
| [bin/test/units.bash](bin/test/units.bash) | Run Python unit tests via pytest (wrapped as `pdm test`). Accepts pytest args. Fastest tier. | **TDD inner loop.** Run this on every edit. |
| [bin/test/commands.bash](bin/test/commands.bash) | Run black-box CLI tests (`tests/bats/commands/`) for individual commands exercised through their installed entry points. Covers both Level 0 primitives and Level 2 orchestrators (see architectural spec §5–6). | After finishing a command's unit tests, verify its CLI contract. |
| [bin/test/integration.bash](bin/test/integration.bash) | Run adjacent-pair pipeline tests (`tests/bats/integration/`). | After touching a stage that sits next to another in the pipeline. |
| [bin/test/e2e.bash](bin/test/e2e.bash) | Run end-to-end pipeline tests (`tests/bats/e2e/`). | After changes that could affect the whole pipeline. |
| [bin/test/functional.bash](bin/test/functional.bash) | Run all functional tiers (units + commands + integration + e2e). Does NOT include the Haskell roundtrip (see below). | Before pushing. |
| [bin/test/e2e_haskell_roundtrip.bash](bin/test/e2e_haskell_roundtrip.bash) | Run the slow Haskell full-build roundtrip test (`tests/bats/e2e/haskell_roundtrip.bats`). Invokes `cabal build` and can take several minutes on a cold cache. | After changes to the Haskell emitter, runtime, or Haskell-specific fixtures. |
| [bin/test/packaging.bash](bin/test/packaging.bash) | Build a wheel, install it into a throwaway venv, verify all entry points resolve, and run a smoke test against the installed package. | After changes to `pyproject.toml`, entry points, or packaging layout. |
| [bin/test/all.bash](bin/test/all.bash) | Run `functional.bash` then `e2e_haskell_roundtrip.bash` then `packaging.bash`. | Full local pre-push check including the Haskell roundtrip. |

### Test output cache

All test scripts cache their output to `/tmp` so agents and tools can grep results without re-running the suite. The cache is keyed on git state (`git status --porcelain` + `git rev-parse HEAD`) and is invalidated automatically whenever the working tree or HEAD changes.

| Command | What it does |
|---|---|
| [bin/test/cache/stats.bash](bin/test/cache/stats.bash) | Print a hit/miss/skip summary, overall and per-script. |
| [bin/test/cache/clear.bash](bin/test/cache/clear.bash) | Remove all cached test output files from `/tmp`. |
| [bin/test/cache/clear-stats.bash](bin/test/cache/clear-stats.bash) | Clear the cache statistics log. |

**Environment variable:** set `PLCC_NO_TEST_CACHE=1` to bypass the cache for a single run — the test suite runs live and the cache is neither read nor written (the run is still logged as a skip in the stats).

**When the cache helps:**

- Grepping test output after a run without re-running the suite.
- Quickly re-running a script to check something when you know the code hasn't changed.
- Agents that call a test script multiple times to inspect different slices of output.

**When to bypass the cache (`PLCC_NO_TEST_CACHE=1`):**

- When you want to force a fresh run regardless of git state (e.g. after changing a fixture file that git doesn't track, or when debugging a flaky test).
- In CI — the variable is set automatically for all test steps.
- When you suspect the cache is stale and `bin/test/cache/clear.bash` is more than you need.

### Release

| Command | What it does |
|---|---|
| [bin/release/extract-changelog.bash](bin/release/extract-changelog.bash) | Print the `CHANGELOG.md` section for a version. Used by the release workflow for GitHub Release notes. |
| [bin/release/verify.bash](bin/release/verify.bash) | Verify a published release: PyPI has the version, the GitHub Release exists, versioned docs are deployed, and the package installs from PyPI and passes the smoke test. See [dev-docs/release-sop.md](dev-docs/release-sop.md). |

## TDD inner loop

plcc-ng is built test-first.

1. Write a failing test in the appropriate tier (see below).
2. Run [bin/test/units.bash](bin/test/units.bash) and confirm the failure.
3. Write the minimal code to make it pass.
4. Run [bin/test/units.bash](bin/test/units.bash) again and confirm the pass.
5. Commit.

[bin/test/units.bash](bin/test/units.bash) runs in seconds and is the tightest feedback loop available. Keep it green at every commit.

## Test tiers

Tests are organized into tiers by scope. Each tier has its own directory and its own runner. Put a new test in the narrowest tier that can exercise what you are testing.

| Tier | Location | Scope |
|---|---|---|
| **Unit** | Alongside the code under test in `src/`, named `<module>_test.py` (pytest) | A single Python function, class, or module in isolation. No subprocesses. Must run in milliseconds. This is where most tests live. Co-locating the test with the code it tests keeps the two in sync and makes the test the first thing a reader sees when opening a module's directory. |
| **Commands** | `tests/bats/commands/` | A single command exercised as a black box via its installed entry point. Stdin/stdout/exit-code contract. Level 2 orchestrators live here too even though they internally compose other commands — what distinguishes this tier is that only one installed command is invoked per test. |
| **Integration** | `tests/bats/integration/` | Adjacent pipeline stages composed together (e.g. `plcc-tokens` piped into `plcc-trees`). Exercises the contract between two stages. |
| **End-to-end** | `tests/bats/e2e/` | The full pipeline from spec file to final output, via `plcc-make` or equivalent orchestrator. Exercises the whole system against a fixture. |
| **Packaging** | [bin/test/packaging.bash](bin/test/packaging.bash) | Builds a wheel, installs it into a fresh venv, and verifies entry points and a smoke test. Catches `pyproject.toml` regressions. |

Rules of thumb:

- If a unit test can cover it, write a unit test.
- Reach for a bats tier only when the contract you are verifying is at the CLI boundary, spans multiple commands, or depends on installed entry points.
- If you are tempted to skip a test tier during active development, don't. Either migrate it to a tier that still passes, or delete it. Indefinite skips rot.

## Before writing a new script

Check [bin/](bin/) first. If a script there does what you need, use it. If one almost does what you need, prefer extending or parameterizing it over writing a parallel script. New scripts belong in [bin/](bin/) with a `.bash` extension, `set -euo pipefail`, and absolute-path resolution via `SCRIPT_DIR`/`PROJECT_ROOT` — match the existing style.

## Workflow

Work happens on feature branches, not on `main`. Branch names describe the work (e.g. `fix-scanner-skip-regression`, `add-python-emitter`). Long-running initiatives may use a shared integration branch, but that is a property of the initiative, not a general rule — there is currently no such branch; everything merges directly to `main`.

Commits follow conventional-commit style (`feat(scope): …`, `fix(scope): …`, `docs(scope): …`, `test(scope): …`, `refactor(scope): …`, `build(scope): …`, `ci: …`, `chore: …`). Match the scope names already in use in the git log. The CI workflow skips automatically for pull requests that touch only `dev-docs/`, `docs/`, top-level `*.md` files, `mkdocs.yml`, or `mkdocs-dev.yml` — no `[skip ci]` annotation needed.
