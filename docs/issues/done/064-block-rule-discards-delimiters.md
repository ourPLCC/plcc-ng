# 064 - Block rules discard the opening and closing delimiter patterns

**Type:** bug
**Date:** 2026-06-05

## Description

When a block token or skip rule matches, the lexeme includes only the content between the delimiters — the opening and closing patterns themselves are stripped. They should be included.

## Steps to Reproduce

`a.plcc`:
```
WS '\s+'
BLOCK_COMMENT '/\*' '\*/'
```

`in.a`:
```
/*

hi

*/


/* another */
```

```bash
$ plcc-scan in
plcc-ng 0.33.0  grammar: /workspaces/CCSCNE-2026/plcc/a.plcc
in:1:1 BLOCK_COMMENT '

hi

'
in:5:3 WS '
'
...
in:8:1 BLOCK_COMMENT ' another '
```

## Expected

The lexeme for each `BLOCK_COMMENT` should include the delimiters:

```
in:1:1 BLOCK_COMMENT '/*

hi

*/'
in:8:1 BLOCK_COMMENT '/* another */'
```

## Notes

- The open and close patterns are part of the matched text and should be preserved in the lexeme, consistent with how non-block tokens work.
- This likely means the block scanning code needs to prepend the opening match and append the closing match to the accumulated content.
