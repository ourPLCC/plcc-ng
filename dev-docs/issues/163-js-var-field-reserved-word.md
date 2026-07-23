# 163 - Auto-named field colliding with a JavaScript reserved word breaks generated code

**Type:** docs
**Date:** 2026-07-23

## Description

A grammar token captured with its auto-generated field name colliding
with a JavaScript reserved word produces JavaScript that fails to load.
Specifically, `<VAR>` (no explicit `:fieldname`) auto-names its field
`var`, and the JavaScript target's generated constructor uses that name
as a parameter (`constructor(var) { ... }`), which is a `SyntaxError` in
JavaScript (`var` is reserved).

## Steps to Reproduce

1. Grammar with `token VAR '[A-Za-z]\w*'` and `<Exp:VarExp> ::= <VAR>`
   (no explicit field name), targeting `javascript`.
2. `echo "x" | plcc-rep`
3. Actual: `SyntaxError: Unexpected token 'var'` while loading the
   generated `VarExp.js`. Expected: it runs, same as the Python/Java
   targets do with the same grammar.

Renaming the capture (e.g. `<VAR:name>`) works around it.

## Notes

Originally filed as issue #4 in `ourPLCC/languages-ng`
(`dev-docs/issues/004-js-var-field-reserved-word.md`), found while
validating a phase-0/phase-1 plan there. Since `VAR` is the conventional
token name for identifiers across that repo's languages, it now renames
the capture everywhere a grammar is shared across targets, rather than
special-casing JavaScript.

plcc-ng might reasonably want to either reject/rename reserved-word
field names at generation time, or document the restriction (JavaScript
is presumably not the only target with reserved words that could
collide this way).
