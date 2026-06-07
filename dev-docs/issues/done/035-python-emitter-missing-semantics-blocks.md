# 035 - Python emitter not including semantics blocks

**Type:** fix
**Date:** 2026-05-24

## Description

When a spec file includes a `% HiPy python` semantics section with `%%%`-delimited blocks,
the generated Python classes do not include the code from those blocks. As a result, methods
defined there (e.g., `_run`) are never injected into the class, and `plcc-rep` falls back to
the default `__str__` output instead of executing the user's logic.

## Steps to Reproduce

1. Create `grammar.plcc`:

```
skip WHITESPACE '\s*'
token NUM '\d+'
token PERIOD '\.'
%
<start> ::= <stuff>
<stuff>:Stuff1 ::= NUM <stuff>
<stuff>:Stuff2 ::= PERIOD
% HiPy python
Start
%%%
def _run(self):
    print("hi");
%%%
```

2. Run:

```bash
$ plcc-rep
>>> 32 . ^D
```

3. Observed output:

```
<Start.Start object at 0x7f87cc582a50>
```

4. Expected output:

```
hi
```

## Notes

The `HiPy python` semantics block is parsed by the spec reader but appears to be dropped
or ignored by the Python code emitter. Compare with issue #028, which covered semantics
block injection for the base class — this may be a related gap in the per-class code
generation path.
