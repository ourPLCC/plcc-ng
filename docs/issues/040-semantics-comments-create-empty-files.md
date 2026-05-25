# 040 - Comment lines in semantics section create empty files in build/Java

**Type:** bug
**Date:** 2026-05-25

## Description

Lines beginning with `#` in the semantics section of a grammar file are intended as comments and should be ignored. Instead, the Java emitter creates empty files in `build/Java/` whose names are derived from the comment text.

For example, a line like:

```
# This is a helper class
```

results in an empty file named something like `# This is a helper class` (or a sanitized variant) being created in `build/Java/`.

## Notes

The semantics section parser either fails to filter comment lines before passing them to the emitter, or the emitter itself does not check for comments before treating a line as a class name / filename. The fix should strip or ignore lines starting with `#` at whichever boundary they are currently passing through.

Worth checking whether the same bug affects the Python emitter.
