# Language extensions

Language extensions provide the emit, build, and run steps for a specific
target language. plcc-ng ships with Python, Java, JavaScript, and Haskell support.

## How language extensions plug in

When `plcc-make` (or any command that calls it) builds a spec with a semantic
section, it runs three dispatch commands in sequence:

1. [`plcc-lang-emit --target=LANG`](../commands/plcc-lang-emit.md) — calls `plcc-<lang>-emit`
2. [`plcc-lang-build --target=LANG`](../commands/plcc-lang-build.md) — calls `plcc-<lang>-build` (no-op if not found)
3. [`plcc-lang-run --target=LANG`](../commands/plcc-lang-run.md) — calls `plcc-<lang>-run`

The `LANG` value comes from the `language` declaration in the spec's semantic
section. Use [`plcc-lang-list`](../commands/plcc-lang-list.md) to see what is
installed.

## plcc-python

Emits a Python interpreter from model JSON, then runs it with the system
Python.

| Command | What it does |
| --- | --- |
| [`plcc-python-emit`](../commands/plcc-python-emit.md) | Writes `.py` class files and a `main.py` entry point to the output directory |
| [`plcc-python-run`](../commands/plcc-python-run.md) | Runs `main.py` with the system Python interpreter |

No build step is required for Python — `plcc-lang-build` exits silently if
`plcc-python-build` is not found.

## plcc-java

Emits a Java interpreter from model JSON, compiles it with `javac`, then
runs it with `java`.

| Command | What it does |
| --- | --- |
| [`plcc-java-emit`](../commands/plcc-java-emit.md) | Writes `.java` class files and a `Main.java` entry point to the output directory |
| [`plcc-java-build`](../commands/plcc-java-build.md) | Compiles all `.java` files with `javac`; requires Java JDK 21+ on `PATH` |
| [`plcc-java-run`](../commands/plcc-java-run.md) | Runs `Main` with `java`; requires Java JDK 21+ on `PATH` |

## plcc-javascript

Emits a JavaScript interpreter from model JSON, then runs it with Node.js.
No build step is required.

| Command | What it does |
| --- | --- |
| [`plcc-javascript-emit`](../commands/plcc-javascript-emit.md) | Writes `.js` class files and a `main.js` entry point to the output directory |
| [`plcc-javascript-run`](../commands/plcc-javascript-run.md) | Runs `main.js` with `node`; requires Node.js 18+ on `PATH` |

No build step is required for JavaScript — `plcc-lang-build` exits silently if
`plcc-javascript-build` is not found.

## plcc-haskell

Emits a Haskell interpreter from model JSON, compiles it with cabal, then
runs it with `cabal run`.

| Command | What it does |
| --- | --- |
| [`plcc-haskell-emit`](../commands/plcc-haskell-emit.md) | Writes `.hs` source files and an `interpreter.cabal` project file to the output directory |
| [`plcc-haskell-build`](../commands/plcc-haskell-build.md) | Compiles with `cabal build`; requires GHC 9.4+ and cabal 3.0+ on `PATH` |
| [`plcc-haskell-run`](../commands/plcc-haskell-run.md) | Runs `cabal run interpreter`; requires cabal 3.0+ on `PATH` |

## The `_run()` protocol

Every language extension's `main`/entry-point driver must implement the same
contract for the root node's entry point method (`_run()` by default, or a
custom name from `entry_point`):

- It **returns a string**. The driver marshals it into a
  `{"kind": "result", "value": "<string>"}` JSON record on stdout for
  `plcc-rep` to read and print — it does not print or convert the value
  itself.
- If it returns anything other than a string (or, for statically-typed
  languages, if the call otherwise fails to produce one — e.g. Java's
  reflection returning `null`), the driver raises a `specification_error`.
  It must never let a wrong-typed value flow into the `value` field
  silently.
- The entry-point implementation itself must never write to stdout. Doing
  so bypasses the JSON envelope entirely; plain-text `plcc-rep` sessions
  will still show it (by accident, since unparseable lines are echoed
  as-is), but `plcc-rep --verbose-format=json` will not.

This is what lets `plcc-rep --verbose-format=json` show a real, structured
record for every result, regardless of which language emitted the
interpreter. A new language extension must follow it to interoperate
correctly with `plcc-rep`.
