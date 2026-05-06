# 004 - plcc-scan should accept '-' as a parameter to read from stdin

**Type:** feat
**Date:** 2026-05-06

## Description

`plcc-scan` does not support `-` as a filename parameter. When `-` appears in the argument list, it should read from standard input until EOF, then continue processing any subsequent file parameters in order.

## Notes

This follows the Unix convention for `-` as stdin. It allows stdin to be interleaved with file arguments, e.g. `plcc-scan file1.txt - file2.txt` reads file1, then stdin, then file2.

`--` should also be supported as an end-of-options marker, so that a file literally named `-` can be passed as `plcc-scan -- -`.
