# plcc-rep Error Taxonomy Design

**Date:** 2026-06-27
**Issue:** [121](../../../dev-docs/issues/121-rep-python-syntax-error-continues.md)

## Problem

`plcc-rep` is an interactive REPL for testing a defined language. Different errors mean different things — some indicate the user made a mistake in the sentence they typed, others mean the language specification is broken, others are the defined language's own intended behavior. Currently there is no clear taxonomy, and `plcc-rep` mishandles some cases (e.g., Python syntax errors in the semantics cause the REPL to continue rather than exit).

## Error Taxonomy

### Syntax Error

**What it is:** A lexical or syntactic error in a sentence the user typed into the interactive shell — the defined language's scanner or parser rejected the input.

**Who caused it:** The end user of the REPL.

**REPL action:** Print the error, give a fresh prompt, continue. The session is healthy.

**Message:** The existing error output from the scanner/parser. No additional label needed.

---

### Specification Error

**What it is:** A flaw in the language specification itself. Includes:

- Syntax or validation errors in the `.plcc` spec file (detected by `plcc-make` before the session starts)
- Python/Java/JavaScript/Haskell syntax errors in the semantics (detected at import/load time)
- Logic bugs in the semantics implementation that surface at runtime (e.g., popping an empty stack, bad array access)

**Who caused it:** The language author — the person writing the `.plcc` spec.

**REPL action:** Print the error, exit. The session cannot continue because the language itself is broken.

**Message:** `Specification error: <type>: <message>` followed by `Fix the errors in your specification and re-run.`

---

### Implemented Behavior

**What it is:** An error intentionally raised by the defined language's own runtime — type errors, precondition violations, or any other error the language author deliberately coded. This is not really an error in plcc-rep's view; it is the defined language working as designed.

**Who caused it:** The end user of the defined language (they did something the language rejects).

**REPL action:** Print the error as-is, give a fresh prompt, continue. `plcc-rep` is a tool for exercising and testing the defined language's behavior, including its error behavior.

**Message:** `plcc-rep` prints the `message` field of the JSON record, with no prefix added. The language author controls the full text — if they want a prefix like `TypeError:`, they include it in the message. The `type` field is available for verbose/debug output but is not shown by default.

---

### System Error

**What it is:** An internal error in `plcc-rep` or any `plcc-*` tool — a bug in plcc-ng itself, an unexpected crash, malformed output from a subprocess that violates the protocol.

**Who caused it:** The plcc-ng implementation.

**REPL action:** Print the error, exit.

**Message:** `System error: <description>` followed by `Please report this at https://github.com/ourPLCC/plcc-ng/issues.`

---

## JSON Protocol

`plcc-rep` communicates with language runners (`plcc-*-run`) via JSON lines on stdout. The protocol is extended to carry error kind:

| `kind` | Meaning | REPL action |
| --- | --- | --- |
| `result` | Normal evaluation result | Print value (if non-null), continue |
| `error` | Implemented behavior — intentional language error | Print message as-is, continue |
| `specification_error` | Semantics implementation bug caught during evaluation | Print as Specification Error, exit |

The existing `result` and `error` kinds are unchanged. `specification_error` is new.

Fields for `specification_error`:

```json
{"kind": "specification_error", "type": "<ExceptionClassName>", "message": "<str>"}
```

### Startup Failure (Pre-Protocol Path)

If the interpreter process exits before sending any output (e.g., Python syntax error at import time, Java class loading failure), `plcc-rep` detects EOF on the interpreter's stdout before any record arrives. This is also treated as a Specification Error — same message, different detection path.

---

## LanguageError Convention

Each language extension provides a `LanguageError` base class. Language authors raise it (or a subclass) to signal intentional error behavior in their defined language. The runtime distinguishes this from all other exceptions.

### Python

`LanguageError` is defined in `runtime/base.py` and available to language authors via their generated class files.

The runtime loop (`main.py.jinja`) catches:

1. `LanguageError` → emit `{"kind": "error", ...}` → REPL continues
2. Any other `Exception` → emit `{"kind": "specification_error", ...}` → REPL exits

Language authors write:

```python
class TypeErrors(Expr):
    def _run(self):
        raise LanguageError(f"type mismatch: expected int, got {type(self.val)}")
```

### Java

`LanguageError` is an unchecked exception class provided in the generated runtime. Language authors `throw new LanguageError("message")` or extend it.

The runtime loop catches `LanguageError` first, then `Throwable` for everything else.

### JavaScript

`LanguageError` is a class extending `Error` provided in the generated runtime (note: distinct from the built-in `TypeError`, `RangeError`, etc.).

The runtime loop catches `LanguageError` instances, falls through to `specification_error` for all others.

### Haskell

`LanguageError` is a data type implementing the `Exception` typeclass:

```haskell
data LanguageError = LanguageError String deriving (Show)
instance Exception LanguageError
```

The runtime loop uses `catch` with `LanguageError` first, then catches `SomeException` for everything else. Language authors `throw (LanguageError "message")`.

Note: Haskell's built-in `error "string"` throws `ErrorCall`, which is **not** a `LanguageError` and will be treated as a specification error. Language authors must use `throw (LanguageError ...)` for intentional errors. This aligns with Haskell convention: `error` signals a programmer mistake.

---

## plcc-rep Behavior Summary

| Situation | Detection | Action |
| --- | --- | --- |
| Scanner/parser rejects input | `{"kind": "error"}` in tree pipeline | Print error, fresh prompt |
| Language author raises `LanguageError` | `{"kind": "error"}` from runner | Print as-is, fresh prompt |
| Semantics bug during evaluation | `{"kind": "specification_error"}` from runner | Print Specification Error, exit |
| Interpreter dies at startup | EOF before any record | Print Specification Error, exit |
| `plcc-make` fails | Non-zero exit code | Print Specification Error, exit |
| Protocol violation / unexpected state | Malformed or missing output | Print System Error, exit |

---

## Out of Scope

- Changes to how `plcc-make` reports spec file syntax/validation errors (already exits with non-zero; messaging improvements are a separate concern)
- Signal handling (SIGINT/Ctrl+C) — already handled
- Source file mode (non-interactive `SOURCE` arguments) — behavior follows the same taxonomy but exit semantics may differ slightly; left for a follow-up
