# Level 2 Orchestrators

These commands compose the [Level 0 primitives](primitives.md) for the most
common workflows. They are the commands students use day-to-day.

---

## plcc-make

Build a PLCC project from a grammar file.

```text
plcc-make [-v ...] [options]
```

| Option | Description |
|---|---|
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. Defaults to `grammar.plcc` on first use. |
| `--through=LEVEL` | Build up to this level: `scan`, `parse`, `model`, or `all`. Default: `all`. |
| `--no-banner` | Suppress the version and grammar banner. |

**Example:**

```bash
plcc-make -g subtract.plcc
```

Run `plcc-make` again after editing your grammar to rebuild.

---

## plcc-scan

Tokenize source input and print tokens in human-readable format.

```text
plcc-scan [-v ...] [options] [SOURCE ...]
```

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to tokenize. Reads stdin if none given. |
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. |
| `-t`, `--trace` | Show detailed scanning output. |
| `--no-banner` | Suppress the version and grammar banner. |

**Example:**

```bash
plcc-scan -g subtract.plcc samples
echo "42" | plcc-scan
```

---

## plcc-parse

Parse source input and print the parse tree in human-readable format.

```text
plcc-parse [-v ...] [options] [SOURCE ...]
```

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to parse. Reads stdin if none given. |
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. |
| `--no-banner` | Suppress the version and grammar banner. |

**Example:**

```bash
plcc-parse -g subtract.plcc samples
echo "42" | plcc-parse
```

---

## plcc-rep

REPL — read, eval, print loop for a PLCC grammar.

```text
plcc-rep [-v ...] [options] [SOURCE ...]
```

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to evaluate before entering interactive mode. |
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. |
| `--tool=NAME` | Semantic section to run. Inferred automatically when only one exists. |
| `--no-banner` | Suppress the version and grammar banner. |

**Example:**

```bash
# Run the 'subtract' semantic section against samples, then enter interactive mode
plcc-rep -g subtract.plcc --tool=subtract samples

# Evaluate a file only (no interactive mode)
plcc-rep -g subtract.plcc samples < /dev/null
```

<!-- TODO: verify how to suppress interactive mode (< /dev/null or EOF behavior) -->
