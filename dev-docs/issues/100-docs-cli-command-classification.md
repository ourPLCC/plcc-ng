# 100 - Reconsider how CLI commands are classified and presented in the docs

**Type:** docs
**Date:** 2026-06-18

## Description

The CLI reference currently groups commands as "Level 0" (primitives) and
"Level 2" (orchestrators). These labels are architectural/internal and not
meaningful to users. Issue 083 flagged that `plcc-diagram` is misclassified
under this scheme. The deeper question is whether this classification is the
right one for the docs at all.

## Context and Discussion

The current "Level 0 / Level 2" framing reflects the internal pipeline
architecture, not how students actually experience the tool. When you look at
actual usage patterns, the commands fall into three distinct groups:

**Primary student tools (`plcc-scan`, `plcc-parse`, `plcc-rep`):** These are
what students use day-in and day-out. Their primary purpose is to allow
students to experiment with and test their language specification at different
stages of the pipeline. These deserve the most prominent placement.

**Visualization (`plcc-diagram`):** Helps students understand the mapping from
the syntactic spec to the classes and objects they program with when defining
semantics. Useful but not a daily driver — its place in the workflow is less
clear and students may reach for it infrequently.

**Everything else (`plcc-make` and the lower-level pipeline commands):** Students
will rarely interact with these directly unless an instructor demonstrates them
or explicitly asks students to use them. These are closer to plumbing.

## Options Considered

- **"Workflow commands / Stage commands"** — maps to the pipeline architecture
  but still doesn't reflect the student experience.
- **"Testing / Visualization / Plumbing"** — more honest about purpose, but
  "plumbing" may be off-putting.
- **"Interactive / Visualization / Advanced"** — emphasizes that scan/parse/rep
  are the hands-on tools; "advanced" signals students can ignore the rest.
- **Drop grouping entirely** — lead with prose that says "you'll mostly use
  `plcc-scan`, `plcc-parse`, and `plcc-rep`" and let emphasis come from the
  narrative rather than category labels. The argument here is that category
  labels imply equal weight across groups, whereas what we really want is for
  students to immediately understand these three commands are their world.

## Open Question

Which approach best serves students who are new to the tool? Is a category
label the right mechanism at all, or does prose framing do a better job of
directing attention to the commands that matter most?

## Notes

This issue also supersedes the reclassification in [[083-fix-plcc-diagram-misclassified]]
— once the classification scheme itself is resolved, 083 either gets folded in
or becomes moot.

Likely touches `docs/cli/index.md` and the overall CLI reference structure.
