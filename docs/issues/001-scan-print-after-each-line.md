# 001 - plcc-scan should print tokens and errors after each line

**Type:** feat
**Date:** 2026-05-06

## Description

`plcc-scan` currently buffers all input until EOF (^D) before printing tokens and errors. It should print tokens and errors incrementally after each line of input is entered.

## Steps to Reproduce

1. Run `plcc-scan` interactively (no file argument).
2. Type a line of input and press Enter.
3. Observe: nothing is printed until ^D is entered.

## Notes

The desired behavior is line-by-line output, making the tool useful for interactive exploration. This matches the expectation that a scanner processes input as a stream.
