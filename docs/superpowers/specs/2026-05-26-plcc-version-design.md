# Design: plcc-version command

**Date:** 2026-05-26
**Issue:** 034

## Summary

Add a `plcc-version` standalone command that prints the installed version of `plcc-ng` to stdout and exits 0.

## Output format

```
plcc-ng 1.2.3
```

Follows the `<name> <version>` convention used by Python (`Python 3.14.2`) and git (`git version 2.53.0`). Output goes to stdout. No flags.

When package metadata is unavailable (running from source without `pdm install`), prints:

```
plcc-ng unknown
```

and still exits 0. In practice, `pdm install` always creates metadata — including in development, where SCM versioning produces a PEP 440 dev string like `0.22.1.dev9+g8cfa461`. The `unknown` fallback is a safety net for unsupported run-from-source cases only.

## Module

**`src/plcc/version.py`** — package-level utility, following the same pattern as `verbose.py`.

Two public names:

- `get_version() -> str` — returns the version string via `importlib.metadata.version("plcc-ng")`, falls back to `"unknown"` on `PackageNotFoundError`.
- `main()` — calls `get_version()`, prints `plcc-ng <version>` to stdout, exits 0.

No imports from other `plcc` submodules. No CLI flags.

## Entry point

In `pyproject.toml`:

```toml
plcc-version = "plcc.version:main"
```

## Future use

Other commands that want a `--version` flag can import `get_version` from `plcc.version` without touching `cmd/`.

## Testing

**Unit (`src/plcc/version_test.py`):**

- `get_version()` returns a string when `importlib.metadata.version` succeeds (mock it).
- `get_version()` returns `"unknown"` when `PackageNotFoundError` is raised (mock it).
- `main()` prints `plcc-ng <version>` to stdout (capture stdout).

**Commands bats (`tests/bats/commands/plcc-version.bats`):**

- `plcc-version` exits 0.
- Output matches `plcc-ng <version>` (regex: `^plcc-ng .+`).
