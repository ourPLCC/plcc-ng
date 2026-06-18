# Design: Hoist test setup out of leaf scripts (issue 096)

## Problem

`bin/test/functional.bash` orchestrates four leaf scripts (`units.bash`,
`commands.bash`, `integration.bash`, `e2e.bash`). Each leaf independently
runs environment setup:

| Script | Setup calls |
|---|---|
| `units.bash` | `bin/install/pdm.bash`, `pdm install` |
| `commands.bash` | `bin/install/bats.bash`, `pdm install` |
| `integration.bash` | `bin/install/bats.bash`, `pdm install` |
| `e2e.bash` | `bin/install/bats.bash`, `pdm install` |

A full `functional.bash` run therefore invokes `pdm install` four times and
`bin/install/bats.bash` three times. Both are idempotent but not free.

## Design

### `functional.bash`

Run all three setup steps once, before invoking the leaf scripts. Pass
`SKIP_SETUP=1` inline on each leaf invocation so the flag is scoped to the
subprocess and does not leak into the surrounding environment.

```bash
_run() {
    "${SCRIPT_DIR}/../install/pdm.bash"
    pdm install
    "${SCRIPT_DIR}/../install/bats.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/units.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/commands.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/integration.bash"
    SKIP_SETUP=1 "${SCRIPT_DIR}/e2e.bash"
}
```

### Leaf scripts

Wrap each script's setup block in a `SKIP_SETUP` guard:

```bash
if [[ -z "${SKIP_SETUP:-}" ]]; then
    # existing setup calls
fi
```

- `units.bash` guards: `bin/install/pdm.bash` + `pdm install`
- `commands.bash`, `integration.bash`, `e2e.bash` each guard: `bin/install/bats.bash` + `pdm install`

Direct callers of individual leaf scripts are unaffected — setup runs as
before when `SKIP_SETUP` is unset.

## Invariants

- `functional.bash` always calls `bin/install/pdm.bash` before `pdm install`
  (same as today; just centralised).
- Each leaf script remains independently runnable without setting any env vars.
- `SKIP_SETUP=1` is the documented contract for skipping setup; no other value
  is tested.

## Testing

No new test infrastructure is needed. The existing functional test suite
validates correct behaviour. A manual smoke-check of `bin/test/functional.bash`
and a direct call to one leaf script (e.g. `bin/test/units.bash`) confirms both
paths work.
