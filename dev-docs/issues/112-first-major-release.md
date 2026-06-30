# 112 - Prepare for first major release (v1.0.0)

**Type:** feat
**Date:** 2026-06-24

## Description

plcc-ng is currently at v0.52.0. The project has working emitters (Python, Java, Haskell, JavaScript), a REPL, diagram generation, a docs site, and a growing test suite. It is time to define what "done enough for v1.0" means and work toward it.

A v1.0 release signals stability to users: the CLI interface and spec syntax are committed to, breaking changes will be deliberate and versioned, and the tool is ready for classroom and production use.

## Notes

- Define the v1.0 criteria — what must be true before cutting a 1.0? Candidates:
  - No known correctness bugs in the core pipeline (scan → parse → emit)
  - Stable CLI surface (command names, flags, output formats) that we are willing to maintain
  - Stable spec syntax — no planned breaking changes to `.plcc` file format
  - End-user documentation covers the full workflow (install, quickstart, language guide, CLI reference)
  - Release SOP (`dev-docs/release-sop.md`) is complete and tested
  - CI is green and the test suite covers the happy path end-to-end for at least Python and Java
- All four emitters (Python, Java, Haskell, JavaScript) are v1 supported — no experimental tier
- Write up the v1.0 milestone in the roadmap once criteria are agreed
- The release SOP (`dev-docs/release-sop.md`) currently has no content — that needs to be written as part of this effort
