# 066 - Extend plcc-ng to one more popular programming language

**Type:** feat
**Date:** 2026-06-05

## Description

plcc-ng currently generates code in Java and Python. Add support for at least one more widely-used language so that more instructors and students can use the tool with their preferred language.

## Notes

- Candidate languages (in rough order of pedagogical interest): C#, JavaScript/TypeScript, Go, Kotlin, C++
- A new language emitter lives under `src/plcc/lang/ext/<language>/`
- Study the existing `java` and `python` emitters to understand the interface expected by `lang/emit.py`
- Consider which language would be easiest to support given the existing template/emitter architecture
- Runtime requirements for the generated code affect classroom usability
