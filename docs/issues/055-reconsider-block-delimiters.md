# 055 - Consider alternative block delimiters

**Type:** feat
**Date:** 2026-06-01

## Description

Reconsider the block delimiter syntax. Currently both the opening and closing delimiter for a block are `%%%`. This works well in practice, but it does not visually distinguish opening from closing.

Others have suggested an asymmetric pair such as `%%{` / `%%}` to make open/close explicit. That approach was rejected because many editors recognize bare `{` and `}` as bracket characters and syntax-highlight or auto-pair them separately from the surrounding `%%`, breaking the delimiter visually. `%%%` does not suffer from this problem, which is why it has remained the choice.

## Alternatives

- **`%%+` / `%%−`** — asymmetric open/close using plus and minus. Neither character triggers editor bracket-matching. The `+`/`−` pair has a natural open/close connotation and is easy to type.

- **`%%BEGIN` / `%%END`** — keyword style. Maximally explicit and beginner-friendly; no ambiguity about which line opens and which closes a block. More verbose than symbol-based delimiters.

## Notes

- Any new delimiter must not be subject to editor bracket-matching that would split it visually.
- Preserving the symmetry of `%%%` is acceptable; the goal is only to see if a better alternative exists.
- Alternatives worth evaluating should be tested against common editors (VS Code, vim, emacs) to confirm they render as a single unit.
