# 053 - Render ll1.json in human-readable format

**Type:** feat
**Date:** 2026-06-01

## Description

Add a command that renders `ll1.json` in a human-readable format — likely a Markdown file using tables. The output should also include explanations of how to interpret each structure in the file (e.g. the parse table, FIRST/FOLLOW sets, or whatever top-level keys are present).

## Notes

- Markdown with tables is a likely output format, but consider whether plain text or HTML might also be useful.
- Each section of `ll1.json` should be accompanied by a short explanation of what it represents and how to read it.
- This would help users understand and debug their grammars without having to read raw JSON.
