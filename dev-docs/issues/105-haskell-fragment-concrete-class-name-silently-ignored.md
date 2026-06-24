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

The fix should raise a fatal error when a fragment's `class_name` matches a
concrete alternative whose parent abstract rule owns the module, with a message
that names the concrete class, explains it maps to a constructor (not a module),
and directs the user to use the abstract class name instead.

The correct workaround for users today is to use the abstract class name
(`ExprRest`) as the fragment's class name, since that is the module that
gets generated.

## Related: Haskell documentation needed

The Haskell emitter's one-nonterminal-per-module model is not documented and
causes this class of confusion:

- In Haskell, each **abstract rule** (non-terminal) maps to a **module**
  (`ExprRest` → `ExprRest.hs`) and its concrete alternatives map to
  **constructors** within that module (`AddRest`, `NilRest` are constructors
  of the `ExprRest` data type).
- Fragment class names in `%haskell` sections must therefore be the **abstract
  rule name** (the module), never the concrete alternative name (a constructor).
- This is different from Java, where every class — concrete or abstract — has
  its own file, so concrete names are valid fragment targets.

Documentation should make this model explicit so users understand why concrete
alternative names are invalid as fragment targets in Haskell.
