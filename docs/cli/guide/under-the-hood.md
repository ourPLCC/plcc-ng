# Under the Hood

The commands you use every day — `plcc-scan`, `plcc-parse`, `plcc-rep`, and
`plcc-diagram` — each orchestrate a pipeline of lower-level commands. This
page shows how the pieces fit together.

## Dependency diagram

The diagram below shows which commands call which. An arrow from A to B means
A calls B.

```plantuml
@startuml
allowmixing

left to right direction

package language-extensions {
  package plcc-java {
    class plcc-java-emit
    class plcc-java-build
    class plcc-java-run
  }

  package plcc-python {
    class plcc-python-emit
    class plcc-python-build
    class plcc-python-run
  }
}

package parser-extensions {
  package plcc-parser-table {
    class plcc-parser-table
  }
}

package diagram-extensions {
  package plcc-plantuml-diagram {
    class plcc-diagram-class-plantuml-emit
    class plcc-diagram-plantuml-build
    class plcc-diagram-plantuml-run
  }
}

package core {

  class plcc-version
  class plcc-lang-list
  class plcc-parser-list

  plcc-scan --> plcc-make
  plcc-scan --> plcc-tokens

  plcc-parse --> plcc-make
  plcc-parse --> plcc-tokens
  plcc-parse --> plcc-trees

  plcc-rep --> plcc-make
  plcc-rep --> plcc-tokens
  plcc-rep --> plcc-trees
  plcc-rep --> plcc-lang-run

  plcc-make --> plcc-spec
  plcc-make --> plcc-ll1
  plcc-make --> plcc-model
  plcc-make --> plcc-lang-emit
  plcc-make --> plcc-lang-build

  plcc-trees --> parser-extensions.plcc-parser-table.plcc-parser-table

  plcc-lang-emit --> plcc-python-emit
  plcc-lang-emit --> plcc-java-emit
  plcc-lang-build --> plcc-java-build
  plcc-lang-build --> plcc-python-build
  plcc-lang-run --> plcc-python-run
  plcc-lang-run --> plcc-java-run

}

package plcc-diagram {

  class plcc-diagram-list

  plcc-diagram --> plcc-make
  plcc-diagram --> plcc-diagram-emit
  plcc-diagram --> plcc-diagram-build
  plcc-diagram --> plcc-diagram-run

  plcc-diagram-emit --> plcc-diagram-class-plantuml-emit
  plcc-diagram-build --> plcc-diagram-plantuml-build
  plcc-diagram-run --> plcc-diagram-plantuml-run

}

actor "Language Author" as author

author --> plcc-scan
author --> plcc-parse
author --> plcc-rep
author --> plcc-version
author --> plcc-lang-list
author --> plcc-parser-list
author --> plcc-diagram
author --> plcc-diagram-list

@enduml
```

## The core pipeline

`plcc-make` is the build orchestrator at the centre of the core package. Every
author-facing command calls it before doing its own work.

| Command | Input → Output |
| --- | --- |
| [`plcc-make`](../commands/plcc-make.md) | `.plcc` spec file → build artifacts in `build/` |
| [`plcc-spec`](../commands/plcc-spec.md) | `.plcc` file → spec JSON |
| [`plcc-ll1`](../commands/plcc-ll1.md) | spec JSON → LL(1) analysis JSON |
| [`plcc-tokens`](../commands/plcc-tokens.md) | spec JSON + source files → token JSONL |
| [`plcc-trees`](../commands/plcc-trees.md) | token JSONL + LL(1) JSON → parse tree JSON (dispatches to parser plugin) |
| [`plcc-model`](../commands/plcc-model.md) | spec JSON → language-neutral model JSON |
| [`plcc-lang-emit`](../commands/plcc-lang-emit.md) | model JSON → language source files (dispatches to language plugin) |
| [`plcc-lang-build`](../commands/plcc-lang-build.md) | language source files → compiled output (dispatches to language plugin) |
| [`plcc-lang-run`](../commands/plcc-lang-run.md) | compiled output + parse tree JSON → evaluation result (dispatches to language plugin) |

## The diagram pipeline

`plcc-diagram` (in the `plcc-diagram` package) calls `plcc-make` to build the
model, then runs its own sub-pipeline:

| Command | Input → Output |
| --- | --- |
| [`plcc-diagram-emit`](../commands/plcc-diagram-emit.md) | model JSON → diagram source (dispatches to diagram plugin) |
| [`plcc-diagram-build`](../commands/plcc-diagram-build.md) | diagram source → PNG image (dispatches to diagram plugin) |
| [`plcc-diagram-run`](../commands/plcc-diagram-run.md) | PNG path → prints path to stdout (dispatches to diagram plugin) |
