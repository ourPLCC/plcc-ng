# 160 - Concurrent plcc-scan/plcc-make invocations race on shared build dir

**Type:** fix
**Date:** 2026-07-22

## Description

Running two `plcc-scan` (or presumably any plcc-ng CLI, since they all shell
out to `plcc-make`) invocations concurrently in the same working directory
crashes both processes with a `FileNotFoundError`. Both invocations build
into the same `./plcc-ng/` directory using a temp file
(`tempfile.mkstemp(..., dir=build_dir)`), and there is no locking or
per-process isolation, so one process's cleanup/recreation of the build
directory races with the other's attempt to write or hash its temp file.

This surfaced in the plcc-ng-demo repo while comparing an in-progress
activity spec against the solution spec using
`diff <(plcc-scan -s activity/spec.plcc < in.txt) <(plcc-scan -s solution/spec.plcc < in.txt)`
— a natural thing for an instructor or student to try, since the two specs
live in sibling directories but the build directory (`plcc-ng/`) is created
relative to the current working directory, not per-spec.

Sequential invocations of the same commands work fine and produce correct,
matching output — this is purely a concurrency/shared-state bug, not a
scanning correctness issue.

## Steps to Reproduce

1. In a directory with a `spec.plcc` (or two sibling directories each with
   their own `spec.plcc`), clear any cached build dir: `rm -rf plcc-ng`
2. Run two invocations concurrently, e.g.:
   ```
   diff <(plcc-scan -s activity/spec.plcc < activity/testprog.txt) \
        <(plcc-scan -s solution/spec.plcc < activity/testprog.txt)
   ```
3. One or both sides crash with:
   ```
   FileNotFoundError: [Errno 2] No such file or directory: '.../plcc-ng/tmpXXXXXXXX.json'
   ```
   traced back through `plcc-make`'s `main()` → `tempfile.mkstemp` or
   `compute_hash`.
4. Running the two commands sequentially (not via process substitution)
   instead of concurrently succeeds every time.

## Notes

- Relevant code: `src/plcc/cmd/make.py`, `src/plcc/build/staleness.py` — the
  shared `./plcc-ng/` build directory needs either a lock around build-dir
  mutation, a per-invocation/per-spec temp directory, or at least a
  graceful retry/error instead of an unhandled traceback.
- Low severity for solo interactive use (a student typing one command at a
  time won't hit it), but plausible for instructors/graders who script
  comparisons, run parallel test suites, or use tools like
  `diff <(...) <(...)` — and the failure mode is a raw Python traceback,
  not a friendly error.
- Originally filed as issue #2 in `ourPLCC/plcc-ng-demo`, which is where it
  surfaced during workshop test-drive.
