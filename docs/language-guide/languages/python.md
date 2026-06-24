# Python

## Prerequisites

Python 3.12 or later. Python is typically pre-installed on macOS and Linux.

Verify your installation:

```bash
python3 --version
```

## Enabling in a spec

Add a bare `%` separator after the syntactic section, then write `Python` on the first non-blank line:

```text
%
Python
```

## Quick reference example

This example exercises every grammar construct. Later sections reference it by name.

```text
token NUM   '\d+'
token PLUS  '\+'
skip  SPACE '\s+'
%
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
%
Python

Prog
%%%
def _run(self):
    return '\n'.join(str(exp.eval()) for exp in self.expList)
%%%

AddExp
%%%
def eval(self):
    return self.left.eval() + self.right.eval()
%%%

NumExp
%%%
def eval(self):
    return int(self.num.lexeme)
%%%
```

Running this with `echo "1 + 2" | plcc-rep` prints `3`.

## BNF to Python constructs

| Grammar construct | Python | Example from spec |
| --- | --- | --- |
| Concrete non-terminal rule | Python dataclass with fields | `<Exp:NumExp> ::= <NUM>` |
| Abstract non-terminal (has alternatives) | Python class, no fields or constructor | `<Exp>` |
| Named non-terminal field (`:name` on RHS) | `self.name` — instance of that class | `<Exp:left>` → `self.left` |
| Captured terminal (`<TOKEN>`) | `self.name` — a `Token` | `<NUM>` → `self.num` |
| Token string value | `.lexeme` on the token | `self.num.lexeme` → `"42"` |
| Uncaptured terminal (no angle brackets) | Not stored, no field | `PLUS` in `<Exp:AddExp>` |
| Arbno (`**=`) | `List[ClassName] nameList` | `<Prog> **= <Exp>` → `self.expList` |

Without explicit `:name` on a RHS symbol, the field name is the symbol name lowercased. Use explicit names when two RHS symbols would produce the same field name.

## Fragment kinds

| Kind | Where injected | Typical use |
| --- | --- | --- |
| `top` | Top of the file, before imports | Module-level constants or directives |
| `import` | Import section | `import` or `from … import` statements |
| `class` | Class declaration line | Additional base classes (multiple inheritance) |
| `init` | `__init__` body, after field assignments | Initialize extra instance state |
| `body` | Class body | Methods, class variables |
| `file` | Replaces the entire file | Standalone helper modules |

`body` is the default when no kind is given (plain `ClassName` with no colon).

### Example

```text
WholeExp:import
%%%
import sys
%%%

WholeExp
%%%
def eval(self):
    x = int(self.whole.lexeme)
    sys.stderr.write(f"eval: {x}\n")
    return x
%%%
```

## `_run` entry point

`_run()` is called by the runtime on the root node of each parsed tree. Define it on your start class (`Prog` in the quick reference example).

```python
Prog
%%%
def _run(self):
    # compute and return a value, or return None to produce no output
    return '\n'.join(str(exp.eval()) for exp in self.expList)
%%%
```

The return value is converted to a string and printed by `plcc-rep`. Return `None` to suppress output.

The default `_Start._run()` prints `str(self)`. Override it to replace the default behavior.

## Referencing other generated classes

Generated `.py` files are separate modules. To use a sibling class, import it with an `import` fragment:

```text
MyClass:import
%%%
from .OtherClass import OtherClass
%%%
```

## Generated output

`plcc-python-emit` writes `.py` files. **All files are overwritten on every emit run.**

```
DIR/
  main.py           — entry point
  _Start.py         — default base for the start class
  Prog.py           — one .py file per class from the grammar
  AddExp.py
  NumExp.py
  runtime/
    ...
```

Do not edit these files directly.

## Running the quick reference example

Save the spec above as `spec.plcc`. In the same directory:

```bash
echo "1 + 2" | plcc-rep
```

Expected output:

```text
3
```

## Commands

| Command | What it does |
| --- | --- |
| [`plcc-python-emit`](../../cli/commands/plcc-python-emit.md) | Writes `.py` class files and a `main.py` entry point to the output directory |
| [`plcc-python-run`](../../cli/commands/plcc-python-run.md) | Runs `main.py` with the system Python interpreter |

No build step is required — Python does not need a compilation step, so `plcc-lang-build` skips silently.

## Restrictions

- Requires Python 3.12 or later.
- Generated files are overwritten on every emit run — do not edit them directly.
- Sibling generated classes are not automatically in scope; import them explicitly with an `import` fragment.

## Tips

- Use `sys.stderr.write(...)` (after `import sys`) for debug output so it does not interfere with the output protocol.
- `self.num.lexeme` is always a string. Use `int(self.num.lexeme)` or `float(self.num.lexeme)` to get a numeric value.
- Abstract classes have no constructor. You can add methods to them via `body` fragments; subclasses inherit them.
- The `class` hook enables multiple inheritance. Use it to add a base class: `MyClass:class\n%%%\n, MyMixin\n%%%`.
