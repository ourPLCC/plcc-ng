# Level 0 Primitives

These commands each perform one step of the pipeline. They are the building
blocks that the [Level 2 orchestrators](orchestrators.md) use internally.

---

## plcc-spec

Parse, validate, and print a PLCC spec file as JSON.

```text
plcc-spec [-v ...] [options] FILE
```

| Argument/Option | Description |
|---|---|
| `FILE` | `.plcc` spec file. Use `-` to read from stdin. |
| `--no-json` | Validate only; do not print JSON to stdout. |

**Example:**

```bash
plcc-spec spec.plcc
```

---

## plcc-tokens

Tokenize source files given a spec JSON file; emit token JSONL.

```text
plcc-tokens [-v ...] [options] SPEC_JSON [SOURCE ...]
```

| Argument/Option | Description |
|---|---|
| `SPEC_JSON` | Path to spec JSON (output of `plcc-spec`). |
| `SOURCE` | Source files to tokenize. Use `-` for stdin. Defaults to stdin. |
| `-t`, `--trace` | Include regex, source line, attempts; emit skip records. |
| `--source-name=LABEL` | Override the source label for stdin. |

**Example:**

```bash
plcc-spec spec.plcc | plcc-tokens - samples
```

---

## plcc-ll1

Perform LL(1) analysis on a grammar spec.

```text
plcc-ll1 [-v ...]
```

Reads spec JSON from stdin (output of `plcc-spec`); emits LL(1) analysis JSON to stdout.

**Example:**

```bash
plcc-spec spec.plcc > spec.json
plcc-ll1 < spec.json > ll1.json
```

---

## plcc-trees

Dispatch to a parser plugin. Reads token JSONL; emits a parse tree.

```text
plcc-trees [-v ...] [options] --ll1=LL1_JSON
```

| Option | Description |
|---|---|
| `--ll1=LL1_JSON` | Path to LL(1) analysis JSON (required). |
| `--parser=KIND` | Parser plugin to use. Default: `table`. |
| `-t`, `--trace` | Forward trace flag to the parser plugin. |

**Example:**

```bash
plcc-spec spec.plcc > spec.json
plcc-ll1 < spec.json > ll1.json
plcc-tokens spec.json samples | plcc-trees --ll1=ll1.json
```

---

## plcc-model

Transform spec JSON into a language-neutral code model.

```text
plcc-model [-v ...] [options] [SPEC_JSON]
```

| Argument | Description |
|---|---|
| `SPEC_JSON` | Path to spec JSON. Use `-` or omit to read from stdin. |

**Example:**

```bash
plcc-spec spec.plcc | plcc-model
```

---

## plcc-lang-emit

Dispatch to the appropriate language emitter.

```text
plcc-lang-emit [-v ...] --target=LANG --output=DIR
```

| Option | Description |
|---|---|
| `--target=LANG` | Target language (e.g. `Python`, `Java`). |
| `--output=DIR` | Directory to write output files into. |

**Example:**

```bash
plcc-spec spec.plcc | plcc-model | plcc-lang-emit --target=Python --output=out/
```

---

## plcc-diagram

Generate and display a class diagram from a PLCC spec file.

```text
plcc-diagram [-v ...] [options]
```

| Option | Description |
|---|---|
| `-s PATH`, `--spec=PATH` | Spec file. Remembers across invocations. Defaults to `spec.plcc`. |
| `--format=FMT` | Diagram format. Default: `plantuml`. |
| `-b`, `--banner` | Show the version and spec banner on stderr. |

**Example:**

```bash
plcc-diagram -s mylang.plcc
```
