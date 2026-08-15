# 191 - Interpreter resource exhaustion is reported as a specification error

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

When a program recurses deeply enough to exhaust the target runtime's
call stack, plcc-rep reports it as a `Specification error` and advises
the user to fix their specification:

```
Specification error: RecursionError: maximum recursion depth exceeded
Fix the errors in your specification and re-run.
```

Nothing about the specification is wrong, and nothing about the program
is wrong either in the sense that word usually carries — the program
asked for more stack than the host runtime allows. That is a resource
limit of the interpreter, a third category the protocol has no way to
express. It is currently indistinguishable from a genuine specification
defect, which is what the label and the advice both claim it is.

The ceilings are low enough to reach by accident and they differ sharply
by target, so the same program is fine on two targets and "a
specification error" on the third. Measured downstream on a language with
`letrec`, at direct language-level recursion depth N:

| target | deepest N that worked | first N that failed | reported as |
|---|---|---|---|
| Python | 329 | 330 | `RecursionError: maximum recursion depth exceeded` |
| Java | 2700 | 2800 | `StackOverflowError:` |
| JavaScript | 2800 | 2900 | `RangeError: Maximum call stack size exceeded` |

Python's is roughly an order of magnitude lower than the other two,
because each language-level call costs several interpreter frames (one
for `eval`, one for the closure's `apply`, one or more for primitive
dispatch). CPython's own 1000-frame default therefore buys about 330
levels of the *implemented* language.

Note also the empty message on Java, which renders with a dangling
separator: `Specification error: StackOverflowError: `.

## Steps to Reproduce

Self-contained. Save as `spec.plcc`:

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
    return str(self._depth(int(self.num.lexeme)))

def _depth(self, n):
    if n == 0:
        return 0
    return 1 + self._depth(n - 1)
%%%
```

```
$ printf '1\n100000\n2\n' | plcc-rep -s spec.plcc
1
Specification error: RecursionError: maximum recursion depth exceeded
Fix the errors in your specification and re-run.
$ echo $?
1
```

The trailing `2` is never evaluated — the session ends. The same input on
the Java and JavaScript targets, with the equivalent `depth` method,
gives `StackOverflowError:` and `RangeError: Maximum call stack size
exceeded` respectively, both also exit 1.

Measured on plcc-ng 2.0.2.

## Notes

**Why this is filed separately from
[#190](190-rep-kills-session-on-program-errors.md).** Both symptoms
arrive through the same branch — the non-`LanguageError` path in each
target's main template, dispatched by `_render_record` in
[`cmd/rep.py`](../../src/plcc/cmd/rep.py) — so #190's fix would
incidentally change this message too. But the right remedy may differ.
For #190, continuing the session is clearly correct. Here it is a real
question: after a stack overflow the Python interpreter is close to its
limit and further evaluation may be unreliable, so ending the session may
be the honest response. What is wrong in every case is calling it a
specification error and telling the user to edit their grammar.

**Suggested direction** (the reporter has no stake in which is chosen):

- A distinct record kind or label for interpreter-resource exhaustion,
  recognizing `RecursionError`, `StackOverflowError`, and `RangeError`
  with a "Maximum call stack" message. The wording should say the program
  recursed too deeply for the target runtime, not that the specification
  is broken.
- Optionally, raise the generated Python interpreter's recursion limit
  (`sys.setrecursionlimit`) so that the three targets' ceilings are closer
  together. That narrows the divergence but does not remove the category,
  so it does not substitute for the above.
- If nothing else, drop the "Fix the errors in your specification and
  re-run" line for this case, and fix the dangling `: ` when the
  exception carries no message.

**Reported from downstream.** Found while porting a course language suite
to plcc-ng; the depth measurements above are that port's, taken across
its three targets on identical source. Its local issue
`ourPLCC/languages-ng 019-python-recursion-ceiling.md` keeps the other
half of the problem — documenting the ceiling so course material stays
inside it — which is downstream's own work. The reproduction above was
rebuilt from scratch against plcc-ng alone.
