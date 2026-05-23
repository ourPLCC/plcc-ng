# 033 - plcc-rep should use SubmitOn.EOF (Enter accumulates, ^D submits)

**Type:** feat
**Date:** 2026-05-23

## Description

`plcc-rep` currently uses `SubmitOn.EOL`, which evaluates after each Enter press (using EOF-error suppression in `TreePipeline` to show `...` when input is incomplete). Now that `SubmitOn.EOF` mode has been changed to pure accumulation (Enter always accumulates, `^D` submits), switching `plcc-rep` to `SubmitOn.EOF` would give it consistent `^D`-to-submit semantics matching `plcc-parse`.

The EOL-mode REPL evaluation mechanism (TreePipeline returning `False` on incomplete parse with `eof=False` to suppress errors and show continuation) would no longer be needed for `plcc-rep` under this model.

## Notes

- The switch is a one-line change in `src/plcc/cmd/rep.py`.
- Requires careful brainstorming: the UX implications for multi-expression grammars (where a single Enter after a complete expression should produce a result in EOL mode, but requires `^D` in EOF mode) need deliberate design.
- The EOF-error suppression path in `TreePipeline` (`eof=False` returning `False`) may become dead code for `plcc-rep` but remains correct for `plcc-parse` continuation detection.
- Tests in `src/plcc/cmd/rep_test.py` will need review.
