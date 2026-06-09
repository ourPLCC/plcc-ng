# Semantic Section

The semantic section of a `.plcc` file embeds target-language code into the
classes generated from the grammar. plcc-ng supports multiple target
languages; the section header declares which language to use.

## Section header

The semantic section begins with a header line that names the tool and the
target language:

```text
% toolname Language
```

- `toolname` is a short label used to select this tool at runtime
  (e.g. with `plcc-rep --tool=toolname`).
- `Language` is the target language (e.g. `Python`, `Java`).

A grammar file may contain multiple semantic sections with different tool
names. When only one exists, `plcc-rep` uses it automatically.

## Code blocks

Inside the semantic section, each class gets a block:

```text
ClassName
%%%
...target-language code...
%%%
```

The code is injected into the generated class. The start symbol's class
should define a `_run` method — this is the entry point called by `plcc-rep`.

### Example (Python)

```text
% subtract Python
Prog
%%%
def _run(self):
    print(self.exp.eval())
%%%

WholeExp
%%%
def eval(self):
    return int(self.whole.lexeme)
%%%

SubExp
%%%
def eval(self):
    return self.exp1.eval() - self.exp2.eval()
%%%
```

### Example (Java)

<!-- TODO: verify Java semantic syntax in plcc-ng matches the example below -->
```text
% subtract Java
Prog
%%%
    public void _run() {
        System.out.println(exp.eval());
    }
%%%

WholeExp
%%%
    public int eval() {
        return Integer.parseInt(whole.toString());
    }
%%%

SubExp
%%%
    public int eval() {
        return exp1.eval() - exp2.eval();
    }
%%%
```

## Hooks

Hooks inject code at specific locations within a generated class file.
Append the hook name to the class name with a colon:

| Hook | Where code is injected |
| --- | --- |
| `ClassName:top` | Top of the generated file |
| `ClassName:import` | Import section |
| `ClassName:class` | Class declaration (extend/implement) |
| `ClassName:init` | Constructor / initializer |

<!-- TODO: verify hook syntax and availability in plcc-ng -->

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

## Adding standalone classes

A class not derived from the grammar can be defined by giving it a name that
does not appear in the syntactic section:

<!-- TODO: verify standalone class support in plcc-ng -->
```text
Helper
%%%
class Helper:
    @staticmethod
    def double(x):
        return x * 2
%%%
```

## JSON AST

<!-- TODO: verify JSON AST support in plcc-ng (original PLCC used --json_ast flag on plccmk and parse) -->
