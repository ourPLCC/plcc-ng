# 165 - `_run()`'s return-and-convert contract is violated by default implementations, undocumented for overriders, and missing from the migration guide

**Type:** fix
**Date:** 2026-07-23

## Description

Found while investigating #162. PLCC-ng's `_run()` is supposed to be a
deliberate redesign of original PLCC's `$run()`: PLCC's `$run()` was
`void` and printed directly (typically `System.out.println(this)` /
`print(self)`), putting I/O inside the semantics code. `_run()` moved
that responsibility out — it **returns** a value, and the runtime
driver (`main.py.jinja` / `main.js.jinja` / `Main.hs` / `Main.java.jinja`)
converts that return value to a string and marshals it into a
`{"kind": "result", "value": "<string>"}` JSON record, which
`plcc-rep` reads and prints. Centralizing this in the runtime is what
lets `plcc-rep --format json` show a real, structured record for every
result instead of raw text.

That redesign is not actually in effect everywhere:

1. **Three of four languages' *default* `_run()` implementations still
   follow the old `$run()` pattern** — printing directly and returning
   nothing — rather than the new contract:

   - Python (`src/plcc/lang/ext/python/emit.py:32-33`):
     `def _run(self): print(str(self))`
   - JavaScript (`src/plcc/lang/ext/javascript/emit.py:31-32`):
     `_run() { console.log(String(this)); }`
   - Java (`src/plcc/lang/ext/java/emit.py:29-30`):
     `public void _run() { System.out.println(this.toString()); }`

   Only Haskell's default is contract-compliant:
   `_run = show` (`src/plcc/lang/ext/haskell/emit.py:170`) — `show`
   *returns* a `String`; it does not print.

   Because Python/JS/Java's defaults return nothing, each runtime
   driver sees `None`/`undefined`/`null`, emits a no-op
   `{"kind": "result", "value": null}` record, and the text the user
   actually sees already went to stdout as a raw, un-enveloped line
   before the JSON machinery ran. This means **any spec that doesn't
   override `_run()`** — not just ones with a custom Java
   implementation — silently breaks `plcc-rep --format json` in
   Python and JavaScript too.

2. **The contract itself is not documented as a rule for users who
   override `_run()`.** `docs/language-guide/languages/python.md` and
   `javascript.md` describe what happens to the return value but never
   state the flip side — that printing directly from inside `_run()`
   bypasses the envelope and breaks `--format json`. `java.md` goes
   further and actively teaches the incompatible pattern: it documents
   `_run()` as `void` and shows `System.out.println` inside it as the
   correct way to produce output (`docs/language-guide/languages/java.md:117-128`).

3. **The migration guide doesn't mention the contract changed, only
   that the method was renamed.** `docs/migration.md` section 9,
   "Rename the entry point method," is a one-row table:
   `$run()` → `_run()` — with no mention that the *behavior* expected
   of that method also changed, from void-and-print to
   return-and-let-the-runtime-print. Anyone migrating a PLCC spec that
   did `System.out.println(...)` / `print(...)` inside `$run()` (the
   normal old-PLCC idiom) will rename the method, keep the print
   statement, watch it keep working in plain-text mode, and only
   discover the breakage later under `--format json`. This belongs
   next to the other two entries already listed under "Breaking
   behavior changes" at the top of the guide, which exists precisely
   to surface changes "easy to miss ... that have caught instructors
   migrating workshop materials by surprise."

## Notes

Fix has three parts, all needed together — this is a `fix` (default
behavior in `src/`) with accompanying `docs` work, not a docs-only
issue:

- **Code:** change the Python, JavaScript, and Java default `_run()`
  implementations to `return` the string (`str(self)` / `String(this)`
  / `this.toString()`) instead of printing it, so the default goes
  through the same JSON-envelope path as a compliant user override.
  This also depends on/relates to the Java design question below.
- **Docs:** add an explicit statement of the contract to each
  language guide ("`_run()` must return its output; do not print from
  inside it, or `--format json` will not see it") — not just describe
  what happens to the return value. `java.md` needs the larger
  rewrite, per the open design question.
- **Migration guide:** add an entry to section 9 (and consider listing
  it under "Breaking behavior changes" at the top of
  `docs/migration.md`, alongside the `plcc-parse`/`plcc-scan` output
  changes) explaining that `$run()`'s void/print behavior does not
  carry over — `_run()` must return its output.

Still-open design question specific to Java (carried over from the
original scope of this issue): should Java's *user-facing* `_run()`
signature change from `void` to a return type, to match
Python/JS/Haskell, or should the void/print style remain a deliberate,
documented exception for Java? Options, unchanged from before:

1. Change Java to match the other three: `_run()` returns a value
   (e.g. `Object` or `String`), and the runtime converts/wraps it —
   same contract everywhere.
2. Keep Java's void/print model, but make the runtime honor it
   explicitly (e.g. capture stdout written during `_run()` and wrap it
   in the JSON envelope) instead of relying on `rep.py`'s
   fallback-line tolerance (`src/plcc/cmd/rep.py:176-181`), so
   `--format json` works correctly for Java too.
3. Document the two models as an intentional, permanent
   per-language difference, with a clear rationale, and make sure both
   the language guide and migration guide state it explicitly.

Whichever option is chosen for Java, the default-implementation bug in
Python and JavaScript (part 1 above) should be fixed regardless — it's
a straightforward contract violation, not a design question.

Related: [#162](162-python-run-return-value-quoted.md) (Python's
return-value conversion uses `repr()` instead of `str()` for
user-returned values — a distinct bug in the same code path as this
issue's default-implementation problem, but scoped to explicit
`return` statements rather than the default).
