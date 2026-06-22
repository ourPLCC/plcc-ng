# 104 - Add `class` fragment support to Java emitter

**Type:** fix
**Date:** 2026-06-22

## Description

The original PLCC supported a `class` semantic hook for Java that injected content into the class declaration line, allowing users to add `implements` clauses to generated classes:

```java
public class Foo extends Bar /*Foo:class*/ {
```

plcc-ng's Java emitter (`src/plcc/lang/ext/java/`) omits this fragment kind entirely. The template (`class_file.java.jinja`) has no placeholder for it, and `emit.py` does not pass `class_fragments` to the template renderer.

## Steps to Reproduce

1. Write a PLCC-ng spec with a `java` semantic section that uses the `class` hook:

   ```text
   Foo:class
   %%%
   implements Runnable
   %%%
   ```

2. Run `plcc-java-emit`. The generated `Foo.java` will not contain `implements Runnable`.

## Notes

- The fix requires updating both `class_file.java.jinja` (add a placeholder after the `extends` clause) and `emit.py` (pass `class_fragments` to the template).
- Discovered while designing the JavaScript emitter (issue 066), which confirmed Java is missing this feature vs. the original PLCC.
- Python emitter already supports `class` fragments (as additional comma-separated base classes), so there is prior art in plcc-ng to follow.
