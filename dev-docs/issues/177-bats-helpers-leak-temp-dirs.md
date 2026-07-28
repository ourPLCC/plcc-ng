# 177 - bats helpers in plcc-rep.bats leak temp build directories

**Type:** test
**Date:** 2026-07-28

## Description

In `tests/bats/e2e/plcc-rep.bats`, the `setup_arbno_build` and
`setup_mid_body_arbno_build` helpers each `mktemp -d` a build
directory (`ARBNO_DIR`, `MID_BODY_DIR`) that the file's `teardown()`
never removes — it only cleans up `WORK_DIR`, which is created by the
file's `setup()`, not by these two helpers. Every e2e run that
exercises the arbno tests (`trivial-arbno`, `arbno-mid-body-terminal`)
leaves one or two directories behind in `/tmp`.

bats runs `teardown()` in the same shell as the test, so `ARBNO_DIR`
and `MID_BODY_DIR` are in scope there; they're just never removed.

## Steps to Reproduce

1. Note `/tmp` entries before a run: `ls /tmp | wc -l`.
2. Run `bin/test/e2e.bash tests/bats/e2e/plcc-rep.bats` (or however
   the e2e tier is invoked for this file).
3. Note `/tmp` entries after: `ls /tmp | wc -l`.
4. Observe leftover `tmp.XXXXXXXXXX`-style directories, one per
   `setup_arbno_build`/`setup_mid_body_arbno_build` call across the
   file's tests, containing a stale `plcc-ng/` build tree.

## Notes

Fix is one line in `teardown()`:

```bash
rm -rf "${WORK_DIR}" "${ARBNO_DIR:-}" "${MID_BODY_DIR:-}"
```

The `:-` guards keep `teardown()` safe for tests that never called
either helper (so the variables are unset).
