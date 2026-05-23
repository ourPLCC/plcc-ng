# 034 - Add plcc-version command

**Type:** feat
**Date:** 2026-05-23

## Description

There is no command to print the installed version of `plcc-ng`. A `plcc-version` command (or `plcc --version` flag) would let users and scripts confirm which version is installed.

## Notes

- Version string is available via `importlib.metadata.version("plcc-ng")` at runtime.
- Should print to stdout and exit 0.
- Consider whether this belongs as a standalone entry point (`plcc-version`) or as a flag on an existing orchestrator (`plcc-make --version`).
