# 056 - Reconsider the scanner algorithm

**Type:** feat
**Date:** 2026-06-01

## Description

Reconsider the algorithm used by the scanner. Currently, skips and tokens are handled separately. A simpler and more predictable alternative would be to use a single algorithm for both: first-longest-match, where all skip and token patterns compete together and the match that starts earliest and extends furthest wins.

## Notes

- First-longest-match is the algorithm used by most lexer generators (e.g. flex/lex) and is well understood by users.
- Unifying the treatment of skips and tokens under one algorithm reduces conceptual surface area.
- Edge cases to consider: what happens when a skip and a token match the same span? Declaration order could serve as a tiebreaker, as it does in traditional lexer generators.
