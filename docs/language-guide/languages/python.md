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
token MINUS '-'
skip  SPACE '\s+'
%
<Prog>     **= <Expr>
<Expr>     ::= <NUM:left> <Op:op> <NUM:right>
<Op:AddOp> ::= PLUS
<Op:SubOp> ::= MINUS
%
Python

Prog
%%%
def _run(self):
    return '\n'.join(str(expr.eval()) for expr in self.exprList)
%%%

Expr
%%%
def eval(self):
    return self.op.apply(int(self.left.lexeme), int(self.right.lexeme))
%%%

AddOp
%%%
def apply(self, left, right):
    return left + right
%%%

SubOp
%%%
def apply(self, left, right):
    return left - right
%%%
```

Running this with `echo "1 + 2" | plcc-rep` prints `3`.

## BNF to Python constructs

| Grammar Construct | Example from spec | Python Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one class | `<Prog>` in `<Prog> **= <Expr>` | Python dataclass with fields | `@dataclass class Prog(_Start): exprList: List[Expr]` |
| Alternative rule (LHS, with alt name) — base nonterminal becomes abstract | `<Op:AddOp>` in `<Op:AddOp> ::= PLUS` | Python dataclass extending the base nonterminal | `@dataclass class AddOp(Op): ...` |
| Named non-terminal (RHS) | `<Op:op>` in `<Expr> ::= <NUM:left> <Op:op> <NUM:right>` | `self.op` — an `Op` instance | `self.op.apply(left, right)` |
| Captured terminal (RHS) | `<NUM:left>` | `self.left` — a `Token`; `.lexeme` for the string value | `int(self.left.lexeme)` |
| Uncaptured terminal (RHS) | `PLUS` in `<Op:AddOp> ::= PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Expr>` | `self.exprList` — `List[Expr]` | `[e.eval() for e in self.exprList]` |

Without explicit `:name` on a RHS symbol, the field name is derived from the symbol name: a terminal is lowercased (`<NUM>` → `self.num`), and a nonterminal has just its first letter decapitalized (`<Expr>` → `self.expr`, `<OneMore>` → `self.oneMore`). Use explicit names when two RHS symbols would produce the same field name.

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
    return '\n'.join(str(expr.eval()) for expr in self.exprList)
%%%
```

`_run()` must return a `str`. The runtime sends that string to `plcc-rep` as-is — it is not converted or coerced. Returning anything else (an `int`, a `list`, `None`, ...) raises a `specification_error`; convert explicitly (`str(x)`) if needed.

Do not print or write to stdout from inside `_run()` — that bypasses `plcc-rep`'s JSON result envelope. `plcc-rep` echoes the stray text as-is in every verbose format: plain-text mode shows it alongside the result, and `--verbose-format=json` emits it as a line that is not JSON among the JSON records, breaking any consumer that parses the stream.

The default `_Start._run()` returns `str(self)`. Override it to replace the default behavior.

## `LanguageError`

Raise `LanguageError` to signal a deliberate error in the defined language — a type mismatch, division by zero, or any condition your language treats as an error. `plcc-rep` prints the message and gives a fresh prompt; the session continues.

`LanguageError` is available in all generated classes without any import:

```python
def eval(self):
    raise LanguageError("type mismatch: expected int")
```

Subclass it to create named error types:

```python
class DivisionByZeroError(LanguageError): pass
raise DivisionByZeroError("division by zero")
```

Any other exception (not `LanguageError` or a subclass) is treated as a specification error — `plcc-rep` prints the error and exits.

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
  Expr.py
  AddOp.py
  SubOp.py
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
- A field name that becomes a Python keyword (e.g. `class`, `import`, `is`) is rejected by `plcc-python-emit` — rename the capture. See [Reserved words](../syntactic.md#reserved-words) for details.

## Tips

- Use `sys.stderr.write(...)` (after `import sys`) for debug output so it does not interfere with the output protocol.
- `self.num.lexeme` is always a string. Use `int(self.num.lexeme)` or `float(self.num.lexeme)` to get a numeric value.
- Abstract classes have no constructor. You can add methods to them via `body` fragments; subclasses inherit them.
- The `class` hook enables multiple inheritance. Use it to add a base class: `MyClass:class\n%%%\n, MyMixin\n%%%`.
