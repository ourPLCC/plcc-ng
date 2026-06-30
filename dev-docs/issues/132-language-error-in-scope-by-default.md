# 132 - Make `LanguageError` in scope by default in user semantics code

**Type:** feature
**Date:** 2026-06-30

## Description

`LanguageError` should be available in user semantics code without requiring an explicit `import` fragment. Currently, users must manually import it in each class that needs it (e.g. `from runtime.base import LanguageError` in Python, `import runtime.LanguageError;` in Java, `const { LanguageError } = require('./runtime/base');` in JavaScript). This is unnecessary friction for a core mechanism.

## Notes

- Python: auto-inject `from runtime.base import LanguageError` into the generated import section of every class file, or add it to the `_Start.py` base so subclasses inherit it.
- Java: auto-inject `import runtime.LanguageError;` into every generated class file.
- JavaScript: auto-inject `const { LanguageError } = require('./runtime/base');` into every generated class file template.
- Haskell: blocked on issue 131 (moving `LanguageError` to a runtime module first).
- Documentation in issue 127 should be written assuming `LanguageError` is in scope by default once this is implemented.
