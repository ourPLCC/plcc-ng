# Semantic Section

The semantic section lets you implement language semantics by injecting
target-language code into classes generated from the syntactic section.

## Section header

A bare `%` line separates the previous section from the semantic section.
The first non-blank line of the semantic section body names the target language.

```text
%
javascript
```

## Code blocks

To inject code into a class, name the class and follow it with a `%%%` block:

```text
ClassName
%%%
# your code here
%%%
```

The block's content is injected into the class body. Multiple blocks for the
same class are injected in the order they appear.

## Field access

Fields generated from production rules become instance variables in the
generated class. For example:

```text
<AddExp> ::= <Exp:left> PLUS <Exp:right>
```

generates a class with fields `left` and `right`. How you access them depends
on your target language — see your language's page below.

## Entry point: `_run`

The start symbol's class inherits from `_Start`, which defines a `_run`
method that is called when you run a program with `plcc-rep`. The default
implementation prints a string representation of the parse tree root.
Override `_run` in your start class to implement your language's semantics.

## Hooks

Hooks inject code at specific locations within a generated class file.
Append the hook name to the class name with a colon:

```text
ClassName:hook
%%%
# code injected at the hook location
%%%
```

| Hook | Where code is injected |
| --- | --- |
| `top` | Top of the generated file |
| `import` | File-level import section |
| `class` | Class declaration line (extend/implement) |
| `init` | Constructor / initializer |

Supported hooks and their exact placement vary by language. See your language's
page for the full list and any language-specific restrictions.

## Adding standalone classes

You can create a file that is not derived from a grammar nonterminal.
Name a class that does not appear in the grammar and follow it with a `%%%`
block; plcc-ng writes the block's content verbatim to a file named after
the class.

## Choose your language

Each language page covers: prerequisites, enabling in a spec, a quick
reference example, how BNF constructs map to language constructs, supported
hooks, the `_run` contract, generated output, commands, restrictions, and tips.

- [JavaScript](languages/javascript.md)
- [Java](languages/java.md)
- [Python](languages/python.md)
