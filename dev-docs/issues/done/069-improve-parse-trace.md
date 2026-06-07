# 069 - Improve output of plcc-parse --trace

**Type:** feat
**Date:** 2026-06-05

## Description

The output of `plcc-parse --trace` is hard to read. Improve it to make parse tracing more useful for debugging grammars.

## Notes

- Consider indentation to reflect parse depth, rule entry/exit labeling, or token consumption markers.
- Look at what information is most useful when diagnosing parse failures or ambiguities.
