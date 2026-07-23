# Path filter for bats-backed test tiers — design

**Issue:** [155](../issues/done/155-test-scripts-path-filter.md)
**Date:** 2026-07-23

## Problem

`bin/test/units.bash` forwards its arguments to `pdm test` (pytest), so
`bin/test/units.bash src/plcc/cmd/make_test.py` narrows to one file — the tight
TDD inner loop CONTRIBUTING.md documents. The bats-backed tiers don't offer the
same thing: `bin/test/commands.bash`, `bin/test/integration.bash`, and
`bin/test/e2e.bash` ignore any arguments and always run their whole
`tests/bats/<tier>/` directory via a hardcoded `bats tests/bats/<tier>/` call,
even though `bats` itself accepts a specific file or subdirectory.
`bin/test/functional.bash`, which composes all four, has the same gap.

This design gives each of these scripts an optional path parameter that
narrows the `bats` invocation, falling back to today's whole-tier behavior
when no path is given.

## Decision summary

1. Fix a latent cache-correctness gap that the new argument would otherwise
   expose: fold the command's arguments into the test-output cache key.
2. `commands.bash` / `integration.bash`: accept an optional path, default to
   the tier directory.
3. `e2e.bash`: accept an optional path; when given, bypass the default file
   list and the `LANGUAGES_REPO_PATH` conditional entirely.
4. `functional.bash`: detect which single tier a given path belongs to and
   run only that sub-script; a path outside all three bats directories is
   treated as a pytest path and forwarded to `units.bash` alone.
5. Document all of the above in CONTRIBUTING.md so agents and contributors
   can find and use it.

## 1. Cache key must include arguments

`bin/test/_cache.bash`'s `_cache_key()` currently hashes only git state
(`HEAD` + `status --porcelain` + `diff HEAD` + untracked file contents). It
never sees the command's arguments. Once a bats tier script accepts a path,
two different invocations at the *same* git state — e.g.
`commands.bash tests/bats/commands/plcc-make.bats` followed by
`commands.bash tests/bats/commands/plcc-diagram.bats` with no edits in
between — would hash to the same key. The second call would get a cache
*hit* and replay the first path's output as if it were its own: silently
wrong.

Fix: `run_cached` passes its trailing arguments (the wrapped command plus
its arguments, e.g. `_run tests/bats/commands/plcc-make.bats`) into
`_cache_key`, which folds them into the hash alongside the existing git
state:

```bash
_cache_key() {
    local extra_args="$1"
    local head status diff untracked
    head=$(git rev-parse HEAD 2>/dev/null) || return 1
    status=$(git status --porcelain 2>/dev/null) || return 1
    diff=$(git diff HEAD 2>/dev/null) || return 1
    untracked=$(git ls-files --others --exclude-standard -z 2>/dev/null \
        | xargs -0 -I{} cat "{}" 2>/dev/null) || return 1
    printf '%s\n%s\n%s\n%s\n%s' "${head}" "${status}" "${diff}" "${untracked}" "${extra_args}" \
        | sha256sum | cut -d' ' -f1
}
```

`run_cached` calls it as `key=$(_cache_key "$*")` (the args remaining after
`shift`'d off the cache-file — i.e. the command name and its arguments).
This is a small, targeted change needed for the new feature to be correct;
it does not change behavior for any script that never receives arguments at
the same git state (the existing hit/miss/stale-cache tests in
`tests/bats/commands/cache.bats` all call `run_cached` with fixed,
argument-free commands like `echo hello`, so they are unaffected).

## 2. `commands.bash` / `integration.bash`

Both scripts follow the same shape today:

```bash
_run() {
    cd "${PROJECT_ROOT}"
    if [[ -z "${SKIP_SETUP:-}" ]]; then
        "${PROJECT_ROOT}/bin/install/bats.bash"
        pdm install
    fi
    export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
    bats tests/bats/commands/
}

run_cached /tmp/plcc-test-commands.log _run
```

Change: `bats tests/bats/commands/` becomes
`bats "${1:-tests/bats/commands/}"`, and the trailing `run_cached` call
forwards `"$@"`:

```bash
run_cached /tmp/plcc-test-commands.log _run "$@"
```

(`integration.bash` mirrors this with `tests/bats/integration/`.)

No path validation is added — a nonexistent path is passed straight through
to `bats`, which reports it clearly on its own. This matches `units.bash`,
which does no pre-check before forwarding to pytest.

## 3. `e2e.bash`

Today `e2e.bash` builds its file list with `find` (excluding
`languages-java.bats` and `haskell_roundtrip.bats`) and conditionally adds
`languages-java.bats` back when `LANGUAGES_REPO_PATH` is set:

```bash
bats $(find tests/bats/e2e/ -name "*.bats" ! -name "languages-java.bats" ! -name "haskell_roundtrip.bats" | sort)
if [ -n "${LANGUAGES_REPO_PATH:-}" ]; then
    "${PROJECT_ROOT}/bin/install/java.bash"
    bats tests/bats/e2e/languages-java.bats
fi
```

When a path argument is given, this entire block is bypassed in favor of a
direct `bats "$1"` — the caller named exactly what they want to run,
including `languages-java.bats` or `haskell_roundtrip.bats` if they ask for
it by path. With no argument, today's default-list-plus-conditional behavior
is unchanged:

```bash
_run() {
    ...
    export PATH="${PROJECT_ROOT}/.venv/bin:${PATH}"
    if [ -n "${1:-}" ]; then
        bats "$1"
        return
    fi
    bats $(find tests/bats/e2e/ -name "*.bats" ! -name "languages-java.bats" ! -name "haskell_roundtrip.bats" | sort)
    if [ -n "${LANGUAGES_REPO_PATH:-}" ]; then
        "${PROJECT_ROOT}/bin/install/java.bash"
        bats tests/bats/e2e/languages-java.bats
    fi
}
```

## 4. `functional.bash`

`functional.bash` composes `units.bash`, `commands.bash`, `integration.bash`,
and `e2e.bash`. A single path like `tests/bats/commands/plcc-make.bats`
belongs to exactly one of those tiers, so `functional.bash` detects which
one by prefix match and forwards the path only to that sub-script, skipping
the other three entirely for that run:

```bash
_run() {
    "${SCRIPT_DIR}/../install/pdm.bash"
    pdm install
    "${SCRIPT_DIR}/../install/bats.bash"

    local path="${1:-}"
    if [[ -z "${path}" ]]; then
        SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash"
        SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash"
        return
    fi

    case "${path}" in
        tests/bats/commands*)    SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash" "${path}" ;;
        tests/bats/integration*) SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash" "${path}" ;;
        tests/bats/e2e*)         SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash" "${path}" ;;
        *)                       SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash" "${path}" ;;
    esac
}

run_cached /tmp/plcc-test-functional.log _run "$@"
```

A path that doesn't match any of the three bats prefixes is treated as a
pytest path and forwarded to `units.bash` alone — this keeps
`functional.bash <path>` uniform ("run whichever single tier owns this
path") rather than requiring the caller to know which script to invoke
directly.

## 5. Testing

- `tests/bats/commands/cache.bats`: add a case asserting that two
  `run_cached` calls with the same cache file and git state but different
  trailing arguments both miss (independent cache entries), rather than the
  second replaying the first's output.
- New file `tests/bats/commands/test-scripts-path-filter.bats` (no existing
  file tests these top-level scripts directly; `cache.bats` only covers
  `run_cached` generically). For `commands.bash` / `integration.bash` /
  `e2e.bash`: stub
  `bats` on `PATH` (capturing its invocation arguments to a file, following
  the existing `git`-stub pattern already in `cache.bats`'s "fallback: runs
  uncached when git is unavailable" case), run the script with
  `SKIP_SETUP=1` and a path argument, and assert the stub was invoked with
  exactly that path rather than the tier directory or default file list.
  Also cover the no-argument case still producing the original invocation.
- New cases for `functional.bash`: assert a `tests/bats/commands/...` path
  triggers only the commands sub-run, a non-matching path triggers only
  `units.bash`, and no argument triggers all four sub-scripts.

## 6. Documentation

Update CONTRIBUTING.md's Test section:

- The `commands.bash` / `integration.bash` / `e2e.bash` / `functional.bash`
  rows in the Test command table gain a note that they accept an optional
  path/file argument to narrow the run, parallel to the existing
  `units.bash` row's "Accepts pytest args."
- The "Test output cache" section's description of the cache key gains a
  mention that it also covers the command's arguments, not just git state.
- The "TDD inner loop" section gains a line noting that the same
  fast-narrow-rerun pattern now applies to bats-covered work via
  `commands.bash`/`integration.bash`/`e2e.bash`, not just `units.bash`.

## Files changed

| File | Change |
| --- | --- |
| `bin/test/_cache.bash` | Fold trailing args into `_cache_key` |
| `bin/test/commands.bash` | Optional path arg, default to tier dir |
| `bin/test/integration.bash` | Optional path arg, default to tier dir |
| `bin/test/e2e.bash` | Optional path arg, bypasses default list/conditional when given |
| `bin/test/functional.bash` | Route path arg to the one matching sub-script |
| `tests/bats/commands/cache.bats` | New case: args differentiate cache entries |
| `tests/bats/commands/test-scripts-path-filter.bats` (new) | Path-narrowing cases for `commands.bash`, `integration.bash`, `e2e.bash`, `functional.bash` |
| `CONTRIBUTING.md` | Document path-filter support and updated cache-key description |
