# 056 - Reconsider the scanner algorithm

**Type:** feat
**Date:** 2026-06-01

## Description

Reconsider the algorithm used by the scanner. Currently, skips and tokens are handled separately. A simpler and more predictable alternative would be to use a single algorithm for both: first-longest-match, where all skip and token patterns compete together and the match that starts earliest and extends furthest wins.

## Analysis

The current algorithm (in `src/plcc/scan/matcher.py`) gives skips categorical priority over tokens: if any skip pattern matches at the current position, the first-declared skip wins immediately, regardless of length. Only when no skips match does longest-match apply, and only among tokens.

This was inherited from the original PLCC and is likely a performance optimization — bail early when a skip matches rather than running all token patterns. For an academic tool with small inputs, this optimization is not meaningful.

The semantic difference: under the current algorithm, a 1-character skip beats a 10-character token match at the same position. Under first-longest-match, length decides and skips have no categorical advantage.

In practice this difference is unlikely to matter. Skips (whitespace, comments) and tokens (identifiers, literals) don't overlap, so skips win naturally by being the only match — not because of priority rules. Existing grammars are unlikely to rely on a skip preempting a longer token. The example grammars should be audited to confirm before shipping the change.

## Notes

- First-longest-match is the algorithm used by most lexer generators (e.g. flex/lex) and is well understood by users.
- Unifying the treatment of skips and tokens under one algorithm reduces conceptual surface area.
- Edge cases to consider: what happens when a skip and a token match the same span? Declaration order could serve as a tiebreaker, as it does in traditional lexer generators.
- flex/lex does not have skips as a first-class concept at all — a "skip" is simply a pattern whose action discards the matched text. All patterns compete under the same first-longest-match rule. PLCC made skips explicit (a good pedagogical choice) but added a priority rule that flex/lex does not have and does not need. Aligning the algorithm would remove a gap between PLCC's behavior and what students learn from textbooks and other tools.
