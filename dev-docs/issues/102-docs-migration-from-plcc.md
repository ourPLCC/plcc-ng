# 102 - Add a migration guide from PLCC to PLCC-ng

**Type:** docs
**Date:** 2026-06-19

## Description

Users of the original PLCC tool have no documented path for migrating to PLCC-ng. Without a migration guide, the differences between the two tools are opaque and the switching cost feels unknown.

## Desired Behavior

Add a migration page to the docs that covers:

- A high-level summary of what changed and why (the motivation for PLCC-ng).
- A side-by-side comparison of the major breaking differences: syntax changes, renamed commands, removed commands, and behavioral differences.
- A step-by-step migration checklist a user can follow to port an existing PLCC project to PLCC-ng.
- Any features from PLCC that are not yet available in PLCC-ng, so users know what to expect.

## Notes

The page should be honest about gaps. If PLCC-ng does not yet support something that PLCC did, say so and link to the relevant open issue.

A good placement is alongside the installation and upgrade docs, or as its own top-level page in the navigation.
