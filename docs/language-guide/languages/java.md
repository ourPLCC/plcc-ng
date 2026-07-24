# Java

## Prerequisites

Java JDK 21 or later. Install from [adoptium.net](https://adoptium.net) or use your system package manager.

Verify your installation:

```bash
java --version
javac --version
```

## Enabling in a spec

Add a bare `%` separator after the syntactic section, then write `Java` on the first non-blank line:

```text
%
Java
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
Java

Op
%%%
public abstract int apply(int left, int right);
%%%

Expr
%%%
public int eval() {
    return op.apply(Integer.parseInt(left.lexeme), Integer.parseInt(right.lexeme));
}
%%%

Prog
%%%
public String _run() {
    java.util.List<String> lines = new java.util.ArrayList<>();
    for (Expr expr : exprList) {
        lines.add(String.valueOf(expr.eval()));
    }
    return String.join("\n", lines);
}
%%%

AddOp
%%%
public int apply(int left, int right) {
    return left + right;
}
%%%

SubOp
%%%
public int apply(int left, int right) {
    return left - right;
}
%%%
```

Running this with `echo "1 + 2" | plcc-rep` prints `3`.

## BNF to Java constructs

| Grammar Construct | Example from spec | Java Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one class | `<Prog>` in `<Prog> **= <Expr>` | Java class with public fields and constructor | `class Prog extends _Start { public ArrayList<Expr> exprList; ... }` |
| Alternative rule (LHS, with alt name) — base nonterminal becomes abstract | `<Op:AddOp>` in `<Op:AddOp> ::= PLUS` | Java class extending the base nonterminal | `class AddOp extends Op { ... }` |
| Named non-terminal (RHS) | `<Op:op>` in `<Expr> ::= <NUM:left> <Op:op> <NUM:right>` | `op` — an `Op` instance | `op.apply(left, right)` |
| Captured terminal (RHS) | `<NUM:left>` | `left` — a `Token`; `.lexeme` for the string value | `Integer.parseInt(left.lexeme)` |
| Uncaptured terminal (RHS) | `PLUS` in `<Op:AddOp> ::= PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Expr>` | `exprList` — `ArrayList<Expr>` | `for (Expr expr : exprList)` |

Without explicit `:name` on a RHS symbol, the field name is the symbol name lowercased (e.g., `<Expr>` → `expr`, `<NUM>` → `num`). Use explicit names when two RHS symbols would produce the same field name.

All generated classes are in the same package, so sibling classes are accessible without explicit imports.

## Fragment kinds

| Kind | Where injected | Typical use |
| --- | --- | --- |
| `top` | Top of the file, before the class | Package declarations |
| `import` | Import section | `import` statements |
| `class` | Class declaration line | `implements` clauses, additional `extends` |
| `init` | Constructor body, after field assignments | Initialize extra instance state |
| `body` | Class body | Methods, static fields |
| `file` | Replaces the entire file | Standalone helper classes |

`body` is the default when no kind is given (plain `ClassName` with no colon).

### Example

```text
WholeExp:import
%%%
import java.io.*;
%%%

WholeExp
%%%
public int eval() {
    int x = Integer.parseInt(whole.lexeme);
    System.err.println("eval: " + x);
    return x;
}
%%%
```

## `_run` entry point

`_run()` is called by the runtime on the root node of each parsed tree. Define it on your start class (`Prog` in the quick reference example).

```java
Prog
%%%
public String _run() {
    // your implementation
}
%%%
```

`_run()` must return a `String`. The runtime sends that string to `plcc-rep` as-is — it is not converted or coerced. Returning `null` raises a `specification_error`.

Do not print or write to stdout from inside `_run()` — that bypasses `plcc-rep`'s JSON result envelope. Plain-text mode will still show what you printed, but `plcc-rep --verbose-format=json` will not.

The default `_Start._run()` returns `this.toString()`. Override it to replace the default behavior.

Abstract classes cannot be instantiated. Declare abstract methods on them so the Java compiler enforces that all concrete subclasses implement them (see `Op` in the quick reference example).

## `LanguageError`

Throw `LanguageError` to signal a deliberate error in the defined language — a type mismatch, division by zero, or any condition your language treats as an error. `plcc-rep` prints the message and gives a fresh prompt; the session continues.

`LanguageError` is available in all generated classes without any import:

```java
public int eval() {
    throw new LanguageError("type mismatch: expected int");
}
```

Subclass it to create named error types:

```java
public class DivisionByZeroError extends LanguageError {
    public DivisionByZeroError() { super("division by zero"); }
}
```

```java
public int eval() {
    throw new DivisionByZeroError();
}
```

Any other exception (not `LanguageError` or a subclass) is treated as a specification error — `plcc-rep` prints the error and exits.

## Referencing other generated classes

All generated `.java` files are compiled together in the same package. You can reference any sibling class by name directly — no import needed.

## Generated output

`plcc-java-emit` writes `.java` source files. `plcc-java-build` compiles them with `javac`. **All source files are overwritten on every emit run.**

```
DIR/
  Main.java         — entry point
  _Start.java       — default base for the start class
  Prog.java         — one .java file per class from the grammar
  Expr.java
  AddOp.java
  SubOp.java
  *.class           — compiled after plcc-java-build
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
| [`plcc-java-emit`](../../cli/commands/plcc-java-emit.md) | Writes `.java` class files and a `Main.java` entry point to the output directory |
| [`plcc-java-build`](../../cli/commands/plcc-java-build.md) | Compiles all `.java` files with `javac`; requires Java JDK 21+ on `PATH` |
| [`plcc-java-run`](../../cli/commands/plcc-java-run.md) | Runs the compiled interpreter with `java`; requires Java JDK 21+ on `PATH` |

## Restrictions

- Requires Java JDK 21 or later for both building and running.
- All generated source files are overwritten on every emit run — do not edit them directly.
- Abstract classes need abstract method declarations added via `body` fragments if you want the compiler to enforce them on subclasses.
- A field name that becomes a Java reserved word (e.g. `class`, `new`) is rejected by `plcc-java-emit` — rename the capture. `var` is fine (it's only reserved for local-variable type inference, not field declarations). See [Reserved words](../syntactic.md#reserved-words) for details.

## Tips

- Use `System.err.println(...)` for debug output so it does not interfere with the output protocol.
- `num.lexeme` is always a `String`. Use `Integer.parseInt(num.lexeme)` or `Double.parseDouble(num.lexeme)` to get a numeric value.
- All generated classes are in the same package — you can use any generated class by name without importing it.
