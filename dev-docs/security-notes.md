# Security notes

Running log of security-relevant findings that aren't full incidents but are
worth remembering so we don't re-investigate them from scratch next time.

## 2026-07-07 — `mkdocs build` prints a "switch to ProperDocs" warning

**Trigger:** Running `pdm run mkdocs build --strict` (as part of verifying the
issue #147 heading-capitalization fix) printed a scary-looking warning
claiming MkDocs is abandoned and urging an install of `pip install
properdocs`, styled like an official notice from "the Material for MkDocs
team."

**What it turned out to be:** Legitimate, not malware — but worth
recognizing on sight.

- MkDocs genuinely has an unresolved maintainership conflict, and the
  original author is working on an incompatible "MkDocs 2.0" in a private
  `encode/mkdocs` repo. See [The Slow Collapse of
  MkDocs](https://fpgmaas.com/blog/collapse-of-mkdocs/).
- **ProperDocs** (`properdocs.org`, GitHub org `ProperDocs`) is a real
  drop-in-replacement fork started by a former MkDocs maintainer
  (`@oprypin`). Its announcement — [Discussion
  #33](https://github.com/orgs/ProperDocs/discussions/33), 2026-03-15 —
  explicitly instructs plugin/theme authors to adopt a "replacement warning"
  pattern: cap `mkdocs` at `<=1.6.1`, add `properdocs` as an extra
  dependency, and call `properdocs.replacement_warning.setup()` so the
  warning fires during `mkdocs build` for anyone with `properdocs` installed.
- `mkdocs-kroki-plugin` adopted that guidance in [commit
  432d75d](https://github.com/AVATEAM-IT-SYSTEMHAUS/mkdocs-kroki-plugin/commit/432d75d18d9b8d2a0055f99f404f233279d64c2f)
  (2026-04-02). That's why an unrelated diagram plugin is the thing printing
  a MkDocs-ecosystem warning — it's intentional, ecosystem-sanctioned
  nagware, not a compromised dependency.
- Separately, **Zensical** (`github.com/zensical/zensical`) is the *actual*
  Material-for-MkDocs team's own successor project — a different effort from
  ProperDocs. The ProperDocs warning cites [the real squidfunk Zensical
  announcement](https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/)
  as "our full analysis," but that post recommends **Zensical**, not
  ProperDocs. The warning borrows a real, credible citation to back a claim
  the citation doesn't actually make. Treat that as a knock against
  ProperDocs's marketing honesty, not as evidence the package itself is
  malicious.

**Why it looked like an attack at first:** The warning text doesn't exist as
static source in `mkdocs`, `mkdocs-material`, or `mkdocs-kroki-plugin` — it's
generated at runtime by `properdocs.replacement_warning.setup()`, which is
only importable if `properdocs` happens to already be installed. In a shared
devcontainer `.venv` where install provenance isn't obvious per-session, that
combination (dynamic warning + unexplained package + citation mismatch) is
genuinely indistinguishable from a supply-chain injection until you trace it
back to source. It was worth the full trace.

**How to re-verify quickly next time:** grep the installed packages for the
literal warning text (it won't be there — that's expected, not a red flag by
itself); check whether `properdocs` is installed and why (`pip show
properdocs`, check which package's metadata requires it); if a warning cites
a URL, fetch the URL and check it actually supports the claim being made.

**Open decision (not yet made):** whether this repo should pin `mkdocs`
below any version that starts pulling in `properdocs` transitively, migrate
to Zensical, or do nothing until MkDocs 2.0 actually ships. Not resolved as
part of issue #147 — revisit if/when `mkdocs-kroki-plugin` or another pinned
doc dependency forces the question. Set `DISABLE_MKDOCS_2_WARNING=true` in
the meantime if the nag becomes disruptive to CI log output.
