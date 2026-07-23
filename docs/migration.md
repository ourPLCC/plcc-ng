# Migration from PLCC to PLCC-ng

PLCC-ng is a modern, pip-installable rewrite of [PLCC](https://github.com/ourPLCC/plcc).
It adds Python semantics support, a cleaner CLI, and a more extensible architecture.
It is not backward compatible — spec files and command invocations both require updates.

## Breaking behavior changes

These two command-output changes are easy to miss in the checklist below and
have caught instructors migrating workshop materials by surprise.

**`plcc-parse` always prints the full parse tree.** There is no `-t` flag
for tracing and no `OK` output on success — the parse tree is the output.

**`plcc-scan` output format changed.** PLCC printed `TOKEN_NAME(lexeme)`;
PLCC-ng prints `source:line:col TOKEN_NAME 'lexeme'`, where `source` is the
filename (or `-` for stdin) and `line`/`col` are 1-indexed.

```
# PLCC
INTEGER(3)
ADDOP(+)

# PLCC-ng
-:1:1 INTEGER '3'
-:2:1 ADDOP '+'
```

Update any documentation, tests, or course materials that show the old
`TOKEN(lexeme)` format — they will no longer match actual output.

**The `_run()` entry point must return a string.** This applies whether
you're migrating an old `$run()` or have already ported to `_run()`. Java's
`_run()` changed from `void` (print inside the method) to `String` (return
the text) — a spec with `public void _run() { System.out.println(...); }`
will fail to compile and must become
`public String _run() { return ...; }`. Python and JavaScript's `_run()`
must now return an actual `str`/`string` — a `_run()` that returns a
non-string value (an `int`, a `list`, a bare number, ...) now fails with a
`specification_error` instead of silently working; convert explicitly
(`str(x)` / `String(x)`) if needed. No language's `_run()` may print or
write to stdout directly — only plain-text `plcc-rep` sessions tolerated
that before, and only by accident.

## Migration checklist

### 1. Install PLCC-ng

Replace the PLCC shell script, Docker, or DevContainer install with:

```bash
pip install plcc-ng
```

See [Installation](installation.md) for upgrade, pinning, and uninstall instructions.

### 2. Rename your grammar file

PLCC's default grammar file is named `grammar`. PLCC-ng's default is `spec.plcc`.

```
grammar  →  spec.plcc
```

### 3. Update regex patterns in the lexical section

PLCC uses Java regex ([`java.util.regex.Pattern`](https://docs.oracle.com/en/java/javase/11/docs/api/java.base/java/util/regex/Pattern.html)).
PLCC-ng uses Python regex ([`re`](https://docs.python.org/3/library/re.html)).

Most common patterns are identical. The following Java-specific syntax must be rewritten:

| Java pattern | Python equivalent |
|---|---|
| `\p{Alpha}` | `[a-zA-Z]` |
| `(?<name>...)` named group | `(?P<name>...)` |
| `\p{Digit}` | `\d` |

Test your patterns with a Python regex tool (e.g. [regex101.com](https://regex101.com/) set to Python flavor).

### 4. Check scan algorithm behavior

PLCC gives skip rules priority over all token rules whenever they match *any* input,
regardless of match length. PLCC-ng uses pure first-longest-match — skip and token rules
compete equally, with ties broken by declaration order.

If any of your skip rules are shorter than competing token rules, the behavior changes:

| Input | PLCC | PLCC-ng |
|---|---|---|
| `123` with `skip ONE '1'` before `token NUMBER '\d+'` | skip wins (nothing emitted) | `NUMBER '123'` (longer match wins) |

**Fix:** If you relied on skip-first behavior, rewrite the skip pattern to match as many characters as the token it was shadowing. For most grammars (whitespace skips vs. identifier/number tokens), the longest match already produces the same result and no change is needed.

### 5. Update nonterminal names to PascalCase

PLCC nonterminals are lowercase; PLCC-ng uses PascalCase.

| PLCC | PLCC-ng |
|---|---|
| `<prog>` | `<Program>` |
| `<exp>` | `<Expr>` |

Update every nonterminal on both the left-hand side and right-hand side of every rule.

### 6. Update alternative/subclass syntax

PLCC places the distinguishing name as a suffix after the closing bracket.
PLCC-ng places it after a colon inside the brackets.

| PLCC | PLCC-ng |
|---|---|
| `<exp>WholeExp ::= ...` | `<Expr:WholeExp> ::= ...` |
| `<exp>SubExp ::= ...` | `<Expr:SubExp> ::= ...` |

### 7. Update captured field syntax

PLCC places a field name as a suffix after the closing bracket.
PLCC-ng places it after a colon inside the brackets.

| PLCC | PLCC-ng |
|---|---|
| `<exp>exp1` (field named `exp1`) | `<Expr:exp1>` |
| `<exp>exp2` (field named `exp2`) | `<Expr:exp2>` |
| `<WHOLE>` (auto-named field `whole`) | `<WHOLE>` (same — auto-naming unchanged) |
| `<WHOLE>` with explicit name | `<WHOLE:whole>` |

### 8. Add semantic section language header

PLCC only supports Java semantics and has no language header.
PLCC-ng requires the first non-blank line of the semantic section to declare the language.

Before (PLCC):
```
%
Prog
%%%
  public void $run() { ... }
%%%
```

After (PLCC-ng):
```
%
Java

Prog
%%%
  public String _run() { ... }
%%%
```

The supported values are `Java` and `Python`.

### 9. Rename the entry point method

The method the start symbol's class uses as its execution entry point was
renamed — and its contract changed, not just its name.

| PLCC | PLCC-ng |
|---|---|
| `$run()` | `_run()` |

`$run()` was `void`; it printed its output directly. `_run()` must
**return** a string — the runtime prints it for you. See "Breaking
behavior changes" above for what this means for each language.

Update this in the semantic section of your spec file.

### 10. Check `%include` paths

Both PLCC and PLCC-ng support `%include FILENAME`. The syntax is unchanged.
If your include paths were relative to a file named `grammar`, they will work
unchanged — paths are resolved relative to the file that contains the `%include` directive.

### 11. Replace commands

| PLCC | PLCC-ng | Notes |
|---|---|---|
| `plcc.py --version` | `plcc-version` | |
| `plccmk [-c] [file]` | *(not needed)* | Top-level commands generate and compile automatically |
| `scan [file...]` | `plcc-scan [file...]` | Token output format changed (see below) |
| `parse [-t] [-n] [file...]` | `plcc-parse [file...]` | Always shows parse tree; no `-t` flag needed |
| `rep [-t] [-n] [file...]` | `plcc-rep [file...]` | |
| `parse --json_ast` | `plcc-tokens \| plcc-trees` | See below |

**Token output format change:**

PLCC format:
```
   1: WHOLE '3'
```

PLCC-ng format (`file:line:column`):
```
-:1:1 NUM '42'
```

**JSON parse trees:**

PLCC's `--json_ast` flag (passed to `plccmk` and `parse`) is not available in PLCC-ng.
To obtain a JSON parse tree, use the lower-level pipeline:

```bash
plcc-spec spec.plcc > plcc-ng/spec.json
plcc-spec spec.plcc | plcc-ll1 > plcc-ng/ll1.json
plcc-tokens plcc-ng/spec.json samples/ | plcc-trees --ll1=plcc-ng/ll1.json
```

See [`plcc-trees`](cli/commands/plcc-trees.md) for details.

## Features not yet in PLCC-ng

- **Docker installation** — PLCC supported Docker via `plcc-con`. PLCC-ng is currently pip-only. Docker support is planned.
- **DevContainer** — PLCC provided a ready-to-use devcontainer image. PLCC-ng does not yet provide one.
