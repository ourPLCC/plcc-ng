# Semantic Section

The semantic section lets you implement language semantics by injecting
target-language code into classes generated from the syntactic section.

## Section header

A bare `%` line separates the previous section from the semantic section.
The first non-blank line of the semantic section body names the language
used by the code blocks.

```text
%
Java
```

The supported languages are:

- Java
- Python

## Code blocks

The semantic section allows you to inject code blocks into the classes generated
from the production rules given in the syntactic section.
The [syntactic section](syntactic.md) describes the classes
and their fields that are generated from production rules.

To inject code into a class, use the following construct.

=== "Python"
    ```text
    %
    Python

    Exp
    %%%
    def _run(self):
        print("Hello")
    %%%
    ```

=== "Java"
    ```text
    %
    Java

    Exp
    %%%
    public void _run() {
        System.out.println("Hello");
    }
    %%%
    ```

Since whatever you put within the `%%%` lines is injected into the body
of the class, you can add static or instance methods, class or instance variables,
or even inner classes. Anything you can place in the body of a class, you
can place inside `%%%`.

## Field Access

Fields generated from production rules become public instance variables.

For example, if the syntactic section contains:

```text
<AddExp> ::= <Exp:left> <PLUS> <Exp:right>
```

the generated class contain fields such as `left`, `plus`, and `right`,
which can be accessed from semantic code.

## Entry point method `_run`

The code between the `%%%` lines is injected into the body of the named class.
The start symbol's class inherits from `_Start`, which defines
a `_run` method that serves as the entry point called by `plcc-rep`.
The default implementation of
`_run` prints a string representation of the root of the parse tree.
You'll want to override the `_run` method to implement the semantics of
your language.

## Hooks

Hooks inject code at specific locations within a generated class file.
Append the hook name to the class name with a colon:

| Hook | Where code is injected | Uses |
| --- | --- | --- |
| `ClassName:top` | Top of the generated file | Package declarations, module directives, file-level code or comments |
| `ClassName:import` | File-level import section | Add imports |
| `ClassName:class` | Class declaration (extend/implement) | Declare class or interface inheritance |
| `ClassName:init` | Constructor / initializer | Add statements to the generated constructor/initializer |

### Example

=== "Python"
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

=== "Java"
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

You can have multiple code blocks that refer to the same class.
The blocks are injected in the order they appear in the semantic section.

## Adding standalone classes

Standalone classes are useful for helper code that does not naturally
belong to a generated grammar class.

You may declare a new class or module that is not derived from
a nonterminal in the syntactic section.
When you do, plcc-ng creates a file based on the class name.
The block contents are written verbatim to that file.

=== "Python"
    ```text
    Helper      # Creates a file named Helper.py
    %%%
    class Helper:
        @staticmethod
        def double(x):
            return x * 2
    %%%
    ```

=== "Java"
    ```text
    Helper      # Creates a file named Helper.java
    %%%
    public class Helper {
        public static int doubled(int x) {
            return x * 2;
        }
    }
    %%%
    ```

## Packages and imports/includes

Each generated class is placed in a separate file with the same name
as the class. All files are placed in the same package.

For Java, this means that all classes can access all other classes without
explicitly importing them.

In Python, code that refers to another generated class by name must
add an appropriate relative import.
