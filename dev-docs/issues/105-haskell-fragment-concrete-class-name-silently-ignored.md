# 105 - haskell-fragment-concrete-class-name-silently-ignored

**Type:** warning
**Date:** 2026-06-23

## Description

In the Haskell emitter, body (and other) fragments tagged with a concrete
alternative's class name (e.g. `AddRest`) are silently ignored when that
class belongs to an abstract rule. Because the one-module-per-rule design
generates one `.hs` file per abstract rule (`ExprRest.hs`), there is no
`AddRest.hs` to place the fragment into. The emitter drops it without any
warning or error.

## Steps to Reproduce

1. Write a grammar with an abstract rule `ExprRest` and a concrete alternative `AddRest`.
2. In the `%haskell` section, tag a body fragment under `AddRest`:
   ```
   AddRest
   %%%
   evalRest :: ExprRest -> Int -> String
   evalRest (AddRest t r) acc = ...
   evalRest NilRest acc = ...
   %%%
   ```
3. Run `plcc-haskell-emit`. No error or warning is printed.
4. The generated `ExprRest.hs` does not contain `evalRest`.
5. Any module that calls `evalRest` fails to compile.

## Notes

The fix should either:
- Emit a warning when a fragment's `class_name` matches a concrete class
  whose parent abstract rule owns the module, and suggest using the abstract
  class name instead.
- Or automatically redirect such fragments to the parent module (friendlier,
  but could be surprising for `file` fragments).

The correct workaround for users today is to use the abstract class name
(`ExprRest`) as the fragment's class name, since that is the module that
gets generated.
