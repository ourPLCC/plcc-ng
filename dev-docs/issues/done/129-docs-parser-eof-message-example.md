# 129 - Update docs for "end of file" parser error message change

**Type:** docs
**Date:** 2026-06-30

## Description

A recent fix changed parser error messages from `eof` to `end of file`. Any documentation that shows example parser error output containing the old `eof` wording is now stale.

## Notes

- Search docs for `eof` in error message examples and update to `end of file`.
- Also check quickstart guides, language guide, and CLI command pages for any copy-pasted error output.
