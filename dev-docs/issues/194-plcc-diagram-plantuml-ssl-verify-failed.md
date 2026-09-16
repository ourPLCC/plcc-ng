# 194 - plcc-diagram-plantuml-ssl-verify-failed

**Type:** fix
**Date:** 2026-09-16

<!--
Classify by user-facing impact, not by whether something was "broken".
`fix` and `feat` bump the release version (see [tool.semantic_release]
in pyproject.toml); reserve them for changes to the shipped package
(src/). A bug in a test, script, or CI workflow (bin/, tests/,
.github/) is still a bug, but it's not user-facing — classify it
`test` or `chore` instead so it doesn't spin the version. `docs` is for
documentation content, and never bumps the version either way.
-->

## Description

`plcc-diagram-plantuml-build` ([src/plcc/diagram/plantuml/build.py](../../src/plcc/diagram/plantuml/build.py))
renders diagrams by POSTing the encoded `.puml` source to
`https://www.plantuml.com/plantuml/png/...` via `urllib.request.urlopen`.
It calls `urlopen` with no explicit `context=`, so certificate verification
falls back to Python's implicit default SSL context — whatever CA trust
store that particular Python install happens to have wired up. On an
install where that's empty, stale, or not wired to the OS store, every
call fails with:

```
plcc-diagram-plantuml-build: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED]
certificate verify failed: unable to get local issuer certificate (_ssl.c:1028)>
```

Reported by an instructor (Alain) after having students run the demos: most
students hit this in `demo-plcc-parse` when running `plcc-diagram`, but it
did not reproduce on the instructor's own machine, despite (as far as
reported) identical firewall/network policy.

## Steps to Reproduce

1. Use a Python install whose default SSL context has no usable CA trust
   store — e.g. macOS with the python.org installer, before running
   `Install Certificates.command`; or an Anaconda/Miniconda install with a
   stale `ca-certificates` package.
2. Run `plcc-diagram` (or `plcc-diagram-plantuml-build` directly) on any
   `.puml` file.
3. Observe `CERTIFICATE_VERIFY_FAILED: unable to get local issuer
   certificate`.

## Notes

Root cause is client-local: certificate chain validation happens after the
TCP connection succeeds, using only the trust store local to that Python
install. It's independent of firewall/routing, which is why "same firewall
settings" didn't rule it out — different students simply have Python
installs with different (or missing) CA trust stores. This affects most
students but not literally all, and not the instructor, which is the
expected fingerprint of trust-store heterogeneity rather than a network
block.

Proposed direction: stop depending on the ambient/OS trust store and pin
verification to the `certifi` package's bundled CA root list instead
(`ssl.create_default_context(cafile=certifi.where())`), added as a small,
widely-used, pure-Python dependency. This does not require ongoing
maintenance — `certifi` ships long-lived root CAs, not the server's
short-lived leaf certificate, and we'd depend on it unpinned
(`certifi>=<floor>`) so routine dependency bumps keep it current.

Residual case this would *not* fix: a network that TLS-intercepts with an
internal/private CA (school security proxy). If some students still fail
after this fix, that's the diagnostic signal pointing there instead — a
different, institution-specific remedy, not a `plcc-ng` bug.

See design doc: dev-docs/specs/2026-09-16-194-plcc-diagram-plantuml-ssl-verify-failed-design.md
