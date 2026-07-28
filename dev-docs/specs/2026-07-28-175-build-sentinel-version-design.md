# Build sentinel ignores the installed PLCC-ng version — design

**Issue:** [175](../issues/done/175-build-sentinel-ignores-package-version.md)

## Problem

`src/plcc/build/staleness.py` records two things in the build sentinel
(`plcc-ng/.spec-hash`): the SHA-256 of the generated `spec.json` and the
set of completed stages.

```python
def write_sentinel(build_dir, hash_, stages):
    (Path(build_dir) / _SENTINEL).write_text(
        json.dumps({"hash": hash_, "stages": sorted(stages)})
    )
```

The installed PLCC-ng version appears nowhere. Because generated
artifacts (`ll1.json`, `model.json`, emitted source) are a function of
both the spec *and* the code that generates them, a sentinel keyed only
on the spec is incomplete: upgrading the package cannot invalidate a
cached build. With an unchanged spec, `is_current` reports the build as
current and `plcc-make` takes the fast path, reusing artifacts produced
by the old code.

Issue #174 is the concrete instance. A user who hit the repetition-rule
bug has a *successfully built* `plcc-ng/` directory — the build
succeeded; only parsing failed. After upgrading to the fixed version,
`plcc-make` sees the same spec hash, reports the build current, and
reuses the old `ll1.json`. The fix silently never reaches them. The
v2.0.1 `docs/whats-new.md` entry currently works around this by telling
users to delete their build directory by hand.

## Decision

Record the installed package version in the sentinel alongside the hash
and stages, and require it to match. A version change then invalidates a
cached build exactly the way a spec change does.

The version is threaded through the sentinel API as an explicit
argument rather than read inside `staleness.py`:

```python
def write_sentinel(build_dir, hash_, stages, version):
    (Path(build_dir) / _SENTINEL).write_text(
        json.dumps({"hash": hash_, "stages": sorted(stages), "version": version})
    )


def is_current(sentinel, hash_, required_stages, version):
    if sentinel is None:
        return False
    if sentinel.get("hash") != hash_:
        return False
    if sentinel.get("version") != version:
        return False
    completed = set(sentinel.get("stages", []))
    return required_stages.issubset(completed)
```

`plcc-make` is the only consumer of this API (verified by grep over
`src/`). It captures `version = get_version()` once — `plcc.version`
is already imported there for `--banner` — and passes it to both
`is_current` and `write_sentinel`.

### Why an explicit argument

Two alternatives were considered and rejected:

- **`staleness.py` calls `get_version()` itself.** No signature change,
  but it hides the dependency and forces monkeypatching to test what is
  otherwise a set of pure functions.
- **Fold the version into the hash** (digest the spec bytes *and* the
  version string). No signature change at all, but the sentinel becomes
  opaque: a spec change and a version change are indistinguishable both
  in the code and in the on-disk file.

The explicit argument keeps `staleness.py` pure and directly testable,
and keeps the sentinel readable so a stale build's cause is visible.

### Legacy sentinels

A sentinel written before this change has no `"version"` key, so
`sentinel.get("version")` is `None`, which never equals a real version
string. Every pre-existing build directory therefore reads as stale and
rebuilds once, automatically, on the first `plcc-make` after upgrading.
That is precisely the #174 upgrade case, handled with no user action —
so the "delete your build directory" paragraph in the v2.0.1
`docs/whats-new.md` entry is removed as part of this change.

The sentinel file keeps its `.spec-hash` name. Renaming it to something
more honest would achieve the same invalidation (the old file would
simply be ignored) but would strand an orphan `.spec-hash` in every
existing build directory and churn the bats tests that assert on the
path, for no functional gain.

### No new output

A version-triggered rebuild is indistinguishable from a spec-triggered
one. Spec-triggered rebuilds are already silent — `plcc-make` just takes
the slow path — and consistency is worth more here than an explanation
the user sees once per upgrade.

## Non-goals

- **Editable/development installs.** An editable install reports one
  version string across arbitrary source edits, so this does not force
  rebuilds while developing PLCC-ng itself. The issue is about released
  upgrades.
- **`get_version()` returning `"unknown"`.** When package metadata is
  missing, two such environments compare equal and the build is reused.
  Acceptable: an environment without installed metadata is not one
  where version-based invalidation can mean anything.

## Testing

**Units** (`src/plcc/build/staleness_test.py`) — the sentinel roundtrip
carries the version; `is_current` is false on version mismatch, false
when the `"version"` key is absent (the legacy-sentinel case), and true
when the versions match. Existing tests are updated for the new
argument.

**Commands** (`tests/bats/commands/plcc-make.bats`) — build, rewrite the
version inside `plcc-ng/.spec-hash` to a bogus value, delete `ll1.json`,
run `plcc-make` again, and assert `ll1.json` is back: the slow path was
taken. This mirrors the existing fast-path tests, which prove the
converse by deleting `ll1.json` and asserting it stays gone.
