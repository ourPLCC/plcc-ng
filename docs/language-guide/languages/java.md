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
skip  SPACE '\s+'
%
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
%
Java

Exp
%%%
public abstract int eval();
%%%

Prog
%%%
public void _run() {
    for (Exp exp : expList) {
        System.out.println(exp.eval());
    }
}
%%%

AddExp
%%%
public int eval() {
    return left.eval() + right.eval();
}
%%%

NumExp
%%%
public int eval() {
    return Integer.parseInt(num.lexeme);
}
%%%
```

Running this with `echo "1 + 2" | plcc-rep` prints `3`.

## BNF to Java constructs

| Grammar construct | Java | Example from spec |
| --- | --- | --- |
| Concrete non-terminal rule | Java class with public fields and constructor | `<Exp:NumExp> ::= <NUM>` |
| Abstract non-terminal (has alternatives) | `abstract` Java class | `<Exp>` |
| Named non-terminal field (`:name` on RHS) | `name` — instance of that class | `<Exp:left>` → `left` |
| Captured terminal (`<TOKEN>`) | `name` — a `Token` | `<NUM>` → `num` |
| Token string value | `.lexeme` on the token | `num.lexeme` → `"42"` |
| Uncaptured terminal (no angle brackets) | Not stored, no field | `PLUS` in `<Exp:AddExp>` |
| Arbno (`**=`) | `ArrayList<ClassName> nameList` | `<Prog> **= <Exp>` → `expList` |

Without explicit `:name` on a RHS symbol, the field name is the symbol name lowercased. Use explicit names when two RHS symbols would produce the same field name.

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
public void _run() {
    // your implementation
}
%%%
```

The default `_Start._run()` prints `String(this)` using `System.out.println`. Override it to replace the default behavior. Return type is `void`.

Abstract classes cannot be instantiated. Declare abstract methods on them so the Java compiler enforces that all concrete subclasses implement them (see `Exp` in the quick reference example).

## Referencing other generated classes

All generated `.java` files are compiled together in the same package. You can reference any sibling class by name directly — no import needed.

## Generated output

`plcc-java-emit` writes `.java` source files. `plcc-java-build` compiles them with `javac`. **All source files are overwritten on every emit run.**

```
DIR/
  Main.java         — entry point
  _Start.java       — default base for the start class
  Prog.java         — one .java file per class from the grammar
  AddExp.java
  NumExp.java
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

## Tips

- Use `System.err.println(...)` for debug output so it does not interfere with the output protocol.
- `num.lexeme` is always a `String`. Use `Integer.parseInt(num.lexeme)` or `Double.parseDouble(num.lexeme)` to get a numeric value.
- All generated classes are in the same package — you can use any generated class by name without importing it.
