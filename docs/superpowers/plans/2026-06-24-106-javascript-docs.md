# JavaScript Language Extension Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add student-facing documentation for the JavaScript language extension and restructure per-language docs into a scalable per-language page pattern.

**Architecture:** Create a `docs/language-guide/languages/` directory with one self-contained page per language (JavaScript, Java, Python). Slim `docs/language-guide/semantic.md` to language-agnostic concepts with links to the per-language pages. Add CLI command reference pages for `plcc-javascript-emit` and `plcc-javascript-run`. Update nav and the language-extensions guide.

**Tech Stack:** MkDocs (static site), Markdown, MkDocs Material (tabbed blocks use `=== "Tab"` syntax).

## Global Constraints

- Node.js minimum version: 18 or later (generated code uses ES6 classes, static class fields, CommonJS).
- Java minimum version: JDK 21 or later (from `quick-start.md`).
- Python minimum version: 3.12 or later (from `quick-start.md`).
- JavaScript language tag in spec: `javascript` (lowercase).
- Java language tag in spec: `Java` (capital J, from fixture `trivial-java.plcc`).
- Python language tag in spec: `Python` (capital P, from fixture `arith.plcc`).
- All per-language pages follow the exact same section order (see Task 1).
- The canonical example grammar is identical across all language pages; only the semantic section changes.
- All files in a JavaScript emit output directory are overwritten on every `plcc-javascript-emit` run.
- No `plcc-javascript-build` command exists; `plcc-lang-build` exits silently when no build command is found.

---

## Canonical Example (used in all language pages)

This grammar is written to `spec.plcc` and referenced throughout the plan.

```text
token NUM   '\d+'
token PLUS  '\+'
skip  SPACE '\s+'
%
<Prog>       **= <Exp>
<Exp:AddExp> ::= <Exp:left> PLUS <Exp:right>
<Exp:NumExp> ::= <NUM>
```

Constructs exercised:

| Construct | Location |
| --- | --- |
| Arbno (zero or more) | `<Prog> **= <Exp>` → field `expList` |
| Abstract non-terminal (alternatives, no constructor) | `<Exp>` (implied by `:AddExp`/`:NumExp` variants) |
| Concrete non-terminal with named non-terminal fields | `<Exp:AddExp>` — `left`, `right` named to avoid collision |
| Captured terminal field | `<Exp:NumExp> ::= <NUM>` → field `num` |
| Uncaptured terminal | `PLUS` in `<Exp:AddExp>` — matched but not stored |

---

## File Map

| Action | Path |
| --- | --- |
| Create | `docs/language-guide/languages/javascript.md` |
| Create | `docs/language-guide/languages/java.md` |
| Create | `docs/language-guide/languages/python.md` |
| Create | `docs/cli/commands/plcc-javascript-emit.md` |
| Create | `docs/cli/commands/plcc-javascript-run.md` |
| Modify | `docs/language-guide/semantic.md` |
| Modify | `docs/cli/guide/language-extensions.md` |
| Modify | `mkdocs.yml` |

---

## Task 1: Create `docs/language-guide/languages/javascript.md`

**Files:**
- Create: `docs/language-guide/languages/javascript.md`

**Note:** `docs/language-guide/languages/` does not exist yet. Create it as part of this task.

- [ ] **Step 1: Create the file with full content**

Write `docs/language-guide/languages/javascript.md` with exactly this content:

````markdown
# JavaScript

## Prerequisites

Node.js 18 or later. Install from [nodejs.org](https://nodejs.org).

Verify your installation:

```bash
node --version
```

## Enabling in a spec

Add a bare `%` separator after the syntactic section, then write `javascript` on the first non-blank line:

```text
%
javascript
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
javascript

Prog
%%%
_run() {
    return this.expList.map(exp => String(exp.eval())).join('\n');
}
%%%

AddExp
%%%
eval() {
    return this.left.eval() + this.right.eval();
}
%%%

NumExp
%%%
eval() {
    return parseInt(this.num.lexeme);
}
%%%
```

Running this with `echo "1 + 2" | plcc-rep` prints `3`.

## BNF to JavaScript constructs

| Grammar construct | JavaScript | Example from spec |
| --- | --- | --- |
| Concrete non-terminal rule | ES6 class with constructor and fields | `<Exp:NumExp> ::= <NUM>` |
| Abstract non-terminal (has alternatives) | ES6 class, no constructor | `<Exp>` |
| Named non-terminal field (`:name` on RHS) | `this.name` — instance of that class | `<Exp:left>` → `this.left` |
| Captured terminal (`<TOKEN>`) | `this.name` — a `Token` | `<NUM>` → `this.num` |
| Token string value | `.lexeme` on the token | `this.num.lexeme` → `"42"` |
| Uncaptured terminal (no angle brackets) | Not stored, no field | `PLUS` in `<Exp:AddExp>` |
| Arbno (`**=`) | Array field named `<symbol>List` | `<Prog> **= <Exp>` → `this.expList` |

Without explicit `:name` on a RHS symbol, the field name is the symbol name lowercased (e.g., `<Exp>` → `exp`, `<NUM>` → `num`). Use explicit names when two RHS symbols would produce the same field name.

## Fragment kinds

Fragments inject code at specific locations in the generated file. Use `ClassName:kind` to name the target class and location.

| Kind | Where injected | Typical use |
| --- | --- | --- |
| `top` | Before all `require` lines | File-level constants, `'use strict'` |
| `import` | After generated `require` lines, before the class | Additional `require` calls |
| `init` | Inside the constructor, after field assignments | Initialize extra instance state |
| `body` | Inside the class body | Methods |
| `file` | Replaces the entire file | Standalone helper modules |

`body` is the default when no kind is given (plain `ClassName` with no colon).

JavaScript has no `class` hook. JavaScript classes do not support interface declarations or multiple inheritance, so there is nothing to inject into the class declaration line.

### Example

```text
NumExp:import
%%%
const { MathHelper } = require('./MathHelper');
%%%

NumExp
%%%
eval() {
    return MathHelper.parse(this.num.lexeme);
}
%%%

MathHelper:file
%%%
class MathHelper {
    static parse(s) { return parseInt(s, 10); }
}
module.exports = { MathHelper };
%%%
```

## `_run` entry point

`_run()` is called by the runtime on the root node of each parsed tree. Define it on your start class (the class derived from the first grammar rule — `Prog` in the quick reference example).

```javascript
Prog
%%%
_run() {
    // Compute and return a value, or return undefined to produce no output.
    return this.expList.map(exp => String(exp.eval())).join('\n');
}
%%%
```

The return value is converted to a string and printed by `plcc-rep`. Return `undefined` (or nothing) to suppress output for that input.

The default `_Start._run()` prints `String(this)` to stdout. Override it to replace the default behavior entirely.

## Referencing other generated classes

Generated files use CommonJS modules. To use a sibling generated class from semantic code, require it with an `import` fragment:

```text
MyClass:import
%%%
const { OtherClass } = require('./OtherClass');
%%%
```

Within the same generated class file, sibling generated classes are not automatically visible — you must require them explicitly.

## Generated output

`plcc-javascript-emit` writes the following to `--output=DIR`. **All files are overwritten on every run.**

```
DIR/
  main.js           — entry point; reads parse tree JSON, calls _run()
  _Start.js         — default base for the start class
  Prog.js           — one .js file per class from the grammar
  AddExp.js
  NumExp.js
  runtime/
    base.js         — Node and Token base classes
    registry.js     — class registry used by deserialization
    deserialize.js  — tree deserialization
```

Do not edit these files directly. Put all custom code in the spec's semantic section.

## Running the quick reference example

Save the spec above as `spec.plcc`. In the same directory:

```bash
echo "1 + 2" | plcc-rep
```

Expected output:

```text
3
```

`plcc-rep` auto-discovers `spec.plcc`, emits the interpreter to a temporary directory, and runs it.

## Commands

| Command | What it does |
| --- | --- |
| [`plcc-javascript-emit`](../../cli/commands/plcc-javascript-emit.md) | Writes `.js` class files and a `main.js` entry point to the output directory |
| [`plcc-javascript-run`](../../cli/commands/plcc-javascript-run.md) | Runs `main.js` with `node`; requires Node.js on `PATH` |

No build step is required — Node.js does not need a compilation step, so `plcc-lang-build` skips silently.

## Restrictions

- No `class` hook (unlike Python). There is no equivalent in JavaScript.
- Generated code uses CommonJS (`require` / `module.exports`). ESM (`import` / `export`) is not supported.
- All output files are overwritten on every emit run — do not edit them directly.
- Sibling generated classes are not automatically in scope; require them explicitly with an `import` fragment.

## Tips

- Use `console.error(...)` for debug output. The runtime reads `_run()`'s return value and passes it to `plcc-rep` via stdout; writing to stdout from inside `_run()` will corrupt the output.
- `this.num.lexeme` is always a string. Use `parseInt(this.num.lexeme)` or `parseFloat(this.num.lexeme)` to get a numeric value.
- Abstract classes (`Exp` in the quick reference example) are never instantiated. You cannot add a constructor to them via fragments.
- The arbno field name is always `<lowerCasedSymbol>List`. For `<Prog> **= <Exp>`, the field is `this.expList`.
````

- [ ] **Step 2: Commit**

```bash
git add docs/language-guide/languages/javascript.md
git commit -m "docs: add JavaScript language extension page"
```

---

## Task 2: Create `docs/language-guide/languages/java.md`

**Files:**
- Create: `docs/language-guide/languages/java.md`
- Reference: `docs/language-guide/semantic.md` (existing Java tabs to reorganize)
- Reference: `docs/cli/commands/plcc-java-emit.md`, `plcc-java-build.md`, `plcc-java-run.md`

- [ ] **Step 1: Create the file with full content**

Write `docs/language-guide/languages/java.md` with exactly this content:

````markdown
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
| Named non-terminal field (`:name` on RHS) | `this.name` — instance of that class | `<Exp:left>` → `left` |
| Captured terminal (`<TOKEN>`) | `this.name` — a `Token` | `<NUM>` → `num` |
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
````

- [ ] **Step 2: Commit**

```bash
git add docs/language-guide/languages/java.md
git commit -m "docs: add Java language extension page"
```

---

## Task 3: Create `docs/language-guide/languages/python.md`

**Files:**
- Create: `docs/language-guide/languages/python.md`
- Reference: `docs/language-guide/semantic.md` (existing Python tabs to reorganize)
- Reference: `docs/cli/commands/plcc-python-emit.md`, `plcc-python-run.md`

- [ ] **Step 1: Create the file with full content**

Write `docs/language-guide/languages/python.md` with exactly this content:

````markdown
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

- Generated files are overwritten on every emit run — do not edit them directly.
- Sibling generated classes are not automatically in scope; import them explicitly with an `import` fragment.

## Tips

- Use `sys.stderr.write(...)` (after `import sys`) for debug output so it does not interfere with the output protocol.
- `self.num.lexeme` is always a string. Use `int(self.num.lexeme)` or `float(self.num.lexeme)` to get a numeric value.
- Abstract classes have no constructor. You can add methods to them via `body` fragments; subclasses inherit them.
- The `class` hook enables multiple inheritance. Use it to add a base class: `MyClass:class\n%%%\n, MyMixin\n%%%`.
````

- [ ] **Step 2: Commit**

```bash
git add docs/language-guide/languages/python.md
git commit -m "docs: add Python language extension page"
```

---

## Task 4: Create CLI command reference pages for JavaScript

**Files:**
- Create: `docs/cli/commands/plcc-javascript-emit.md`
- Create: `docs/cli/commands/plcc-javascript-run.md`
- Reference: `docs/cli/commands/plcc-python-emit.md` (pattern to follow)

- [ ] **Step 1: Create `plcc-javascript-emit.md`**

Write `docs/cli/commands/plcc-javascript-emit.md` with exactly this content:

```markdown
# plcc-javascript-emit

Emit a JavaScript interpreter from model JSON. Reads model JSON from stdin and
writes `.js` class files and a `main.js` entry point to the output directory.

Called by [`plcc-lang-emit --target=javascript`](plcc-lang-emit.md).

Requires Node.js 18 or later on `PATH` to run the emitted interpreter.

## Usage

```text
plcc-javascript-emit --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory to write generated JavaScript files into. Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-spec spec.plcc | plcc-model | plcc-javascript-emit --output=build/javascript
```
```

- [ ] **Step 2: Create `plcc-javascript-run.md`**

Write `docs/cli/commands/plcc-javascript-run.md` with exactly this content:

```markdown
# plcc-javascript-run

Run a generated JavaScript interpreter. Reads parse tree JSON from stdin and
passes it to `main.js` in the output directory using `node`.

Called by [`plcc-lang-run --target=javascript`](plcc-lang-run.md).

Requires Node.js 18 or later on `PATH`.

## Usage

```text
plcc-javascript-run --output=DIR [-v ...] [options]
```

## Arguments and Options

| Option | Description |
|---|---|
| `--output=DIR` | Directory containing generated JavaScript files (from `plcc-javascript-emit`). Required. |
| `-h`, `--help` | Show usage and exit. |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`). |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json`. |

## Examples

```bash
plcc-javascript-run --output=build/javascript
```
```

- [ ] **Step 3: Commit**

```bash
git add docs/cli/commands/plcc-javascript-emit.md docs/cli/commands/plcc-javascript-run.md
git commit -m "docs: add plcc-javascript-emit and plcc-javascript-run command reference pages"
```

---

## Task 5: Slim `docs/language-guide/semantic.md`

**Files:**
- Modify: `docs/language-guide/semantic.md`

Remove all language-specific tabbed examples. Replace with language-agnostic concepts and a "Choose your language" section at the bottom linking to the per-language pages. The per-language pages now own all language-specific examples.

- [ ] **Step 1: Replace the file content entirely**

Overwrite `docs/language-guide/semantic.md` with exactly this content:

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add docs/language-guide/semantic.md
git commit -m "docs: slim semantic.md to concepts, link to per-language pages"
```

---

## Task 6: Update `docs/cli/guide/language-extensions.md`

**Files:**
- Modify: `docs/cli/guide/language-extensions.md`

Add a `## plcc-javascript` section and update the intro sentence to mention JavaScript.

- [ ] **Step 1: Update the intro sentence**

Change the first paragraph from:

```markdown
Language extensions provide the emit, build, and run steps for a specific
target language. plcc-ng ships with Python and Java support.
```

to:

```markdown
Language extensions provide the emit, build, and run steps for a specific
target language. plcc-ng ships with Python, Java, and JavaScript support.
```

- [ ] **Step 2: Add the `## plcc-javascript` section**

Append this section at the end of the file (after `## plcc-java`):

```markdown

## plcc-javascript

Emits a JavaScript interpreter from model JSON, then runs it with Node.js.
No build step is required.

| Command | What it does |
| --- | --- |
| [`plcc-javascript-emit`](../commands/plcc-javascript-emit.md) | Writes `.js` class files and a `main.js` entry point to the output directory |
| [`plcc-javascript-run`](../commands/plcc-javascript-run.md) | Runs `main.js` with `node`; requires Node.js 18+ on `PATH` |

No build step is required for JavaScript — `plcc-lang-build` exits silently if
`plcc-javascript-build` is not found.
```

- [ ] **Step 3: Commit**

```bash
git add docs/cli/guide/language-extensions.md
git commit -m "docs: add plcc-javascript section to language-extensions guide"
```

---

## Task 7: Update `mkdocs.yml` and verify build

**Files:**
- Modify: `mkdocs.yml`

Add the `Languages` sub-nav under `Language Guide` and add the two new JS command docs under `All Commands`.

- [ ] **Step 1: Add Languages sub-nav under Language Guide**

In `mkdocs.yml`, find the `Language Guide:` nav block. It currently looks like:

```yaml
  - Language Guide:
    - Overview: language-guide/index.md
    - Lexical Section: language-guide/lexical.md
    - Syntactic Section: language-guide/syntactic.md
    - Semantic Section: language-guide/semantic.md
    - Examples: language-guide/examples.md
```

Replace it with:

```yaml
  - Language Guide:
    - Overview: language-guide/index.md
    - Lexical Section: language-guide/lexical.md
    - Syntactic Section: language-guide/syntactic.md
    - Semantic Section: language-guide/semantic.md
    - Languages:
      - JavaScript: language-guide/languages/javascript.md
      - Java: language-guide/languages/java.md
      - Python: language-guide/languages/python.md
    - Examples: language-guide/examples.md
```

- [ ] **Step 2: Add JS command docs to All Commands**

In `mkdocs.yml`, find the `All Commands:` block. Add these two entries in alphabetical order alongside the existing command docs:

```yaml
      - plcc-javascript-emit: cli/commands/plcc-javascript-emit.md
      - plcc-javascript-run: cli/commands/plcc-javascript-run.md
```

They belong between `plcc-java-run` and `plcc-lang-build` alphabetically.

- [ ] **Step 3: Verify the site builds**

```bash
python -m mkdocs build --strict 2>&1 | tail -20
```

Expected: build completes with no errors. If there are broken link warnings, fix them before committing.

- [ ] **Step 4: Commit**

```bash
git add mkdocs.yml
git commit -m "docs: add Languages nav and JavaScript command docs to mkdocs.yml"
```
