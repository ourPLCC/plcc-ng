# Getting Started

## Prerequisites

- Python 3.12 or later
- Java JDK 21 or later (only necessary if implementing semantics in Java)

## Install

```bash
pip install plcc-ng
```

## Test Drive

Let's build a tiny language whose programs consist of a sequence of integers.
Running a program will print their sum.

### 1. Define the language

Create a file named `grammar.plcc`:

```text
# Define the tokens of the language.
skip  WHITESPACE '\s+'
token NUM '\d+'

%

# Define the structure of the language.
# A program consists of a sequence of numbers.
<Program> **= <NUM:num>

% Python

# Define what happens when a program is run.
Program
%%%
def _run(self):
  print(sum(int(str(num)) for num in self.numList))
%%%
```

PLCC-ng automatically generates fields such as `numList` from the grammar.
The [Language Guide](language-guide/index.md) explains how this mapping works.

### 2. Scan source text

In the same directory as `grammar.plcc`:

```bash
echo "42 36 2" | plcc-scan
```

`plcc-scan` automatically discovers the grammar file.

Output:

```text
-:1:1 NUM '42'
-:1:4 NUM '36'
-:1:7 NUM '2'
```

### 3. Parse source text

In the same directory:

```bash
echo "42 36 2" | plcc-parse
```

Output:

```text
Program
  NUM '42' [-:1:1]
  NUM '36' [-:1:4]
  NUM '2' [-:1:7]
```

### 4. Run the program

In the same directory:

```bash
echo "42 36 2" | plcc-rep
```

Output:

```text
80
```

Congratulations! You've defined a language,
scanned it with `plcc-scan`, parsed it with `plcc-parse`,
and executed it with `plcc-rep`.

## What Next

- [Language Guide](language-guide/index.md) - Learn to specify languages.
- [CLI Reference](cli/index.md) - Learn about commands.
