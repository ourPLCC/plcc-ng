# Getting Started

## Prerequisites

- Python 3.12 or later
- Java JDK 21 or later (only necessary if implementing semantics in Java)

## Install

```bash
pip install plcc-ng
```

## Test Drive

Let's build a language that sums a sequence of integers.

**Step 1.** Create a grammar file `sum.plcc`:

```text
skip  WHITESPACE '\s+'
token NUM '\d+'

%

<Program> **= <NUM:num>

% Summation Python

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
80
```

## What Next

- [Language Guide](language-guide/index.md) - Learn to specify languages.
- [CLI Reference](cli/index.md) - Learn about commands.
