# 106 - Add documentation for the JavaScript language extension

**Type:** docs
**Date:** 2026-06-23

## Description

plcc-ng can now emit JavaScript, but there is no user-facing documentation for it. Users have no way to know the feature exists, how to invoke it, or how to write JavaScript semantic sections.

## Notes

- Model the page on the existing Java and Python language guide pages.
- Cover: how to invoke `plcc-javascript-emit`, the supported fragment kinds (`top`, `import`, `body`, `file`, `class`), and a minimal end-to-end example.
- Note any JavaScript-specific runtime requirements (Node.js version, module format).
