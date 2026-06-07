# 073 - Add Java JDK as an optional prerequisite to docs

**Type:** docs
**Date:** 2026-06-07

## Description

The docs do not mention that a Java JDK is required when writing semantics in Java. Users who choose Java for their semantics hit a confusing failure with no documented explanation.

## Desired Behavior

In the prerequisites section of the docs, add a Java JDK entry marked as optional, with a note that it is needed only when writing semantics in Java. Include:

- What to install (JDK, not just JRE) and a recommended minimum version.
- Where to get it (e.g. Adoptium/Temurin, system package manager).
- How to verify the installation (`java -version`, `javac -version`).

## Notes

Should be clearly distinguished from required prerequisites so users who are not using Java do not install it unnecessarily.
