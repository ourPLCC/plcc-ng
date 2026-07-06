# 142 - verify-pypi-simple-index-race

**Type:** fix
**Date:** 2026-07-06

## Description

`bin/release/verify.bash` can report `OK: PyPI has plcc-ng <version>` and
then fail the install step with `No matching distribution found`. Check 1
polls PyPI's JSON API (`pypi.org/pypi/plcc-ng/<version>/json`), but pip
installs from the simple index (`pypi.org/simple/plcc-ng/`), which is
CDN-served and updates later. Right after a publish the JSON API can know
the version while the simple index does not, so the check passes without
the release actually being installable — a false positive that wastes the
maintainer's time chasing a healthy release (seen on v0.67.0, 2026-07-05).

## Steps to Reproduce

1. Publish a release.
2. Run `bin/release/verify.bash v<version>` immediately, inside the
   propagation window where the JSON API lists the version but the simple
   index does not yet.
3. Check 1 prints OK; check 4 exhausts its retries with
   `ERROR: No matching distribution found for plcc-ng==<version>`.

## Notes

Fix: make check 1 poll the same index pip resolves against — fetch
`https://pypi.org/simple/plcc-ng/` and look for a `plcc_ng-<version>`
distribution file (note the normalized `_`) — so the retry loop waits on
the thing that actually gates the install. Related: #140 covered the same
propagation race for the TestPyPI smoke test in CI.
