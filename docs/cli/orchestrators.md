# Level 2 Orchestrators

These commands compose the [Level 0 primitives](primitives.md) for the most
common workflows. They are the commands students use day-to-day.

---

## plcc-make

Build a PLCC project from a spec file.

```text
plcc-make [-v ...] [options]
```

| Option | Description |
|---|---|
| `-s PATH`, `--spec=PATH` | Spec to build from. Remembered across invocations. Defaults to `spec.plcc` on first use. |
| `--through=LEVEL` | Build up to this level: `scan`, `parse`, `model`, or `all`. Default: `all`. |
| `-b`, `--banner` | Show the version and spec banner on stderr. |

**Example:**

```bash
plcc-make -s subtract.plcc
```

Run `plcc-make` again after editing your spec to rebuild.

---

## plcc-scan

Tokenize source input and print tokens in human-readable format.

```text
plcc-scan [-v ...] [options] [SOURCE ...]
```

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to tokenize. Reads stdin if none given. |
| `-s PATH`, `--spec=PATH` | Spec to build from. Remembered across invocations. |
| `-t`, `--trace` | Show detailed scanning output. |
| `-b`, `--banner` | Show the version and spec banner on stderr. |

**Example:**

```bash
plcc-scan -s subtract.plcc samples
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
| `-s PATH`, `--spec=PATH` | Spec to build from. Remembered across invocations. |
| `-b`, `--banner` | Show the version and spec banner on stderr. |

**Example:**

```bash
plcc-parse -s subtract.plcc samples
echo "42" | plcc-parse
```

---

## plcc-rep

REPL — read, eval, print loop for a PLCC spec.

```text
plcc-rep [-v ...] [options] [SOURCE ...]
```

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to evaluate before entering interactive mode. |
| `-s PATH`, `--spec=PATH` | Spec to build from. Remembered across invocations. |
| `--tool=NAME` | Semantic section to run. Inferred automatically when only one exists. |
| `-b`, `--banner` | Show the version and spec banner on stderr. |

**Example:**

```bash
# Run the 'subtract' semantic section against samples, then enter interactive mode
plcc-rep -s subtract.plcc --tool=subtract samples

# Evaluate a file only (no interactive mode)
plcc-rep -s subtract.plcc samples < /dev/null
```

<!-- TODO: verify how to suppress interactive mode (< /dev/null or EOF behavior) -->
