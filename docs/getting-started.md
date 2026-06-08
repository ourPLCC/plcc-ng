# Getting Started

## Prerequisites

- Python 3.12 or later
- Java JDK 21 or later (only necessary if implementing semantics in Java)


## Install

```bash
pip install plcc-ng
```

## Quickstart

Let's build a language that sums a sequence of integers.

**Step 1.** Create a grammar file `hello.plcc`:

```text
token NUM '\d+'
skip  WS  '\s+'

%

<Program> **= <NUM:num>

% sum Python

Program
%%%
def _run(self):
  print(sum(int(num.lexeme) for num in self.numList))
%%%
```

**Step 2.** Test scanner:

```bash
echo "42 36 2" | plcc-scan -g hello.plcc
```

Expected:

```text
plcc-ng x.y.z
grammar: hello.plcc
-:1:1 NUM '42'
-:1:4 NUM '36'
-:1:7 NUM '2'
```

**Step 3.** Test parser:

```bash
echo "42 36 2" | plcc-parse
```

Expected:

```text
plcc-ng x.y.z
grammar: hello.plcc
Program
  NUM '42' [-:1:1]
  NUM '36' [-:1:4]
  NUM '2' [-:1:7]
```

**Step 3.** Test semantics:

```bash
echo "42 36 2" | plcc-rep
```

Expected:

```text
plcc-ng x.y.z
grammar: hello.plcc
Running sum with Python.
80
```

From here, see the [Language Guide](language-guide/index.md) to add grammar
rules and semantic code, or the [CLI Reference](cli/index.md) for all available
commands.
