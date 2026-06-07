# Getting Started

## Prerequisites

- Python 3.12 or later

<!-- TODO: note whether Java is required for any default workflow, and which version -->

Verify your Python version:

```bash
python3 --version
```

## Install

```bash
pip install plcc-ng
```

Verify the installation:

```bash
plcc-make --help
```

## Quickstart

This quickstart builds a minimal language that recognizes integers.

**Step 1.** Create a grammar file `hello.plcc`:

```text
token NUM '\d+'
skip  WS  '\s+'
%
<Program> ::= <NUM:num>
```

**Step 2.** Build:

```bash
plcc-make -g hello.plcc
```

**Step 3.** Scan some input:

```bash
echo "42" | plcc-scan -g hello.plcc
```

<!-- TODO: verify output format -->
Expected:

```text
   1: NUM '42'
```

**Step 4.** Parse some input:

```bash
echo "42" | plcc-parse -g hello.plcc
```

<!-- TODO: verify output format -->
Expected:

```text
<Program>
| NUM "42"
```

From here, see the [Language Guide](language-guide/index.md) to add grammar
rules and semantic code, or the [CLI Reference](cli/index.md) for all available
commands.
