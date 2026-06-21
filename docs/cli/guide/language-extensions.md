# Language Extensions

Language extensions provide the emit, build, and run steps for a specific
target language. plcc-ng ships with Python and Java support.

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
