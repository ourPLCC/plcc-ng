# plcc-rep Protocol, `specification_error`, and `LanguageError` Documentation Design

**Date:** 2026-06-30
**Issue:** [127](../issues/done/127-docs-rep-protocol-language-error.md)

## Problem

`plcc-rep` gained a startup handshake (ready signal) and structured `specification_error` handling, and each language runtime gained a `LanguageError` mechanism. None of this is documented. Users who encounter "Specification error" output don't know what it means or how to distinguish it from deliberate language behavior. Users who need to signal errors from semantics code have no discoverable path to `LanguageError`.

## Design

Four files are touched: `docs/cli/commands/plcc-rep.md`, `docs/language-guide/semantic.md`, and four per-language pages.

---

### 1. `docs/cli/commands/plcc-rep.md` — "Startup and errors" section

Add a new section after "Interactive mode". Written as user-facing prose — no JSONL record names exposed.

**Content:**

> **Startup and errors**
>
> When `plcc-rep` starts, it builds your spec and launches an interpreter subprocess. If the interpreter fails to start — for example, because your semantics code has a syntax error that prevents it from loading — you will see:
>
> ```text
> Specification error: interpreter failed to start.
> Fix the errors in your specification and re-run.
> ```
>
> During a session, `plcc-rep` distinguishes between two categories:
>
> **Language behavior** — the defined language working as designed. `plcc-rep` reports the outcome and gives you a fresh prompt:
>
> - The scanner did not recognize the input (lexical error).
> - The parser found input that does not match any rule (syntax error).
> - Your semantics code raised a `LanguageError` (semantic rejection — e.g., a type error or division by zero your language author chose to handle explicitly).
>
> **Specification errors** — a flaw in the language specification itself. Your semantics code threw an unexpected exception (not a `LanguageError`). `plcc-rep` prints the error type and message, then exits. Fix the problem in your spec and re-run.
>
> See your language's page for how to raise a `LanguageError` from semantics code.

---

### 2. `docs/language-guide/semantic.md` — "Signaling errors from semantics" section

Add after the `_run` entry point section.

**Content:**

> **Signaling errors from semantics**
>
> When your semantics code needs to report a deliberate error — a type mismatch, a precondition violation, or any condition your language treats as an error — raise a `LanguageError`. `plcc-rep` prints the message and gives a fresh prompt; the session continues.
>
> Raising any other exception is treated as a bug in your specification. `plcc-rep` prints a Specification Error and exits.
>
> Each language provides `LanguageError` as part of its generated runtime. See your language's page for the exact syntax.

---

### 3. Per-language pages — `LanguageError` section

Add a `LanguageError` section to each of the four language pages. `LanguageError` is in scope by default in all generated classes (no import fragment required — tracked in issue 132).

**Note on "in scope by default":** The content below documents the *intended* behavior — `LanguageError` available without an explicit import. The current implementation requires an import fragment in each class. Issue 132 tracks making this automatic. Since the project has not yet released, the docs are written for the intended state; they will be correct when issue 132 lands.

#### Python (`docs/language-guide/languages/python.md`)

Add after the `_run` entry point section.

````markdown
## `LanguageError`

Raise `LanguageError` to signal a deliberate error in the defined language — a type
mismatch, division by zero, or any condition your language treats as an error. `plcc-rep`
prints the message and gives a fresh prompt; the session continues.

`LanguageError` is available in all generated classes without any import:

```python
def eval(self):
    raise LanguageError("type mismatch: expected int")
```

Subclass it to create named error types:

```python
class TypeError(LanguageError): pass
raise TypeError("expected int")
```

Any other exception (not `LanguageError` or a subclass) is treated as a specification
error — `plcc-rep` prints the error and exits.
````

#### Java (`docs/language-guide/languages/java.md`)

Add after the `_run` entry point section.

````markdown
## `LanguageError`

Throw `LanguageError` to signal a deliberate error in the defined language — a type
mismatch, division by zero, or any condition your language treats as an error. `plcc-rep`
prints the message and gives a fresh prompt; the session continues.

`LanguageError` is available in all generated classes without any import:

```java
public int eval() {
    throw new LanguageError("type mismatch: expected int");
}
```

Subclass it to create named error types:

```java
public class TypeError extends LanguageError {
    public TypeError(String msg) { super(msg); }
}
throw new TypeError("expected int");
```

Any other exception (not `LanguageError` or a subclass) is treated as a specification
error — `plcc-rep` prints the error and exits.
````

#### JavaScript (`docs/language-guide/languages/javascript.md`)

Add after the `_run` entry point section.

````markdown
## `LanguageError`

Throw `LanguageError` to signal a deliberate error in the defined language — a type
mismatch, division by zero, or any condition your language treats as an error. `plcc-rep`
prints the message and gives a fresh prompt; the session continues.

`LanguageError` is available in all generated classes without any import:

```javascript
eval() {
    throw new LanguageError("type mismatch: expected int");
}
```

Subclass it to create named error types:

```javascript
class TypeError extends LanguageError {}
throw new TypeError("expected int");
```

Any other exception (not `LanguageError` or a subclass) is treated as a specification
error — `plcc-rep` prints the error and exits.
````

#### Haskell (`docs/language-guide/languages/haskell.md`)

Add after the `_run` entry point section. Note the current limitation.

````markdown
## `LanguageError`

`LanguageError` is the intended mechanism for signaling a deliberate error in the defined
language from Haskell semantics code. When thrown, `plcc-rep` prints the message and gives
a fresh prompt; the session continues.

`LanguageError` is currently not accessible from user-authored module files — it is defined
in the generated `Main.hs`, which user modules cannot import. Support for throwing
`LanguageError` from semantics code is tracked in issues 131 and 132.

In the meantime, note that Haskell's built-in `error "message"` throws `ErrorCall`, which
is treated as a **specification error** (not a language error) — `plcc-rep` will exit.
````

---

## Out of Scope

- Changing the JSONL protocol or record shapes.
- Implementing issue 131 (move `LanguageError` to a Haskell runtime module).
- Implementing issue 132 (auto-inject `LanguageError` into all generated class files).
- The `--verbose-format=json` output format — that is already documented separately.
