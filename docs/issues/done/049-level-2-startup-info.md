# 049 - Level-2 commands should print startup info

**Type:** feat
**Date:** 2026-05-29

## Description

When a level-2 command (`plcc-scan`, `plcc-parse`, `plcc-rep`) starts, it should
print:

- The version of plcc
- The path to the grammar file being used

`plcc-rep` should additionally print the name of the tool being run (the language's
REPL entry point).

This gives users immediate confirmation that the right grammar and version are active,
and helps diagnose the class of confusion described in issues 038 and 046.

## Notes

- Output should go to stdout so it appears alongside other user-facing output (see
  issue 039).
- The grammar path should be the resolved absolute or canonical path so there is no
  ambiguity about which file is in use.
- For `plcc-rep`, the tool name is whatever executable the REPL launches (e.g.
  `python3 build/Main.py`), so the user knows what is running.
- Consider whether this output should be suppressible with a `--quiet` / `-q` flag,
  or always printed.
