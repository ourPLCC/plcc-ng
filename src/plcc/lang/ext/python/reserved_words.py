import keyword

# Sourced from the running interpreter's own stdlib so it can never drift
# from the Python version actually executing plcc-ng. Deliberately uses
# kwlist (hard keywords), not softkwlist — `match`, `case`, `type`, `_`
# remain legal parameter names.
RESERVED_WORDS = frozenset(keyword.kwlist)
