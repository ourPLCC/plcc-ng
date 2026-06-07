# Getting Started

## Prerequisites

- Python 3.12 or later
- Java JDK 21 or later (only necessary if implementing semantics in Java)


## Install

```bash
pip install plcc-ng
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

**Step 2.** Test scanner:

```bash
echo "42" | plcc-scan -g hello.plcc --no-banner
```

Expected:

```text
-:1:1 NUM '42'
```

**Step 3.** Test parser:

```bash
echo "42" | plcc-parse -g hello.plcc --no-banner
```

Expected:

```text
Program
  NUM '42' [-:1:1]
```

From here, see the [Language Guide](language-guide/index.md) to add grammar
rules and semantic code, or the [CLI Reference](cli/index.md) for all available
commands.
