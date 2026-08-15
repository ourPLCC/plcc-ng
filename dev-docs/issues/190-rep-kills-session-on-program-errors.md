# 190 - A program error kills the plcc-rep session and blames the specification

**Type:** fix
**Date:** 2026-08-15

<!--
Classify by user-facing impact, not by whether something was "broken".
`fix` and `feat` bump the release version (see [tool.semantic_release]
in pyproject.toml); reserve them for changes to the shipped package
(src/). A bug in a test, script, or CI workflow (bin/, tests/,
.github/) is still a bug, but it's not user-facing — classify it
`test` or `chore` instead so it doesn't spin the version. `docs` is for
documentation content, and never bumps the version either way.
-->

## Description

Every exception a semantic action raises that is not a `LanguageError` is
reported as a `specification_error`, which terminates the interpreter and
then `plcc-rep` itself. Two things go wrong at once: a session that should
survive one bad input does not, and the user is told to fix a
specification that is not at fault.

A language implementer can only choose between two behaviors today:

| what the semantic action raises | record kind | session | exit |
|---|---|---|---|
| `LanguageError` | `error` | continues | 0 |
| anything else | `specification_error` | **dies** | **1** |

There is no third option, so any exception the implementer did not
anticipate and convert takes the whole session down. That is the wrong
default: the overwhelmingly common cause is the *input program*, not the
specification. A student typing an out-of-range argument to a primitive
gets their REPL killed and is advised to go edit the grammar.

The message is also actively misleading. `plcc-rep` prints:

```
Specification error: ValueError: chr() arg not in range(0x110000)
Fix the errors in your specification and re-run.
```

The specification is fine. The input was `-5`.

This is not target-specific — all four language extensions emit the same
record, and the two sites are:

- the generated interpreter, which emits `specification_error` and exits:
  [`python/templates/main.py.jinja`](../../src/plcc/lang/ext/python/templates/main.py.jinja)
  (`except Exception` → `sys.exit(1)`),
  [`java/templates/Main.java.jinja`](../../src/plcc/lang/ext/java/templates/Main.java.jinja)
  (both the non-`LanguageError` `InvocationTargetException` cause and the
  outer `catch (Exception e)` → `System.exit(1)`),
  [`javascript/templates/main.js.jinja`](../../src/plcc/lang/ext/javascript/templates/main.js.jinja)
  (`else` branch → `process.exit(1)`), and
  [`haskell/emit.py`](../../src/plcc/lang/ext/haskell/emit.py).
- [`cmd/rep.py`](../../src/plcc/cmd/rep.py), whose `_render_record`
  `specification_error` branch prints the label and the "fix your
  specification" advice, then calls `sys.exit(1)`.

## Steps to Reproduce

Self-contained — no external specification needed. Save as `spec.plcc`:

```
token NUM '-?\d+'
skip WS '\s+'
%
<Program> ::= <NUM:num>
%
Python
Program
%%%
def _run(self):
    n = int(self.num.lexeme)
    if n == 999:
        raise LanguageError("deliberate language error")
    if n < 0:
        return chr(n)
    return str(n)
%%%
```

1. **A `LanguageError` behaves correctly** — the session survives and the
   remaining input is still evaluated:

   ```
   $ printf '1\n999\n2\n' | plcc-rep -s spec.plcc
   1
   deliberate language error
   2
   $ echo $?
   0
   ```

2. **Any other exception ends the session** — `2` is never evaluated:

   ```
   $ printf '1\n-5\n2\n' | plcc-rep -s spec.plcc
   1
   Specification error: ValueError: chr() arg not in range(0x110000)
   Fix the errors in your specification and re-run.
   $ echo $?
   1
   ```

Measured on plcc-ng 2.0.2.

The same input reproduces on the other targets, with each one's native
exception type — the classification, not the exception, is what they share:

| target | semantic action | reported as |
|---|---|---|
| Python | `chr(-5)` | `Specification error: ValueError: chr() arg not in range(0x110000)` |
| JavaScript | `String.fromCodePoint(-5)` | `Specification error: RangeError: Invalid code point -5` |
| Java | `Character.toChars(-5)` | `Specification error: IllegalArgumentException: Not a valid Unicode code point: 0xFFFFFFFB` |

All three exit 1 and drop the rest of the session.

## Notes

**Why it matters.** `plcc-rep` is what students interact with, and a
language built on plcc-ng is mostly *primitives written in the target
language*. Every one of those is a place where a bad argument raises a
native exception rather than a `LanguageError`. Making the specification
author defensively wrap each such call is a lot of ceremony to buy back a
default that could be correct on its own; missing one anywhere is a
session-killing crash with misdirected advice.

**Suggested direction** (the reporter has no stake in which is chosen):

- Treat a non-`LanguageError` exception from a semantic action as a
  runtime error of the program: emit `error` (or a new record kind such
  as `runtime_error`) and let the session continue, reserving
  `specification_error` for failures during load/deserialization, where
  the specification genuinely is the suspect. This changes the
  `except Exception` branch in each target's main template and drops the
  process exit.
- If the session must still end, at least separate the label from the
  advice, so "Fix the errors in your specification and re-run" is printed
  only for load-time failures.

Whichever is chosen, the two sites move together: the record kind emitted
by the four main templates, and `_render_record`'s dispatch in `rep.py`.

**Related.** [#187](187-rep-lacks-output-and-clean-exit-records.md) is
also about missing record kinds in this protocol and touches the same
`_render_record` dispatch, but is independent of this one — it adds
channels for output and clean exit, and leaves the `specification_error`
branch as it is. [#127](done/127-docs-rep-protocol-language-error.md),
[#131](done/131-haskell-language-error-not-accessible-from-user-code.md),
and [#132](done/132-language-error-in-scope-by-default.md) made
`LanguageError` available and documented; none of them considered what
happens when something else escapes.

**Reported from downstream.** Found while porting a course language suite
to plcc-ng, and split out of that repo's local issue
`ourPLCC/languages-ng 039-putc-puts-diverge-across-targets.md`, whose
other half (target-dependent character-code truncation in the port's own
specification) is a downstream defect and stays there. The reproduction
above was rebuilt from scratch against plcc-ng alone.

Filed alongside
[#191](191-rep-reports-resource-exhaustion-as-specification-error.md),
which reaches this same branch from a different cause and may or may not
want the same remedy.
