# 111 - Redesign the Mermaid diagram extension

**Type:** feat
**Date:** 2026-06-24

## Description

The Mermaid diagram extension emits a `.mmd` file and has a `run` command that attempts to open or render it. The `run` command does not work even with Node.js installed, so users who choose `--format=mermaid` get a source file they cannot easily view.

VS Code renders Mermaid diagrams embedded in Markdown when the file is previewed. This may be a better fit than trying to invoke a standalone Mermaid CLI renderer.

## Notes

- **Proposed approach**: Change the Mermaid extension so that:
  1. `plcc-mermaid-diagram-emit` produces a Markdown file (`.md`) with the diagram wrapped in a ` ```mermaid ` fenced code block instead of a bare `.mmd` file.
  2. `plcc-mermaid-diagram-run` prints the path to the generated Markdown file and tells the user to open and preview it in VS Code (e.g., with Ctrl+Shift+V / Cmd+Shift+V).
- This removes the broken Node/CLI dependency entirely and gives users a working, zero-install experience in the most common dev environment.
- The `build` step (`.mmd` → `.png`) may still be worth keeping for headless/CI use, but `run` should be the VS Code preview path.
- Check whether any bats tests rely on the `.mmd` output filename or the current `run` behavior; those will need updating.
