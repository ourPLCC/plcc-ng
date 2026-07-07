# Design: Make `LanguageError` In Scope by Default

**Date:** 2026-07-01
**Issue:** 132
**Status:** Approved

## Problem

Users writing semantics code must manually import `LanguageError` in each class that needs it:

- Python: `from runtime.base import LanguageError`
- Java: `import runtime.LanguageError;`
- JavaScript: `const { LanguageError } = require('./runtime/base');`

This is unnecessary friction for a core mechanism that nearly every language implementation will use.

## Scope

Python, Java, and JavaScript emitters only. Haskell is blocked on issue 131 (moving `LanguageError` into a runtime module first).

## Approach: Static line in each Jinja template

Add one import line directly to each language's `class_file.*.jinja` template. Every generated class file will unconditionally include the import. No emitter Python code changes needed.

This approach was chosen over:
- **Emitter-side variable injection** — adds indirection with no current benefit
- **Re-export through existing runtime alias** — non-obvious (`_plcc.LanguageError`) and inconsistent across languages

## Changes

### Python

**File:** `src/plcc/lang/ext/python/templates/class_file.py.jinja`

Add `from runtime.base import LanguageError` immediately after the existing `import runtime.base as _plcc` line.

```
import runtime.base as _plcc
from runtime.base import LanguageError   ← add this
```

### Java

**File:** `src/plcc/lang/ext/java/templates/class_file.java.jinja`

Add `import runtime.LanguageError;` after the existing `import runtime.Token;` line.

```
import runtime.Token;
import runtime.LanguageError;   ← add this
```

### JavaScript

**File:** `src/plcc/lang/ext/javascript/templates/class_file.js.jinja`

Expand the existing destructuring require to include `LanguageError`.

```js
const { Node, Token, LanguageError } = require('./runtime/base');   // was { Node, Token }
```

## What Does Not Change

- `_Start.py`, `_Start.java`, `_Start.js` — handwritten scaffold files outside the class template
- Runtime files (`runtime/base.py`, `runtime/LanguageError.java`, `runtime/base.js`) — already define `LanguageError` correctly
- Haskell emitter — no change; blocked on issue 131

## Testing

Each emitter has an `emit_test.py`. Add one test per language asserting that a generated class file contains the expected import line. Use the minimal model fixture already present in each test file — no special fragments needed.

| Language | Test assertion |
|---|---|
| Python | Generated `<ClassName>.py` contains `from runtime.base import LanguageError` |
| Java | Generated `<ClassName>.java` contains `import runtime.LanguageError;` |
| JavaScript | Generated `<ClassName>.js` contains `LanguageError` in the `require('./runtime/base')` destructure |

No bats command tests need updating (none currently reference `LanguageError`).
