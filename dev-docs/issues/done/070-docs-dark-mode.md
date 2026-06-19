# 070 - Add dark mode to docs site

**Type:** feat
**Date:** 2026-06-07

## Description

The docs site has no dark mode. Users who prefer dark mode (either by system preference or personal choice) see only the light theme with no way to change it.

## Desired Behavior

- Detect the user's system color-scheme preference (`prefers-color-scheme: dark`) and apply dark mode automatically.
- Provide a manual toggle so users can override the detected preference (force light or dark regardless of system setting).
- Persist the user's override across page loads (e.g. `localStorage`).

## Notes

Most static-site doc frameworks (MkDocs Material, Docusaurus, Sphinx) have first-class dark mode support. If the docs are built with one of those, enabling their built-in theme toggle may be enough. If the site uses custom CSS, a `data-theme` attribute on `<html>` toggled by a small JS snippet is a common pattern.
