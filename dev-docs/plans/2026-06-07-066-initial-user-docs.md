# Initial User Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate all "Content coming soon" stubs in `docs/` with draft content drawn from the original PLCC README, updated for plcc-ng's syntax and CLI.

**Architecture:** Batch-draft approach — write all ten pages in a fixed order (language guide → getting started → CLI → home), placing PLCC README content in its correct location and marking every divergence with `<!-- TODO: verify ... -->`. The resulting draft is a complete first pass ready for maintainer review.

**Tech Stack:** Markdown, MkDocs Material, worktree branch `docs/initial-documentation`

---

## Flagging convention

Any place where plcc-ng may differ from the original PLCC README, insert:

```html
<!-- TODO: verify this reflects plcc-ng (original PLCC used X) -->
```

These render invisibly on the site. Run `grep -r 'TODO:' docs/` to get the full review checklist after all tasks complete.

## Known differences from the PLCC README

Keep these in mind throughout — they apply to every task:

| PLCC | plcc-ng |
|------|---------|
| Grammar file named `grammar` | Grammar file named `grammar.plcc` |
| `plccmk -c grammar` | `plcc-make` |
| `scan`, `parse`, `rep` | `plcc-scan`, `plcc-parse`, `plcc-rep` |
| Always Java semantics | `% toolname Language` header selects target |
| Entry point `$run()` | Entry point `_run` |
| `<exp>SubExp ::=` (old LHS alt-name) | `<Exp:SubExp> ::=` (colon inside brackets) |
| `<exp>:rest` (old RHS field) | `<Exp:rest>` (colon inside brackets) |
| `<NUM>:num` (old terminal field) | `<NUM:num>` (colon inside brackets) |
| Nonterminals lowercase | Nonterminals PascalCase |

---

## Task 1: Language Guide Overview

**Files:**
- Modify: `docs/language-guide/index.md`

- [ ] **Step 1: Write the draft**

Replace the stub with:

```markdown
# Language Guide

A plcc-ng grammar file describes a language in three sections, separated by
lines containing a single `%`:

```text
[Lexical specification]
%
[Syntactic specification]
%
[Semantic specification]
```

| Section | What it describes | Pipeline stage it drives |
|---|---|---|
| Lexical | Token and skip rules | Scanner (`plcc-scan`) |
| Syntactic | Grammar rules (BNF) | Parser (`plcc-parse`) |
| Semantic | Target-language code embedded in generated classes | Interpreter (`plcc-rep`) |

Each stage depends on the one before it:

```
plcc-rep  →  plcc-parse  →  plcc-scan
Semantic  →  Syntactic   →  Lexical
```

You can write a grammar with only a lexical section (no `%` needed), or a
grammar with lexical and syntactic sections but no semantic section. Add
sections as your language grows.

<!-- TODO: verify that include FILENAME works in plcc-ng (original PLCC supported it) -->
External files can be included in any section using:

```
include FILENAME
```

## Pages in this guide

- [Token Rules](tokens.md) — `token` and `skip` syntax, scanning algorithm
- [Grammar Rules](grammar.md) — BNF rules, parse tree class hierarchy
- [Code Generation](code-generation.md) — embedding code, hooks, target language selection
- [Examples](examples.md) — worked examples of increasing complexity
```

- [ ] **Step 2: Commit**

```bash
cd .worktrees/docs
git add docs/language-guide/index.md
git commit -m "docs(language-guide): draft language guide overview [skip ci]"
```

---

## Task 2: Token Rules

**Files:**
- Modify: `docs/language-guide/tokens.md`

- [ ] **Step 1: Write the draft**

Replace the stub with:

```markdown
# Token Rules

The lexical section of a `.plcc` file defines what the scanner recognizes.
Each line is either a `token` rule, a `skip` rule, or a comment.

## Syntax

```text
token NAME 'pattern'
skip  NAME 'pattern'
# This is a comment
```

`token` rules emit a token when matched. `skip` rules consume input silently
(useful for whitespace and comments in the language you are implementing).

### Naming rules

Token names must be all uppercase letters, digits, and underscores, starting
with a letter:

```text
token PLUS   '\+'
token WHOLE  '\d+'
skip  SPACE  '\s+'
skip  COMMENT '#[^\n]*'
```

### Patterns

Patterns are regular expressions enclosed in single or double quotes.
They follow Java `Pattern` syntax.

<!-- TODO: verify plcc-ng uses Java Pattern syntax or Python re syntax -->

A few common patterns:

| Pattern | Matches |
|---|---|
| `'\d+'` | One or more digits |
| `'\s+'` | One or more whitespace characters |
| `'[a-zA-Z_]\w*'` | An identifier |
| `'\+'` | A literal `+` (escaped) |
| `'"[^"]*"'` | A double-quoted string |

Patterns **cannot match across newlines**.

## Scan algorithm

The scanner processes input left-to-right, one rule at a time:

1. Find all rules whose pattern matches a non-empty prefix of the remaining input.
2. If none match, emit a lexical error and stop.
3. Among matching rules, prefer `skip` rules over `token` rules.
   Apply the first-listed skip rule that matches.
4. Among matching `token` rules, choose the one with the longest match.
   Break ties by taking the first-listed rule.
5. Remove the matched text from the input. If it was a `token` rule, emit the token.
6. Repeat from step 1.

The scanner emits tokens one at a time. The parser reads them on demand.
```

- [ ] **Step 2: Commit**

```bash
cd .worktrees/docs
git add docs/language-guide/tokens.md
git commit -m "docs(language-guide): draft token rules page [skip ci]"
```

---

## Task 3: Grammar Rules

**Files:**
- Modify: `docs/language-guide/grammar.md`

- [ ] **Step 1: Write the draft**

Replace the stub with:

```markdown
# Grammar Rules

The syntactic section of a `.plcc` file defines the grammar of your language
in a BNF-flavored notation. Each rule maps a non-terminal to a sequence of
symbols on its right-hand side.

## Naming conventions

| Kind | Format | Example |
|---|---|---|
| Non-terminal (class name) | PascalCase, angle-bracketed | `<Expr>`, `<Program>` |
| Terminal (token name) | UPPER_CASE | `PLUS`, `NUM` |
| Field name (captured symbol) | camelCase | `expr`, `num`, `rest` |
| Alt-name (subclass) | PascalCase | `AddExpr`, `NilRest` |

## Basic rules

```text
<Program> ::= <Expr:expr>
<Expr>    ::= <Term:term> <ExprRest:rest>
<Term>    ::= <NUM:num>
```

Each rule becomes a class. Captured symbols (those inside `<...>` or with a
field name) become instance variables on that class.

### Capturing terminals

Wrap a terminal in angle brackets and give it a field name to capture it:

```text
<Term> ::= <NUM:num>   # captures NUM as field `num`
<Term> ::= NUM         # matches NUM but does not capture it
```

### Capturing non-terminals

Give a non-terminal a field name with `:fieldname`:

```text
<Program> ::= <Expr:expr>   # captures Expr as field `expr`
<Program> ::= <Expr>        # matches Expr but does not capture it
```

## Alternative rules and subclasses

When a non-terminal has multiple rules, each alternative gets an alt-name
that becomes a subclass:

```text
<Expr:LitExpr> ::= <NUM:num>
<Expr:AddExpr> ::= PLUS <Expr:left> <Expr:right>
```

This generates:

```
abstract class Expr
class LitExpr extends Expr  { Token num; }
class AddExpr extends Expr  { Expr left; Expr right; }
```

<!-- TODO: verify the exact generated class hierarchy for plcc-ng (may differ from PLCC's Java) -->

The first rule in the file defines the start symbol.

## Repetition rules

The `**=` form matches zero or more occurrences of a pattern, with an optional
separator:

```text
<Args>    **= <Expr:expr>
<ArgList> **= <Expr:expr> +COMMA
```

Captured symbols become parallel lists:

```text
<Args> **= <Expr:expr>
# generates: Args { List<Expr> exprList; }

<Pairs> **= <WHOLE:x> <WHOLE:y> +COMMA
# generates: Pairs { List<Token> xList; List<Token> yList; }
```

The `+SEPARATOR` token is consumed between repetitions but not captured.

<!-- TODO: verify repetition rule syntax and generated field names in plcc-ng -->

## Parse algorithm

plcc-ng uses recursive-descent LL(1) parsing. Each non-terminal gets a parse
method. The method reads the next token and dispatches to the correct
alternative, then matches the RHS left-to-right: tokens are consumed directly,
non-terminals call their own parse methods.

A grammar is valid only if it is LL(1): each alternative must be
distinguishable by a single lookahead token. plcc-ng reports LL(1) conflicts
when it detects them.
```

- [ ] **Step 2: Commit**

```bash
cd .worktrees/docs
git add docs/language-guide/grammar.md
git commit -m "docs(language-guide): draft grammar rules page [skip ci]"
```

---

## Task 4: Code Generation

**Files:**
- Modify: `docs/language-guide/code-generation.md`

- [ ] **Step 1: Write the draft**

Replace the stub with:

```markdown
# Code Generation

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
|---|---|
| `ClassName:top` | Top of the generated file |
| `ClassName:import` | Import section |
| `ClassName:class` | Class declaration (extend/implement) |
| `ClassName:init` | Constructor / initializer |

<!-- TODO: verify hook syntax and availability in plcc-ng -->

### Example

```text
WholeExp:import
%%%
from collections import defaultdict
%%%

WholeExp
%%%
seen = defaultdict(int)

def eval(self):
    x = int(self.whole.lexeme)
    if self.seen[x]:
        print(f"Duplicate: {x}")
    self.seen[x] += 1
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
```

- [ ] **Step 2: Commit**

```bash
cd .worktrees/docs
git add docs/language-guide/code-generation.md
git commit -m "docs(language-guide): draft code generation page [skip ci]"
```

---

## Task 5: Examples

**Files:**
- Modify: `docs/language-guide/examples.md`

- [ ] **Step 1: Write the draft**

Replace the stub with:

```markdown
# Examples

## Example: Subtraction language

This end-to-end example implements a small expression language that evaluates
subtraction expressions. It walks through all three grammar sections and shows
the output of each pipeline stage.

### Sample programs

Create a file named `samples`:

```text
3
-(3,2)
-(-(4,1), -(3,2))
```

### Grammar file

Create `subtract.plcc`:

```text
# Subtraction language
skip WHITESPACE '\s+'
token WHOLE     '\d+'
token MINUS     '\-'
token LP        '\('
token RP        '\)'
token COMMA     ','
%
<Prog>         ::= <Exp:exp>
<Exp:WholeExp> ::= <WHOLE:whole>
<Exp:SubExp>   ::= MINUS LP <Exp:exp1> COMMA <Exp:exp2> RP
%
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

### Build

```bash
plcc-make -g subtract.plcc
```

<!-- TODO: verify plcc-make output format (below adapted from PLCC's plccmk output) -->
Expected output:

```text
plcc-ng 0.39.2 | subtract.plcc
Nonterminals (* indicates start symbol):
  <Exp>
 *<Prog>

Abstract classes:
  Exp
```

### Scanner

```bash
plcc-scan -g subtract.plcc samples
```

<!-- TODO: verify plcc-scan output format -->
Expected output:

```text
   1: WHOLE '3'
   3: MINUS '-'
   3: LP '('
   3: WHOLE '3'
   3: COMMA ','
   3: WHOLE '2'
   3: RP ')'
   5: MINUS '-'
   5: LP '('
   5: MINUS '-'
   5: LP '('
   5: WHOLE '4'
   5: COMMA ','
   5: WHOLE '1'
   5: RP ')'
   5: COMMA ','
   5: MINUS '-'
   5: LP '('
   5: WHOLE '3'
   5: COMMA ','
   5: WHOLE '2'
   5: RP ')'
   5: RP ')'
```

### Parser

```bash
plcc-parse -g subtract.plcc samples
```

<!-- TODO: verify plcc-parse output format and flags -->
Expected output:

```text
<Prog>
| <Exp:WholeExp>
| | WHOLE "3"
<Prog>
| <Exp:SubExp>
| | MINUS "-"
| | LP "("
| | <Exp:WholeExp>
| | | WHOLE "3"
| | COMMA ","
| | <Exp:WholeExp>
| | | WHOLE "2"
| | RP ")"
<Prog>
| <Exp:SubExp>
...
```

### Interpreter

```bash
plcc-rep -g subtract.plcc --tool=subtract samples
```

<!-- TODO: verify plcc-rep output format -->
Expected output:

```text
3
1
2
```
```

- [ ] **Step 2: Commit**

```bash
cd .worktrees/docs
git add docs/language-guide/examples.md
git commit -m "docs(language-guide): draft examples page [skip ci]"
```

---

## Task 6: Getting Started

**Files:**
- Modify: `docs/getting-started.md`

- [ ] **Step 1: Write the draft**

Replace the stub with:

```markdown
# Getting Started

## Prerequisites

- Python 3.12 or later

<!-- TODO: note whether Java is required for any default workflow, and which version -->

Verify your Python version:

```bash
python3 --version
```

## Install

```bash
pip install plcc-ng
```

Verify the installation:

```bash
plcc-make --help
```

## Quickstart

This quickstart builds a minimal language that recognizes integers.

**Step 1.** Create a grammar file `hello.plcc`:

```text
token NUM '\d+'
skip  WS  '\s+'
%
<Program> ::= <NUM:num>
```

**Step 2.** Build:

```bash
plcc-make -g hello.plcc
```

**Step 3.** Scan some input:

```bash
echo "42" | plcc-scan -g hello.plcc
```

<!-- TODO: verify output format -->
Expected:

```text
   1: NUM '42'
```

**Step 4.** Parse some input:

```bash
echo "42" | plcc-parse -g hello.plcc
```

<!-- TODO: verify output format -->
Expected:

```text
<Program>
| NUM "42"
```

From here, see the [Language Guide](language-guide/index.md) to add grammar
rules and semantic code, or the [CLI Reference](cli/index.md) for all available
commands.
```

- [ ] **Step 2: Commit**

```bash
cd .worktrees/docs
git add docs/getting-started.md
git commit -m "docs: draft getting started page [skip ci]"
```

---

## Task 7: CLI Overview

**Files:**
- Modify: `docs/cli/index.md`

- [ ] **Step 1: Write the draft**

Replace the stub with:

```markdown
# CLI Reference

plcc-ng provides two groups of commands: **Level 0 primitives** and
**Level 2 orchestrators**.

## Level 0 primitives

Low-level commands that each perform one step of the pipeline. They read and
write JSON, making them composable with other tools.

| Command | Purpose |
|---|---|
| [`plcc-spec`](primitives.md#plcc-spec) | Parse and validate a `.plcc` grammar file; emit spec JSON |
| [`plcc-tokens`](primitives.md#plcc-tokens) | Tokenize source files given a spec JSON; emit token JSONL |
| [`plcc-trees`](primitives.md#plcc-trees) | Parse token JSONL using an LL(1) table; emit parse trees |
| [`plcc-model`](primitives.md#plcc-model) | Transform spec JSON into a language-neutral code model |
| [`plcc-lang-emit`](primitives.md#plcc-lang-emit) | Dispatch to the appropriate language emitter |
| [`plcc-diagram`](primitives.md#plcc-diagram) | Generate a class diagram from a grammar file |

## Level 2 orchestrators

High-level commands that compose the primitives for common workflows.

| Command | Purpose |
|---|---|
| [`plcc-make`](orchestrators.md#plcc-make) | Build a PLCC project from a grammar file |
| [`plcc-scan`](orchestrators.md#plcc-scan) | Tokenize source input and print tokens |
| [`plcc-parse`](orchestrators.md#plcc-parse) | Parse source input and print the parse tree |
| [`plcc-rep`](orchestrators.md#plcc-rep) | Read-eval-print loop using generated semantics |

## Common options

All commands accept:

| Option | Effect |
|---|---|
| `-h`, `--help` | Show usage and exit |
| `-v` | Increase verbosity (repeat for more: `-v`, `-vv`, `-vvv`) |
| `--verbose-format=FMT` | Verbosity output format: `text` or `json` |

## Grammar memory

The Level 2 orchestrators remember the grammar path between invocations.
Pass `-g <path>` once; subsequent commands in the same directory use the same
grammar automatically.

<!-- TODO: verify grammar memory behavior (sticky grammar) and where it is stored -->
```

- [ ] **Step 2: Commit**

```bash
cd .worktrees/docs
git add docs/cli/index.md
git commit -m "docs(cli): draft CLI overview page [skip ci]"
```

---

## Task 8: Level 0 Primitives

**Files:**
- Modify: `docs/cli/primitives.md`

- [ ] **Step 1: Write the draft**

Replace the stub with:

```markdown
# Level 0 Primitives

These commands each perform one step of the pipeline. They are the building
blocks that the [Level 2 orchestrators](orchestrators.md) use internally.

---

## plcc-spec

Parse, validate, and print a PLCC grammar file as JSON.

```text
plcc-spec [-v ...] [options] FILE
```

| Argument/Option | Description |
|---|---|
| `FILE` | `.plcc` grammar file. Use `-` to read from stdin. |
| `--no-json` | Validate only; do not print JSON to stdout. |

**Example:**

```bash
plcc-spec grammar.plcc
```

---

## plcc-tokens

Tokenize source files given a spec JSON file; emit token JSONL.

```text
plcc-tokens [-v ...] [options] SPEC_JSON [SOURCE ...]
```

| Argument/Option | Description |
|---|---|
| `SPEC_JSON` | Path to spec JSON (output of `plcc-spec`). |
| `SOURCE` | Source files to tokenize. Use `-` for stdin. Defaults to stdin. |
| `-t`, `--trace` | Include regex, source line, attempts; emit skip records. |
| `--source-name=LABEL` | Override the source label for stdin. |

**Example:**

```bash
plcc-spec grammar.plcc | plcc-tokens - samples
```

---

## plcc-trees

Dispatch to a parser plugin. Reads token JSONL; emits a parse tree.

```text
plcc-trees [-v ...] [options] --ll1=LL1_JSON
```

| Option | Description |
|---|---|
| `--ll1=LL1_JSON` | Path to LL(1) analysis JSON (required). |
| `--parser=KIND` | Parser plugin to use. Default: `table`. |
| `-t`, `--trace` | Forward trace flag to the parser plugin. |

<!-- TODO: document how to obtain LL1_JSON (output of plcc-ll1) -->

---

## plcc-model

Transform spec JSON into a language-neutral code model.

```text
plcc-model [-v ...] [options] [SPEC_JSON]
```

| Argument | Description |
|---|---|
| `SPEC_JSON` | Path to spec JSON. Use `-` or omit to read from stdin. |

**Example:**

```bash
plcc-spec grammar.plcc | plcc-model
```

---

## plcc-lang-emit

Dispatch to the appropriate language emitter.

```text
plcc-lang-emit [-v ...] --target=LANG --output=DIR
```

| Option | Description |
|---|---|
| `--target=LANG` | Target language (e.g. `Python`, `Java`). |
| `--output=DIR` | Directory to write output files into. |

**Example:**

```bash
plcc-spec grammar.plcc | plcc-model | plcc-lang-emit --target=Python --output=out/
```

---

## plcc-diagram

Generate and display a class diagram from a PLCC grammar file.

```text
plcc-diagram [-v ...] [options]
```

| Option | Description |
|---|---|
| `-g PATH`, `--grammar=PATH` | Grammar file. Remembers across invocations. Defaults to `grammar.plcc`. |
| `--format=FMT` | Diagram format. Default: `plantuml`. |
| `--no-banner` | Suppress the version and grammar banner. |

**Example:**

```bash
plcc-diagram -g mylang.plcc
```
```

- [ ] **Step 2: Commit**

```bash
cd .worktrees/docs
git add docs/cli/primitives.md
git commit -m "docs(cli): draft primitives page [skip ci]"
```

---

## Task 9: Level 2 Orchestrators

**Files:**
- Modify: `docs/cli/orchestrators.md`

- [ ] **Step 1: Write the draft**

Replace the stub with:

```markdown
# Level 2 Orchestrators

These commands compose the [Level 0 primitives](primitives.md) for the most
common workflows. They are the commands students use day-to-day.

---

## plcc-make

Build a PLCC project from a grammar file.

```text
plcc-make [-v ...] [options]
```

| Option | Description |
|---|---|
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. Defaults to `grammar.plcc` on first use. |
| `--through=LEVEL` | Build up to this level: `scan`, `parse`, `model`, or `all`. Default: `all`. |
| `--no-banner` | Suppress the version and grammar banner. |

**Example:**

```bash
plcc-make -g subtract.plcc
```

Run `plcc-make` again after editing your grammar to rebuild.

---

## plcc-scan

Tokenize source input and print tokens in human-readable format.

```text
plcc-scan [-v ...] [options] [SOURCE ...]
```

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to tokenize. Reads stdin if none given. |
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. |
| `-t`, `--trace` | Show detailed scanning output. |
| `--no-banner` | Suppress the version and grammar banner. |

**Example:**

```bash
plcc-scan -g subtract.plcc samples
echo "42" | plcc-scan
```

---

## plcc-parse

Parse source input and print the parse tree in human-readable format.

```text
plcc-parse [-v ...] [options] [SOURCE ...]
```

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to parse. Reads stdin if none given. |
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. |
| `--no-banner` | Suppress the version and grammar banner. |

**Example:**

```bash
plcc-parse -g subtract.plcc samples
echo "42" | plcc-parse
```

---

## plcc-rep

REPL — read, eval, print loop for a PLCC grammar.

```text
plcc-rep [-v ...] [options] [SOURCE ...]
```

| Argument/Option | Description |
|---|---|
| `SOURCE` | Source files to evaluate before entering interactive mode. |
| `-g PATH`, `--grammar=PATH` | Grammar to build from. Remembered across invocations. |
| `--tool=NAME` | Semantic section to run. Inferred automatically when only one exists. |
| `--no-banner` | Suppress the version and grammar banner. |

**Example:**

```bash
# Run the 'subtract' semantic section against samples, then enter interactive mode
plcc-rep -g subtract.plcc --tool=subtract samples

# Evaluate a file only (no interactive mode)
plcc-rep -g subtract.plcc samples < /dev/null
```

<!-- TODO: verify how to suppress interactive mode (< /dev/null or EOF behavior) -->
```

- [ ] **Step 2: Commit**

```bash
cd .worktrees/docs
git add docs/cli/orchestrators.md
git commit -m "docs(cli): draft orchestrators page [skip ci]"
```

---

## Task 10: Home Page

**Files:**
- Modify: `docs/index.md`

- [ ] **Step 1: Write the draft**

Replace the stub with:

```markdown
# plcc-ng

plcc-ng is a tool for teaching and learning programming language concepts.
It is a reimagining of [PLCC](https://github.com/ourPLCC/plcc).

You write a grammar file describing your language's tokens, grammar rules,
and semantics. plcc-ng generates a scanner, parser, and interpreter for you.

## Where to start

**Installing for the first time?**
→ [Getting Started](getting-started.md) — install and run your first grammar in under 10 minutes.

**Writing or debugging a grammar file?**
→ [Language Guide](language-guide/index.md) — token rules, BNF syntax, code generation, worked examples.

**Looking up a command?**
→ [CLI Reference](cli/index.md) — every command, every flag.

**Evaluating plcc-ng for a course?**
→ [Instructor Guide](instructor-guide/index.md) — what it teaches, what students need to know, how to structure assignments.

## Install

```bash
pip install plcc-ng
```

Requires Python 3.12 or later.

<!-- TODO: add version badge and license badge per documentation design spec -->

## Community

- [Discord server](https://discord.gg/EVtNSxS9E2)
- [Changelog](changelog.md)
- [GitHub](https://github.com/ourPLCC/plcc-ng)
```

- [ ] **Step 2: Commit**

```bash
cd .worktrees/docs
git add docs/index.md
git commit -m "docs: draft home page [skip ci]"
```

---

## After all tasks: review pass

Run this to see every flagged item:

```bash
grep -rn 'TODO:' docs/
```

Work through each flag with the project maintainer, correcting content where
plcc-ng's behavior differs from the original PLCC README.
