# 143 - verify-python-version-preflight

**Type:** fix
**Date:** 2026-07-06

## Description

`bin/release/verify.bash` builds its throwaway venv from whatever
`python3` is on PATH. When that interpreter does not satisfy the
package's `requires-python` (>=3.12), pip filters out **every** release
and fails with the misleading `No matching distribution found for
plcc-ng==<version>` — after burning through the full retry loop, since
the failure looks identical to index lag. The devcontainer's default
`python3` (both `/usr/local/python/current/bin/python3` and
`/usr/bin/python3`) is 3.9.2, so the script fails this way out of the
box unless the project venv happens to be on PATH. This is what actually
broke verification of v0.67.0 (initially misattributed to the
simple-index race, #142).

## Steps to Reproduce

1. In a shell whose `python3` is older than 3.12 (the devcontainer
   default), run `bin/release/verify.bash v0.67.0`.
2. Checks 1–3 pass; check 4 retries five times and fails with
   `No matching distribution found`, even though PyPI serves the
   version fine.

## Notes

Fix: before creating the venv, compare `python3 --version` against
`requires-python` parsed from `pyproject.toml`, and fail fast with a
diagnostic that names the actual problem and the remedy (put a
satisfying python3 on PATH, e.g. the project venv's).
