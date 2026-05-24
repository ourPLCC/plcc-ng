# 035 - plcc-diagram --output=build hangs

**Type:** fix
**Date:** 2026-05-24

## Description

Running `plcc-diagram --output=build` hangs indefinitely and never returns.

## Steps to Reproduce

1. Run `plcc-diagram --output=build` on any grammar file.
2. Observe that the command does not exit.

## Notes

The hang appears specific to the `--output=build` flag. Investigate whether the issue is in how the output path is resolved, whether the command blocks waiting on a subprocess or file handle, or whether the build directory triggers a different code path from the default output.
