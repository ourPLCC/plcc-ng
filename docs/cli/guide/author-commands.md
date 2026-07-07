# Author-facing commands

These are the commands you interact with directly when working with plcc-ng.
Everything else runs behind the scenes.

## Daily drivers

Use these to experiment with your language spec at each stage of the pipeline.
They all remember the spec file path between invocations — pass `-s <path>`
once and subsequent commands in the same directory pick it up automatically.

### plcc-scan

Tokenize source input and print each token in human-readable format. Useful
for checking that your lexical rules match what you expect.

```bash
echo "42 36 2" | plcc-scan
plcc-scan -s subtract.plcc samples/
```

### plcc-parse

Parse source input and print the parse tree. Useful for verifying that your
grammar accepts the input you intend and rejects what it shouldn't.

```bash
echo "42 36 2" | plcc-parse
plcc-parse -s subtract.plcc samples/
```

`plcc-parse` also has an interactive mode: when no source files are given and
stdin is a terminal, it reads input at a `>>>` prompt and parses each line as
you type.

### plcc-rep

Read-eval-print loop. Runs your full language spec — scanning, parsing, and
executing semantics — and prints the result of each input.

```bash
plcc-rep -s subtract.plcc samples/   # evaluate files and exit
plcc-rep -s subtract.plcc            # enter interactive mode
```

## Common options

All commands accept these options:

| Option | Effect |
|---|---|
| `-h`, `--help` | Show usage and exit |
| `-v` | Increase verbosity (repeat for more detail: `-v`, `-vv`, `-vvv`) |
| `--verbose-format=FMT` | Verbosity output format: `text` (default) or `json` |

## Visualization

### plcc-diagram

Generate and display a class diagram from your spec file. Shows the classes
and inheritance relationships that plcc-ng derives from your syntactic
grammar — useful for understanding the object model you'll program against
when writing semantics.

```bash
plcc-diagram -s subtract.plcc
```

> **Requires the `plcc-diagram` package.** If `plcc-diagram` is not
> installed, this command will not be available.

## Metadata and extension discovery

### plcc-version

Print the installed plcc-ng version.

```bash
plcc-version
```

### plcc-lang-list

List the language plugins installed on your system. plcc-ng ships with
`python` and `java` support; this command shows what is available.

```bash
plcc-lang-list
```

### plcc-parser-list

List the parser plugins installed on your system. plcc-ng ships with the
`table` parser (LL(1) table-driven); this command shows what is available.

```bash
plcc-parser-list
```

### plcc-diagram-list

List the diagram plugins installed on your system. Each line shows a
`type/format` pair (e.g., `class/plantuml`).

```bash
plcc-diagram-list
```

> **Requires the `plcc-diagram` package.**

## Extension points

plcc-ng is built around extension points. The language, parser, and diagram
plugins you see above are the built-in implementations, but the system is
designed so that new plugins can be installed alongside plcc-ng and discovered
automatically. See the [Language extensions](language-extensions.md),
[Parser extensions](parser-extensions.md), and
[Diagram extensions](diagram-extensions.md) guides for details.
