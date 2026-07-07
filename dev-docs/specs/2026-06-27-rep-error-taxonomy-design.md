# plcc-rep Error Taxonomy Design

**Date:** 2026-06-27
**Issue:** [121](../issues/done/121-rep-python-syntax-error-continues.md)

## Problem

`plcc-rep` is an interactive REPL for testing a defined language. Different outcomes mean different things — some are the defined language doing exactly what it is supposed to do, others mean the language specification is broken, others are bugs in plcc-ng itself. Currently there is no clear taxonomy, and `plcc-rep` mishandles some cases (e.g., Python syntax errors in the semantics cause the REPL to continue rather than exit).

## Outcome Taxonomy

### Language Behavior

**What it is:** Any output produced by the defined language working as designed. From `plcc-rep`'s perspective this is never an error — it is the result the user is testing. Language behavior manifests in four distinct ways:

**1. Successful result** — the defined language evaluated the input and produced a value. The result is printed and the session continues.

**2. Lexical rejection** — the defined language's scanner did not recognize the input (e.g., an illegal character). The scanner reports the problem; `plcc-rep` gives a fresh prompt and continues. The defined language is healthy.

**3. Syntax rejection** — the defined language's parser found that the input does not match any rule in the grammar. The parser reports the problem; `plcc-rep` gives a fresh prompt and continues. The defined language is healthy.

**4. Semantic rejection** — the defined language's runtime deliberately signals a condition (e.g., a type error, a precondition violation, a "division by zero" that the language author chose to handle explicitly). The language author raises a `LanguageError` (see below); `plcc-rep` prints the message and gives a fresh prompt. The defined language is healthy.

In all four cases `plcc-rep` continues. No label is added by `plcc-rep` — the output is whatever the defined language produced. For semantic rejections the `message` field of the JSON record is printed as-is; the language author controls the full text. The `type` field is available for verbose/debug output but is not shown by default.

---

### Specification Error

**What it is:** A flaw in the language specification itself. The spec is broken and the session cannot meaningfully continue. Includes:

- Syntax or validation errors in the `.plcc` spec file (detected by `plcc-make` before the session starts)
- Python/Java/JavaScript/Haskell syntax or import errors in the generated semantics code (detected at load time)
- Logic bugs in the semantics implementation that surface at runtime (e.g., popping an empty stack, a bad array index — any uncaught exception that is not a deliberate `LanguageError`)

**Who caused it:** The language author — the person writing the `.plcc` spec.

**REPL action:** Print the error, exit.

**Message:** `Specification error: <type>: <message>` followed by `Fix the errors in your specification and re-run.`

---

### plcc-ng Error

**What it is:** An internal error in `plcc-rep` or any `plcc-*` tool — a bug in plcc-ng itself, an unexpected crash, or malformed output from a subprocess that violates the protocol.

**Who caused it:** The plcc-ng implementation.

**REPL action:** Print the error, exit.

**Message:** `plcc-ng error: <description>` followed by `Please report this at https://github.com/ourPLCC/plcc-ng/issues.`

---

## JSON Protocol

`plcc-rep` communicates with language runners (`plcc-*-run`) via JSON lines on stdout. The protocol is extended to carry outcome kind:

| `kind` | Meaning | REPL action |
| --- | --- | --- |
| `result` | Successful result | Print value (if non-null), continue |
| `error` | Semantic rejection — deliberate `LanguageError` | Print message as-is, continue |
| `specification_error` | Semantics bug caught during evaluation | Print as Specification Error, exit |

The existing `result` and `error` kinds are unchanged. `specification_error` is new.

Fields for `specification_error`:

```json
{"kind": "specification_error", "type": "<ExceptionClassName>", "message": "<str>"}
```

Lexical and syntax rejections do not pass through the language runner — they are reported by the scanner/parser pipeline inside `plcc-rep` and handled the same way (continue).

### Startup Failure (Pre-Protocol Path)

If the interpreter process exits before sending any output (e.g., Python syntax error at import time, Java class loading failure), `plcc-rep` detects EOF on the interpreter's stdout before any record arrives. This is treated as a Specification Error — same message, different detection path.

---

## LanguageError Convention

Each language extension provides a `LanguageError` base class. Language authors raise it (or a subclass) to signal deliberate semantic rejections. The runtime loop distinguishes `LanguageError` from all other exceptions so that bugs in the semantics implementation are not silently swallowed.

### Python

`LanguageError` is defined in `runtime/base.py` and available to language authors via their generated class files.

The runtime loop (`main.py.jinja`) catches:

1. `LanguageError` → emit `{"kind": "error", ...}` → REPL continues
2. Any other `Exception` → emit `{"kind": "specification_error", ...}` → REPL exits

Language authors write:

```python
class TypeCheck(Expr):
    def _run(self):
        raise LanguageError(f"type mismatch: expected int, got {type(self.val)}")
```

### Java

`LanguageError` is an unchecked exception class provided in the generated runtime. Language authors `throw new LanguageError("message")` or extend it.

The runtime loop catches `LanguageError` first, then `Throwable` for everything else.

### JavaScript

`LanguageError` is a class extending `Error` provided in the generated runtime (distinct from the built-in `TypeError`, `RangeError`, etc.).

The runtime loop catches `LanguageError` instances and falls through to `specification_error` for all others.

### Haskell

`LanguageError` is a data type implementing the `Exception` typeclass:

```haskell
data LanguageError = LanguageError String deriving (Show)
instance Exception LanguageError
```

The runtime loop uses `catch` with `LanguageError` first, then catches `SomeException` for everything else. Language authors `throw (LanguageError "message")`.

Note: Haskell's built-in `error "string"` throws `ErrorCall`, which is **not** a `LanguageError` and is treated as a specification error. This is intentional — `error` in Haskell signals a programmer mistake, not deliberate language behavior.

---

## plcc-rep Behavior Summary

| Situation | Detection | Action |
| --- | --- | --- |
| Successful evaluation | `{"kind": "result"}` from runner | Print value, continue |
| Lexical rejection | `{"kind": "error"}` from scanner pipeline | Print, continue |
| Syntax rejection | `{"kind": "error"}` from parser pipeline | Print, continue |
| Semantic rejection (`LanguageError`) | `{"kind": "error"}` from runner | Print message, continue |
| Semantics bug during evaluation | `{"kind": "specification_error"}` from runner | Print Specification Error, exit |
| Interpreter dies at startup | EOF before any record | Print Specification Error, exit |
| `plcc-make` fails | Non-zero exit code | Print Specification Error, exit |
| Protocol violation / unexpected state | Malformed or missing output | Print plcc-ng Error, exit |

---

## Out of Scope

- Changes to how `plcc-make` reports spec file syntax/validation errors (already exits with non-zero; messaging improvements are a separate concern)
- Signal handling (SIGINT/Ctrl+C) — already handled
- Source file mode (non-interactive `SOURCE` arguments) — behavior follows the same taxonomy but exit semantics may differ slightly; left for a follow-up
