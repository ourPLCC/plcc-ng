# 072 - Add version-pinning instructions to docs

**Type:** docs
**Date:** 2026-06-07

## Description

The docs do not explain how to install or stay on a specific version of plcc-ng. Users who need a stable, reproducible environment have no documented path for pinning.

## Desired Behavior

Add a section to the docs (likely near the installation and upgrade pages) that covers:

- Installing a specific version (e.g. `pip install plcc-ng==1.2.3`).
- Pinning in a `requirements.txt` or `pyproject.toml` dependency spec.
- How to check which version is currently installed.

## Notes

Could live alongside the upgrade instructions added in issue 071.
