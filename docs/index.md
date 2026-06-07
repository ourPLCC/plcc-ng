# PLCC-ng

PLCC-ng is the next generation of
the Programming Languages Compiler Compiler ([PLCC](https://github.com/ourPLCC/plcc)).
It is a tool for teaching and learning programming language concepts.

The goal is to make specifying the syntax of languages as easy to do and
understand, so the learner can focus on studying the essence of
programming languages: semantics. As such, when designing and implementing
PLCC-ng, we value understandability and ease of use over performance.
Whenever possible we use standard notations and easy to explain and understand
algorithms.

Key features of PLCC-ng:

- Semantics can be defined in Python or Java.
- Syntax is defined using standard notations: regex and BNF.
- The scanner uses a simple first-longest-match algorithm.
- Parser supports LL(1), and follows a simple top-down, predictive parsing algorithm.
- Three command-line tools to interactively test each part a language specification:
  - `plcc-scan` to test the lexical specification
  - `plcc-parse` to test the syntactic specification
  - `plcc-rep` to test the semantic specification
- Assistive error messages that help students learn why the error occurred
    and how they might correct it.
- Trace modes to visualize and understand the scan and parse algorithms.

## Where to start

- [Getting Started](getting-started.md) — install and run your first grammar in under 10 minutes.
- [Language Guide](language-guide/index.md) — token rules, BNF syntax, code generation, worked examples.
- [CLI Reference](cli/index.md) — every command, every flag.
- [Instructor Guide](instructor-guide/index.md) — what it teaches, what students need to know, how to structure assignments.

## Join Our Community

- [Discord server](https://discord.gg/EVtNSxS9E2): get help and receive announcements.
- [GitHub](https://github.com/ourPLCC/plcc-ng): report bugs, view the source, make a contribution.

## Licenses

- Code is licensed under AGPL 3.0 or later.
- Non-code (e.g., documentation) is licensed under Creative Commons
    CC-BY-SA 4.0.
