# Design: Issues 162, 165 — A Single, Strict `_run()` Contract

**Date:** 2026-07-23
**Issues:** 162, 165
**Type:** fix, docs

---

## Overview

`_run()` is the entry point `plcc-rep` calls on the root node of each parsed
tree. It exists to replace original PLCC's `$run()`, which was `void` and
printed directly — moving I/O responsibility out of semantics code and into
the runtime, so `plcc-rep --format json` can show a real record for every
result instead of raw text.

That redesign turned out to be incomplete and inconsistently applied:

- **Python** (#162): the runtime driver converts the return value with
  `repr()` instead of `str()`, so returning `"hello"` prints `'hello'`.
- **Python, JavaScript, Java** (#165): the *default* `_run()` (used whenever
  a spec doesn't override it) still prints directly and returns nothing —
  the exact `$run()` pattern the redesign was meant to replace. This
  silently breaks `plcc-rep --format json` for any spec that relies on the
  default, not just ones with custom Java code.
- **Java** (#165): the *documented, user-facing* contract is also still
  `void` + direct `System.out.println` — a fundamentally different model
  from the other three languages' return-and-convert approach.
- The contract itself is undocumented as a rule for anyone overriding
  `_run()`, and the migration guide only documents `$run()` → `_run()` as a
  rename, not a behavior change.

This spec resolves all of it as one change: **`_run()` returns a string,
period.** No `None`/`null`/`undefined`/`Nothing` suppression escape hatch —
that feature has no real use case in this repo today (grep confirms zero
existing examples or tests exercise it), and Haskell's
`_run :: StartModule -> String` signature has no way to express it honestly
anyway. An empty string is a valid, meaningful result, not a special case.
This also finally resolves #162 as a side effect: with the contract this
strict, the runtime uses the returned string as-is — no `repr()`, no `str()`
conversion step to get wrong.

---

## The Contract

> `_run()` is called on the root node of each parsed tree. **It must return
> a string.** The runtime driver marshals that string into a
> `{"kind": "result", "value": "<string>"}` JSON record and sends it to
> `plcc-rep`, which prints it. `_run()` must never write to stdout itself —
> doing so bypasses the JSON envelope, and while plain-text mode will still
> show the output, `plcc-rep --format json` will not.
>
> If `_run()` returns anything other than a string, the runtime raises a
> `specification_error` (same category as an unimplemented custom entry
> point, per issue #031) rather than silently printing something wrong.

Per language:

| Language | Signature | Enforcement |
|---|---|---|
| Haskell | `_run :: StartModule -> String` | Compiler (already true today) |
| Java | `public String _run()` | Compiler for return statement shape; runtime null-check for the value |
| Python | `def _run(self)` returning `str` | Runtime `isinstance` check |
| JavaScript | `_run()` returning `string` | Runtime `typeof` check |

Java's signature change (`void` → `String`) is a **breaking change** — see
Versioning below. So is strict validation for Python and JavaScript: any
spec whose `_run()` currently returns a non-string (an `int`, a `list`, any
object relying on implicit stringification — exactly what this repo's own
`arith.plcc` fixture does today) will start failing with a
`specification_error` instead of silently working. Only the *default*
`_run()` fix is a pure bug fix with zero behavior change in plain-text mode
for every language — no default anywhere returns a non-string, so the only
visible difference there is `--format json` starting to work correctly.

---

## Code Changes

### Python — `src/plcc/lang/ext/python/`

`emit.py`, default `_Start._run()`:
```python
# before
def _run(self):
    print(str(self))

# after
def _run(self):
    return str(self)
```

`templates/main.py.jinja`, result handling:
```python
# before
result = tree.{{ entry_point }}()
print(json.dumps({"kind": "result", "value": repr(result) if result is not None else None}), flush=True)

# after
result = tree.{{ entry_point }}()
if not isinstance(result, str):
    raise TypeError(f"{{ entry_point }}() must return a string, got {type(result).__name__}")
print(json.dumps({"kind": "result", "value": result}), flush=True)
```
The `TypeError` is uncaught by the existing `except LanguageError` clause and
falls through to the existing generic `except Exception as e`, which already
produces a `specification_error` record — no new exception-handling path
needed.

### JavaScript — `src/plcc/lang/ext/javascript/`

`emit.py`, default `_Start._run()`:
```js
// before
_run() {
    console.log(String(this));
}

// after
_run() {
    return String(this);
}
```

`templates/main.js.jinja`, result handling:
```js
// before
const result = tree.{{ entry_point }}();
console.log(JSON.stringify({ kind: 'result', value: result != null ? String(result) : null }));

// after
const result = tree.{{ entry_point }}();
if (typeof result !== 'string') {
    throw new Error(`{{ entry_point }}() must return a string, got ${typeof result}`);
}
console.log(JSON.stringify({ kind: 'result', value: result }));
```
The thrown `Error` is not a `LanguageError`, so it falls into the existing
`else` branch that already produces `specification_error`.

### Java — `src/plcc/lang/ext/java/`

`emit.py`, `_START_JAVA`:
```java
// before
public abstract class _Start extends runtime.Node {
    public void _run() {
        System.out.println(this.toString());
    }
}

// after
public abstract class _Start extends runtime.Node {
    public String _run() {
        return this.toString();
    }
}
```

`templates/Main.java.jinja`, result handling:
```java
// before
Object result = m.invoke(root);
JSONObject record = new JSONObject();
record.put("kind", "result");
record.put("value", result != null ? result.toString() : JSONObject.NULL);

// after
Object result = m.invoke(root);
if (result == null) {
    throw new IllegalStateException("{{ entry_point }}() must return a string, got null");
}
JSONObject record = new JSONObject();
record.put("kind", "result");
record.put("value", result.toString());
```
`IllegalStateException` is a `RuntimeException`, caught by the existing
generic `catch (Exception e)` block, which already produces
`specification_error` and exits 1.

### Haskell

No code change. `_run :: StartModule -> String` already can't return
anything but a `String`; the compiler is the validator. The default
`_run = show` already returns rather than prints.

---

## Documentation Changes

- **`docs/language-guide/languages/{python,javascript,java}.md`**: replace
  "the return value is converted to a string" with the strict contract —
  `_run()` must return a string; printing directly bypasses the JSON
  envelope and breaks `--format json`; a non-string return is a
  `specification_error`. Java's code example changes from
  `void`+`System.out.println` to `String`+`return`.
- **`docs/language-guide/languages/haskell.md`**: light wording pass so its
  phrasing matches the other three (no semantic change — it's already
  compliant).
- **`docs/quick-start.md`**: update the Java example (currently
  `void _run() { System.out.println(sum); }`).
- **`docs/cli/guide/language-extensions.md`**: add a short section stating
  the `_run()` protocol as an obligation on any language extension —
  existing or future — return-only, validate non-string returns, raise
  `specification_error`. This is the natural home for the obligation, since
  it's the closest thing this repo has to a language-extension contract
  doc.
- **`docs/migration.md`**:
  - Add an entry to "Breaking behavior changes" (top section) covering all
    three: Java's `_run()` changed from `void` to `String`; Python and
    JavaScript's `_run()` must now return an actual string/`str` (a
    non-string return that used to be silently coerced is now a
    `specification_error`); the old `$run()` void/print model does not
    carry over to any language under `_run()`.
  - Update §9 ("Rename the entry point method") to note the contract
    change, not just the name change.

---

## Testing Changes

Several existing fixtures return non-strings today, relying on the
conversion this change removes:

- `tests/fixtures/arith.plcc:14-15` — `return self.expr.eval()` → `int`
- `tests/fixtures/trivial-python.plcc:9-10` — `return int(self.num.lexeme)` → `int`
- `tests/fixtures/trivial-arbno.plcc:14-15` — `return [e.eval() for e in ...]` → `list`
- `tests/fixtures/trivial-java.plcc:9-11` — `void` + `System.out.println` (old style, not just the default)

All four need their `_run()` bodies updated to return an explicit string.
`tests/fixtures/bad-delimiters.plcc`'s `void _run(){}` needs no change — it
is only ever built `--through=model` in `bad_block_delimiters.bats` and
never emitted or run.

Also:

- `src/plcc/lang/ext/java/emit_test.py:58-62`
  (`test_start_java_uses_underscore_run`) — update to assert
  `'public String _run()'`.
- `tests/bats/integration/java-emit.bats:42` — rename
  `"run outputs token lexeme from void _run()"` (assertion itself still
  holds — `"99"` still appears, now via the JSON envelope instead of a raw
  println).
- `src/plcc/lang/ext/{python,javascript}/emit_test.py` — audit for any
  other inline `_run` body fixtures returning non-strings; update as found.
- New unit tests: default `_run()` returns rather than prints, for Python
  and JavaScript (Java already has a `_START_JAVA` content test to update).
- New unit tests: a non-string return triggers `specification_error`, one
  per language driver (Python, JavaScript, Java).
- New/extended integration test: `plcc-rep --format json` shows a real
  `value` for a spec relying on the default `_run()` — no existing test
  proves this today (`tests/bats/e2e/plcc-rep.bats:55` only exercises an
  explicit Python `_run()` returning an `int`, which happens to `repr()`
  the same as `str()` today, masking #162's bug in that particular test).

---

## Versioning

Three languages have a breaking change here, not just Java. Each gets its
own commit with `!` on the type **and** a `BREAKING CHANGE:` footer — `!`
flags it for `python-semantic-release` (which bumps the major version per
`dev-docs/release-sop.md`), the footer tells users what broke and how to
fix it:

```
fix(java)!: _run() must return a String instead of void

_run() now returns a String that the runtime marshals into plcc-rep's
JSON result envelope, matching the return-and-convert contract already
used by Python, JavaScript, and Haskell. The previous void/print-inside-
_run() model silently bypassed the envelope and broke
`plcc-rep --format json`.

BREAKING CHANGE: Java's `_run()` signature changed from `public void
_run()` to `public String _run()`. Any spec that overrides `_run()` (or
a custom entry point) must change it to return a String instead of
printing directly — e.g. replace `System.out.println(x);` with
`return x.toString();`. Specs that never defined `_run()` are
unaffected; the default implementation was updated to match.
```

```
fix(python)!: _run() must return a str, or it's a specification error

The runtime no longer coerces _run()'s return value with repr()/str() —
it uses the returned string as-is, and validates it is actually a str
before doing so. This also fixes _run() returning a quoted string
(issue #162), which was a symptom of the same repr()-based coercion.

BREAKING CHANGE: _run() (or a custom entry point) that returns a
non-str value — an int, a list, any object relied on for its __str__ —
now fails with a specification_error instead of silently working.
Convert the return value explicitly, e.g. `return str(x)` instead of
`return x`. Specs whose _run() already returns a str, or that never
define _run() at all, are unaffected.
```

```
fix(javascript)!: _run() must return a string, or it's a specification error

The runtime no longer coerces _run()'s return value with String() — it
uses the returned string as-is, and validates it is actually a string
before doing so.

BREAKING CHANGE: _run() (or a custom entry point) that returns a
non-string value — a number, an array, any object relied on for its
toString() — now fails with a specification_error instead of silently
working. Convert the return value explicitly, e.g. `return String(x)`
instead of `return x`. Specs whose _run() already returns a string, or
that never define _run() at all, are unaffected.
```

The migration guide carries the same "what broke / how to fix it" content
in prose for all three languages, since it's the durable reference — the
commit footers drive the changelog entries, but not everyone reads
changelogs.

---

## Out of Scope

- Changing Haskell's `_run` to support a suppress-output feature
  (`Maybe String`) — no demonstrated use case, and would reintroduce the
  per-language asymmetry this design deliberately removes.
- Adding a suppress-output feature to any language — dropped entirely (see
  Overview).
- The `languages-corpus.txt` external e2e smoke suite
  (`tests/bats/e2e/languages-java.bats`) — depends on an external repo; any
  fixture updates there happen downstream, not as part of this change.
