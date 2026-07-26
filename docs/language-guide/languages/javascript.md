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
token MINUS '-'
skip  SPACE '\s+'
%
<Prog>     **= <Expr>
<Expr>     ::= <NUM:left> <Op:op> <NUM:right>
<Op:AddOp> ::= PLUS
<Op:SubOp> ::= MINUS
%
javascript

Expr
%%%
eval() {
    return this.op.apply(parseInt(this.left.lexeme), parseInt(this.right.lexeme));
}
%%%

Prog
%%%
_run() {
    return this.exprList.map(expr => String(expr.eval())).join('\n');
}
%%%

AddOp
%%%
apply(left, right) {
    return left + right;
}
%%%

SubOp
%%%
apply(left, right) {
    return left - right;
}
%%%
```

Running this with `echo "1 + 2" | plcc-rep` prints `3`.

## BNF to JavaScript constructs

| Grammar Construct | Example from spec | JavaScript Construct | Example based on spec |
| --- | --- | --- | --- |
| Concrete rule (LHS, no alt name) — generates one class | `<Prog>` in `<Prog> **= <Expr>` | ES6 class with constructor and fields | `class Prog extends _Start { constructor(exprList) { ... } }` |
| Alternative rule (LHS, with alt name) — base nonterminal becomes abstract | `<Op:AddOp>` in `<Op:AddOp> ::= PLUS` | ES6 class extending the base nonterminal | `class AddOp extends Op { ... }` |
| Named non-terminal (RHS) | `<Op:op>` in `<Expr> ::= <NUM:left> <Op:op> <NUM:right>` | `this.op` — an `Op` instance | `this.op.apply(left, right)` |
| Captured terminal (RHS) | `<NUM:left>` | `this.left` — a `Token`; `.lexeme` for the string value | `parseInt(this.left.lexeme)` |
| Uncaptured terminal (RHS) | `PLUS` in `<Op:AddOp> ::= PLUS` | No field generated | — |
| Arbno rule (`**=`) | `<Prog> **= <Expr>` | `this.exprList` — `Array` of `Expr` | `this.exprList.map(e => e.eval())` |

Without explicit `:name` on a RHS symbol, the field name is derived from the symbol name: a terminal is lowercased (`<NUM>` → `this.num`), and a nonterminal has just its first letter decapitalized (`<Expr>` → `this.expr`, `<OneMore>` → `this.oneMore`). Use explicit names when two RHS symbols would produce the same field name.

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
Expr:import
%%%
const { MathHelper } = require('./MathHelper');
%%%

Expr
%%%
eval() {
    return this.op.apply(MathHelper.parse(this.left.lexeme), MathHelper.parse(this.right.lexeme));
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
    return this.exprList.map(expr => String(expr.eval())).join('\n');
}
%%%
```

`_run()` must return a `string`. The runtime sends that string to `plcc-rep` as-is — it is not converted or coerced. Returning anything else (a `number`, an `array`, `undefined`, ...) raises a `specification_error`; convert explicitly (`String(x)`) if needed.

Do not print or write to stdout from inside `_run()` — that bypasses `plcc-rep`'s JSON result envelope. Plain-text mode will still show what you printed, but `plcc-rep --verbose-format=json` will not.

The default `_Start._run()` returns `String(this)`. Override it to replace the default behavior entirely.

## `LanguageError`

Throw `LanguageError` to signal a deliberate error in the defined language — a type mismatch, division by zero, or any condition your language treats as an error. `plcc-rep` prints the message and gives a fresh prompt; the session continues.

`LanguageError` is available in all generated classes without any import:

```javascript
eval() {
    throw new LanguageError("type mismatch: expected int");
}
```

Subclass it to create named error types:

```javascript
class DivisionByZeroError extends LanguageError {}
throw new DivisionByZeroError("division by zero");
```

Any other exception (not `LanguageError` or a subclass) is treated as a specification error — `plcc-rep` prints the error and exits.

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
  Expr.js
  AddOp.js
  SubOp.js
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
| [`plcc-javascript-run`](../../cli/commands/plcc-javascript-run.md) | Runs `main.js` with `node`; requires Node.js 18+ on `PATH` |

No build step is required — Node.js does not need a compilation step, so `plcc-lang-build` skips silently.

## Restrictions

- No `class` hook (unlike Java and Python). There is no equivalent in JavaScript.
- Generated code uses CommonJS (`require` / `module.exports`). ESM (`import` / `export`) is not supported.
- All output files are overwritten on every emit run — do not edit them directly.
- Sibling generated classes are not automatically in scope; require them explicitly with an `import` fragment.
- A field name that becomes a JavaScript reserved word (e.g. `<VAR>` auto-naming field `var`) is rejected by `plcc-javascript-emit` — rename the capture, e.g. `<VAR:name>`. See [Reserved words](../syntactic.md#reserved-words) for details.

## Tips

- Use `console.error(...)` for debug output. The runtime reads `_run()`'s return value and passes it to `plcc-rep` via stdout; writing to stdout from inside `_run()` will corrupt the output.
- `this.left.lexeme` is always a string. Use `parseInt(this.left.lexeme)` or `parseFloat(this.left.lexeme)` to get a numeric value.
- Abstract classes (`Op` in the quick reference example) are never instantiated. You cannot add a constructor to them via fragments.
- The arbno field name is always `<lowerCasedSymbol>List`. For `<Prog> **= <Expr>`, the field is `this.exprList`.
