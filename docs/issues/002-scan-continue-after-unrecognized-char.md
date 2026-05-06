# 002 - plcc-scan should continue processing after an unrecognized character

**Type:** fix
**Date:** 2026-05-06

## Description

When `plcc-scan` encounters an unrecognized character, it prints an error and exits immediately. It should instead print all tokens recognized before the error, print the error, and then continue scanning the remaining input until EOF.

## Steps to Reproduce

1. Run `plcc-scan` with input that contains an unrecognized character followed by valid tokens.
2. Observe: only the error is printed; any tokens before the bad character and all input after it are silently dropped.

## Notes

Continuing past errors makes the tool more useful for diagnosing input — a single bad character should not suppress all subsequent output.
