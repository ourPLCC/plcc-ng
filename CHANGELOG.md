# CHANGELOG


## v0.59.2 (2026-06-27)

### Bug Fixes

- ^c always exits 130 in interactive mode, even in continuation
  ([#119](https://github.com/ourPLCC/plcc-ng/pull/119),
  [`5799012`](https://github.com/ourPLCC/plcc-ng/commit/5799012ce1d9e8c806dbed25a801d13a3d7a47a0))

Replace the buffer-clearing path with immediate exit 130 when Ctrl+C is pressed, regardless of
  whether there's unparsed content in the buffer.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for issue #119 ctrl-c continuation mode fix [skip ci]
  ([`26e035d`](https://github.com/ourPLCC/plcc-ng/commit/26e035d56407bd3766a42dd16e6d6bc16f215ca2))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issue #119 ctrl-c continuation mode [skip ci]
  ([`2d8a725`](https://github.com/ourPLCC/plcc-ng/commit/2d8a7259ea2b3ec31d0891ff309b3a20944b579a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.59.1 (2026-06-26)

### Bug Fixes

- Guard against None separator in _validateSeparatorIsTerminal
  ([`3989921`](https://github.com/ourPLCC/plcc-ng/commit/3989921dcb1de8ba976dfc101b6c9f750d2c8d47))

A repeating rule using **= without a separator has rule.separator=None, causing an AttributeError
  when the validator tried to access .name.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.59.0 (2026-06-26)

### Bug Fixes

- Correct InvalidLhsNameError message and update plcc-parse.bats to use valid LHS names
  ([`16a5591`](https://github.com/ourPLCC/plcc-ng/commit/16a559144b31f4ce4584190578750adc2adfd3f2))

LHS names in PLCC must start with an uppercase letter (they become class names). The message said
  "lowercase" — opposite of the actual check in is_valid_class_name. Two bats tests also used
  invalid lowercase <program>/<expr> specs that only worked before because plcc-validate-syntactic
  was dead code.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **118**: Wire plcc-validate-semantic into plcc-make; add e2e test for bad block delimiters
  ([`2af21c1`](https://github.com/ourPLCC/plcc-ng/commit/2af21c1dff815be651d8491932684f826c9334b8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add spec validation pipeline design for issue 118 [skip ci]
  ([`e75c70f`](https://github.com/ourPLCC/plcc-ng/commit/e75c70f94ac267721f4de2063e6aa9fa8b9906b2))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Write implementation plan for spec validation pipeline [skip ci]
  ([`b32529d`](https://github.com/ourPLCC/plcc-ng/commit/b32529d46783d67783c74a5084204ac64768a2b8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Add plcc-validate-lexical command and wire into plcc-make [skip ci]
  ([`cb68a42`](https://github.com/ourPLCC/plcc-ng/commit/cb68a429c7a0a3d8829941eff2a5498f50d4c0f1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add plcc-validate-semantic command [skip ci]
  ([`425d82a`](https://github.com/ourPLCC/plcc-ng/commit/425d82a86a16788a4ca7df82e04cd6b9ff13e0e4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add plcc-validate-syntactic command; wire all validators into plcc-make; fix _REQUIRED hierarchy
  ([`40313c4`](https://github.com/ourPLCC/plcc-ng/commit/40313c41c6437d6850bccbf8c19ac19835f77ccc))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add SemanticSpec deserializer from spec JSON [skip ci]
  ([`7652c75`](https://github.com/ourPLCC/plcc-ng/commit/7652c75e6ffd4469ad904a89633ba915afd58311))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- Upgrade semantic error classes to SpecError with improved messages [skip ci]
  ([`ae57063`](https://github.com/ourPLCC/plcc-ng/commit/ae57063664bd534a1714394937268dbb6b1110e6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Upgrade syntactic validation error classes to SpecError [skip ci]
  ([`3d23cc8`](https://github.com/ourPLCC/plcc-ng/commit/3d23cc8b3a1188a6c25c356dc97285f340d5ce41))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.58.1 (2026-06-26)

### Bug Fixes

- Prevent RecursionError in build_follow_sets on left-recursive grammars
  ([`5cc5a05`](https://github.com/ourPLCC/plcc-ng/commit/5cc5a05a65290a66b6b8a2e70174b70aa54dd701))

_canDeriveEmptyString had no cycle detection, so checking if a nullable nonterminal could derive ε
  would recurse infinitely when its first production expanded into a left-recursive nonterminal
  (e.g., prog **= exp with exp ::= exp PLUS exp). Thread a `computing` set through to break cycles.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.58.0 (2026-06-26)

### Bug Fixes

- **117**: Exclude zero-char candidates from trace table; add test
  ([`656edff`](https://github.com/ourPLCC/plcc-ng/commit/656edff87706c689f815f9a98757b94eb0bb4404))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for issue 117 scan trace output readability [skip ci]
  ([`681e2e2`](https://github.com/ourPLCC/plcc-ng/commit/681e2e2e4e62dcd62d31faf279b43d5870fbc846))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issue 117 scan trace output readability [skip ci]
  ([`30e74be`](https://github.com/ourPLCC/plcc-ng/commit/30e74be52edcb0259b0578dcda02092d79e0e093))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **117**: Add rule_index to matcher attempt records
  ([`6e913fe`](https://github.com/ourPLCC/plcc-ng/commit/6e913fe553e352eb0f2f0359a6be3238ced0379d))

Each match object now tracks its 1-based position in the spec's lexical rule list. This is added to
  attempt dicts as 'rule_index' for downstream display layers.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **117**: Replace scan trace renderer with new block format
  ([`961546b`](https://github.com/ourPLCC/plcc-ng/commit/961546b7d96f74812c4dff1a9041eed27eb0c854))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **117**: Remove unused import and dead conditional in trace renderer
  ([`0c1360b`](https://github.com/ourPLCC/plcc-ng/commit/0c1360bbf9076ca5f7fad3b3ce2089d3cd65a2d6))

Remove unused pytest import from scan_render_test.py. Remove dead conditional in
  _print_candidates_table where char_count > 0 check is unreachable due to earlier continue guard on
  line 45-46.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **117**: Add rule_index assertion to test_attempts_entry_fields
  ([`2f2f5ea`](https://github.com/ourPLCC/plcc-ng/commit/2f2f5ea28acd6de5502745879d901f19fc82ffb3))

- **117**: Update scan --trace bats tests for new output format
  ([`a16d7a5`](https://github.com/ourPLCC/plcc-ng/commit/a16d7a5a26f5f25300e6b72acb536d7c041ff5dc))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.57.0 (2026-06-25)

### Documentation

- Add design spec for issue 116 docopts error message improvement [skip ci]
  ([`7d9c0d1`](https://github.com/ourPLCC/plcc-ng/commit/7d9c0d1dd76925bba5119fc20a20a6bec1a5eebe))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issue 116 docopts error message improvement [skip ci]
  ([`3394942`](https://github.com/ourPLCC/plcc-ng/commit/339494282af12041f35f953219bcaf7e3607f9af))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Move completed issues to done and add 8 new issues from board feedback [skip ci]
  ([`d1baaa1`](https://github.com/ourPLCC/plcc-ng/commit/d1baaa1d17359cdf5b02b775e95613e10d3ecc0a))

- Move 109 and 113 to done/ - Add issues 115-122 based on board member feedback (docopts UX, scan
  trace readability, %%{ syntax error, ^C continuation mode, eof error message, Python rep
  build-failure handling, Python rep wrong output)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Add parse_args wrapper to give clear error messages for bad options (issue 116)
  ([`9987353`](https://github.com/ourPLCC/plcc-ng/commit/99873533b8d4fdbbd841936c007ed6e4ee78b78b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- Migrate all CLI entry points from docopt() to parse_args() (issue 116)
  ([`a57fa79`](https://github.com/ourPLCC/plcc-ng/commit/a57fa790b7fde7c1e377bf66e995ac9679929823))


## v0.56.1 (2026-06-25)

### Bug Fixes

- Correct PlantUML EBNF syntax in syntactic diagram emitter (issue 109)
  ([`cc3f708`](https://github.com/ourPLCC/plcc-ng/commit/cc3f7087fb9d6b7f9fb6634e66fd8c09d518b55b))

Use '=' instead of '::=' and ', ' to concatenate symbols in sequences, matching PlantUML's EBNF
  grammar requirements.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.56.0 (2026-06-25)

### Bug Fixes

- Remove unused _fake_run helper in diagram_test.py (issue 109)
  ([`1756baf`](https://github.com/ourPLCC/plcc-ng/commit/1756bafb666d0710652bac617143edac51f913b1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Remove unused imports in emit_test.py (issue 109)
  ([`40c50ea`](https://github.com/ourPLCC/plcc-ng/commit/40c50ead03dcec5daa21531aa4418087fa804605))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update plcc-diagram-class output paths to build/diagram/class.* (issue 109)
  ([`e5928b4`](https://github.com/ourPLCC/plcc-ng/commit/e5928b49b78eb2dec60f8e40055e2145095cba69))

Changes the orchestrator to write class diagrams to build/diagram/class.puml and
  build/diagram/class.png instead of build/diagram/diagram.* to follow the
  build/diagram/{type}.{ext} convention for all diagram artifacts.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec and issue 114 for syntactic/lexical EBNF diagrams [skip ci]
  ([`14f8202`](https://github.com/ourPLCC/plcc-ng/commit/14f82020a02958db34215c2fcb78f72f91158fe4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for syntactic EBNF diagram (issue 109) [skip ci]
  ([`a630dff`](https://github.com/ourPLCC/plcc-ng/commit/a630dffe362ce0741cad07860444660227467e0f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Add plcc-diagram-syntactic orchestrator and entry points (issue 109)
  ([`6067d84`](https://github.com/ourPLCC/plcc-ng/commit/6067d84f838199bdcb271cb37d7936a099247b2b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add plcc-diagram-syntactic-plantuml-emit (issue 109)
  ([`e8b5d4c`](https://github.com/ourPLCC/plcc-ng/commit/e8b5d4c05359e1818ba9f7edc65863b65e3cd459))

### Testing

- Add bats tests for plcc-diagram-syntactic and update packaging (issue 109)
  ([`b072b55`](https://github.com/ourPLCC/plcc-ng/commit/b072b55b9f1ad3baa42265798fba380abc9493b6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.55.0 (2026-06-25)

### Bug Fixes

- Emit doc example, validate_spec_flag ordering, and list output description (issue 113)
  ([`8c135a1`](https://github.com/ourPLCC/plcc-ng/commit/8c135a186d38209ce4ad2e6a5957219251ccde9e))

Fix plcc-diagram-emit.md Usage block and example to include required --type flag. Move
  validate_spec_flag before VerboseContext construction in plcc-diagram-class to match the
  type-discoverer's ordering. Update author-commands.md plcc-diagram-list description for new
  type/format output.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Restore spec validation and strengthen bats test (issue 113 phase 1) [skip ci]
  ([`3383a1e`](https://github.com/ourPLCC/plcc-ng/commit/3383a1ee5f6a5c283806abef82f42f41958e705a))

Restore validate_spec_flag so plcc-diagram fails fast on a bad --spec path even when no diagram
  types are installed. Fix bats test assertion to check for a distinctive phrase in the help output
  rather than the trivially-true command name.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update packaging test for renamed diagram commands (issue 113)
  ([`c3ab286`](https://github.com/ourPLCC/plcc-ng/commit/c3ab2869689e0ce013faff9e41ef0f88e0e13894))

Replace plcc-plantuml-diagram-* references with the new plcc-diagram-* command names throughout
  packaging.bash.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for issue 113 rename diagram commands [skip ci]
  ([`6f11767`](https://github.com/ourPLCC/plcc-ng/commit/6f117679b45d2efb7158ca8c80a1d01291520c59))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plans for issue 113 phases 1 and 2 [skip ci]
  ([`7a3d0fe`](https://github.com/ourPLCC/plcc-ng/commit/7a3d0fe989a71e90c4ad12445ddf8c984d420bb3))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Rename diagram commands to plcc-diagram-* namespace (issue 113 phase 2)
  ([`e946331`](https://github.com/ourPLCC/plcc-ng/commit/e9463315ca0566bf4295dceda3e668c33fceb7e4))

- Replace plcc-diagram with type-discoverer (issue 113 phase 1) [skip ci]
  ([`52be0e6`](https://github.com/ourPLCC/plcc-ng/commit/52be0e62c57a65a6725f8fef638d39d11c008cf5))


## v0.54.0 (2026-06-24)

### Bug Fixes

- Remove unused urllib.error import from mermaid build
  ([`13461e7`](https://github.com/ourPLCC/plcc-ng/commit/13461e785aeaa6b4f1f42e4c2d5d0147bd48db9f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for issue 111 mermaid build via kroki.io [skip ci]
  ([`3ac6533`](https://github.com/ourPLCC/plcc-ng/commit/3ac6533ba646f608bf8a0e8ab2bedff5b9bbcfd0))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issue 111 mermaid build via kroki.io [skip ci]
  ([`efc4832`](https://github.com/ourPLCC/plcc-ng/commit/efc4832c86125ff77ad369197eabaa00fec7b43d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Render mermaid diagrams via kroki.io instead of mmdc
  ([`a05005e`](https://github.com/ourPLCC/plcc-ng/commit/a05005e38696f7d4f2c4d4723b246d0543baafdb))


## v0.53.0 (2026-06-24)

### Continuous Integration

- Fix tilde expansion, add dist-newstyle restore-keys, and update CONTRIBUTING.md
  ([`d20828a`](https://github.com/ourPLCC/plcc-ng/commit/d20828a15122f5e376439c92211df3492e181b2b))

- Use $HOME instead of ~ in HASKELL_ROUNDTRIP_OUT_DIR env var; GitHub Actions does not expand ~ in
  env: blocks, causing cache path mismatch - Add restore-keys: ${{ runner.os }}-dist-newstyle- to
  the dist-newstyle cache step so any change to haskell_roundtrip.bats does not force a full cold
  Haskell build - Update CONTRIBUTING.md test table: document e2e_haskell_roundtrip.bash, clarify
  functional.bash excludes the Haskell roundtrip, and update all.bash description to reflect it now
  includes the Haskell roundtrip

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Parallelize all test jobs and add venv/cabal/dist-newstyle caches
  ([`c848f7d`](https://github.com/ourPLCC/plcc-ng/commit/c848f7d08aa6581836e9e98c004f8cca50566825))

- Skip CI for doc-only changes via paths-ignore
  ([`0eaab7f`](https://github.com/ourPLCC/plcc-ng/commit/0eaab7fcb834b4ee43e576536f5654cc92fed711))

Adds paths-ignore to the pull_request trigger so pushes that touch only dev-docs/, docs/, top-level
  markdown, or mkdocs config files do not run the test suite. Replaces the manual [skip ci]
  convention.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for issue 110 Haskell roundtrip CI performance [skip ci]
  ([`fb6ff8f`](https://github.com/ourPLCC/plcc-ng/commit/fb6ff8fc2a19431316318d292608646b57b721da))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issue 110 Haskell roundtrip CI performance [skip ci]
  ([`d934504`](https://github.com/ourPLCC/plcc-ng/commit/d934504bb84d96c8ed01d0de4cc82aa256e96144))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Remove [skip ci] convention from CONTRIBUTING.md
  ([`040b32b`](https://github.com/ourPLCC/plcc-ng/commit/040b32b4b2f52dd1552a63101dda01e40d0ec5d3))

CI now skips doc-only PRs automatically via paths-ignore in ci.yml. No manual annotation needed.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update issues and roadmap for 2026-06-24 [skip ci]
  ([`92995d9`](https://github.com/ourPLCC/plcc-ng/commit/92995d9874d5d44799499cf025c9fe47ba2453b3))

Move completed issues 106, 107, 108 to done. Add issues 109 (PlantUML EBNF diagram), 110 (e2e
  Haskell build performance), 111 (Mermaid extension redesign), 112 (v1.0 release prep). Update
  roadmap to 0 open issues.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Add e2e_haskell_roundtrip.bash and exclude roundtrip from e2e suite
  ([`321dc68`](https://github.com/ourPLCC/plcc-ng/commit/321dc688e135e55b58ccf7697ff39fe4eb956335))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- Split haskell.bats into fast emit and slow roundtrip
  ([`e7d99ad`](https://github.com/ourPLCC/plcc-ng/commit/e7d99ade52dbe5a515a6f847a36551d0612f6cb8))


## v0.52.0 (2026-06-24)

### Bug Fixes

- **diagram**: Update bats command test for new plantuml inheritance arrow direction
  ([`39138ae`](https://github.com/ourPLCC/plcc-ng/commit/39138aef2acc344df73c8769a4851bf13405136a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Update e2e test for new plantuml inheritance arrow direction
  ([`5871141`](https://github.com/ourPLCC/plcc-ng/commit/587114183aeaab08e4fff053cd87514b8825b34f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for Haskell language extension documentation (issue 107)
  ([`21c6102`](https://github.com/ourPLCC/plcc-ng/commit/21c610229a4f45f899b8a94660b3730893fc3a04))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add Haskell language extension guide (issue 107)
  ([`b96aeba`](https://github.com/ourPLCC/plcc-ng/commit/b96aeba6c768ed8449aa4af1706d9b862a6f7143))

- Add Haskell to Languages nav and CLI commands in mkdocs.yml
  ([`30c31ea`](https://github.com/ourPLCC/plcc-ng/commit/30c31eaee2b4394719d7d8cf932ef91d865ab83b))

- Add implementation plan for Haskell language extension documentation
  ([`94ccc41`](https://github.com/ourPLCC/plcc-ng/commit/94ccc41ca6c4067e4b4fd6c44e0ce87375db0f7c))

- Add implementation plan for plantuml inheritance arrow direction
  ([`15dc6aa`](https://github.com/ourPLCC/plcc-ng/commit/15dc6aa9f23418bed887b6222a8cee0da2293d9f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add issue 108 and design spec for plantuml inheritance arrow direction
  ([`0cae21a`](https://github.com/ourPLCC/plcc-ng/commit/0cae21a85c1da5904d17f51a7bafc801b662399c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add Java language extension page
  ([`a0aaf00`](https://github.com/ourPLCC/plcc-ng/commit/a0aaf00e795aee849c85c367efc87ce4be4efa7a))

- Add JavaScript language extension page
  ([`151d885`](https://github.com/ourPLCC/plcc-ng/commit/151d885d338eb83595026ea2ef30d998befcd5ba))

- Add Languages nav and JavaScript command docs to mkdocs.yml
  ([`093577f`](https://github.com/ourPLCC/plcc-ng/commit/093577f8f7bff3abbae66547caa2bc7a815d98f8))

- Add plcc-haskell section to language-extensions guide
  ([`2e07122`](https://github.com/ourPLCC/plcc-ng/commit/2e071229f2bc6ea65becf830edadcacb7f0d1ebf))

- Add plcc-haskell-emit/build/run CLI command reference pages
  ([`261ebcb`](https://github.com/ourPLCC/plcc-ng/commit/261ebcbf4a4601e0621cdbf61793caa0ccc6c1f0))

- Add plcc-javascript section to language-extensions guide
  ([`7856f69`](https://github.com/ourPLCC/plcc-ng/commit/7856f692f7d3a7270d625e4639c97f79c87d159b))

- Add plcc-javascript-emit and plcc-javascript-run command reference pages
  ([`337599e`](https://github.com/ourPLCC/plcc-ng/commit/337599e0e1f6feb7a4efb200064062d9c13d1a39))

- Add Python language extension page
  ([`41129b7`](https://github.com/ourPLCC/plcc-ng/commit/41129b708ca8b1104babf90b4cb7932cd7d53fb3))

- Fix Commands table separator in haskell.md
  ([`fdf9231`](https://github.com/ourPLCC/plcc-ng/commit/fdf9231bec46f2028461661b3a1f482f8430c7bc))

- Fix review findings in language pages
  ([`1584621`](https://github.com/ourPLCC/plcc-ng/commit/1584621520bec38dcb62b35b356da0771cd90d3a))

- Reorganize BNF tables to 4-column format with LHS/RHS clarity
  ([`aa3e6dd`](https://github.com/ourPLCC/plcc-ng/commit/aa3e6dd9951edf92cbf3e7cfaf8496568a6e379a))

Fixes the concrete/abstract distinction: a rule with no alt name on the LHS is a concrete rule; a
  rule with an alt name (e.g. <Exp:AddExp>) is an alternative rule that makes the base nonterminal
  abstract. Removes the separate "Token string value" row by folding .lexeme into the captured
  terminal row. Adds an "Example based on spec" column (generated or semantic code snippet)
  alongside the renamed "Example from spec" column.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Slim semantic.md to concepts, link to per-language pages
  ([`89df13e`](https://github.com/ourPLCC/plcc-ng/commit/89df13e347bb4671b664fab99077d8c66eab8064))

- **plan**: Add implementation plan for issue 106 JavaScript language extension docs
  ([`fea564d`](https://github.com/ourPLCC/plcc-ng/commit/fea564de01bddfb857105b5f11c233a3545b09d8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Add design doc for issue 106 JavaScript language extension docs
  ([`70de103`](https://github.com/ourPLCC/plcc-ng/commit/70de10303ab88752928ec6ebec7cd18cc0a9ad01))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Fix canonical example syntax and Node.js version in issue 106 design
  ([`13ccdba`](https://github.com/ourPLCC/plcc-ng/commit/13ccdbafb501d5707d02f53dbf7267820b54c003))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **diagram**: Point plantuml inheritance arrows up (Parent <|-- Child)
  ([`5c2000b`](https://github.com/ourPLCC/plcc-ng/commit/5c2000b19354d1aa078fefba15068771252dba46))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.51.1 (2026-06-24)

### Bug Fixes

- **haskell**: Skip Token runtime tests when hackage package list is absent
  ([`37c6815`](https://github.com/ourPLCC/plcc-ng/commit/37c6815af43a4c4f32226748a5597a616019b7c4))

Replace unconditional @pytest.mark.skip with a skipif that checks whether the hackage package list
  exists. Tests run where cabal has been properly initialized (devcontainer), skip cleanly in CI
  where cabal update has not run.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **haskell**: Unskip Token runtime tests and add missing bytestring dep
  ([`1c1f5ea`](https://github.com/ourPLCC/plcc-ng/commit/1c1f5eabfb264f011bd88a1cdfd3ed2567f31559))

The two cabal-based tests were unconditionally skipped despite cabal being available. The build also
  failed because the cabal template was missing bytestring in build-depends (needed for
  Data.ByteString.Lazy.Char8).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Chores

- Update close-worktree.bash to find worktrees under .claude/worktrees/
  ([`90023de`](https://github.com/ourPLCC/plcc-ng/commit/90023defafa3b3047394fde5af5b1db5b18f66ed))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Close 104 and 105; update roadmap [skip ci]
  ([`c18aa23`](https://github.com/ourPLCC/plcc-ng/commit/c18aa2313b118ceb7abbadec6cbd0c6c61f5f490))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.51.0 (2026-06-24)

### Documentation

- Add design spec and update issue 105 for haskell fragment validation
  ([`b0e2e3d`](https://github.com/ourPLCC/plcc-ng/commit/b0e2e3d7cd85b4b4e73b2fec0924fbc2024cf8c5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for haskell fragment validation
  ([`e562c8d`](https://github.com/ourPLCC/plcc-ng/commit/e562c8d59d16fa6330259d386e5d97f2e4604c58))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **haskell**: Add validate_fragments to detect invalid fragment class names
  ([`7e3d09f`](https://github.com/ourPLCC/plcc-ng/commit/7e3d09f476d40cef9f66baa7086f835031642752))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **haskell**: Wire validate_fragments into emit to enforce fragment class name rules
  ([`9e186bf`](https://github.com/ourPLCC/plcc-ng/commit/9e186bf32432111c89323d734d440fa65fb6b699))


## v0.50.0 (2026-06-23)

### Build System

- Add ghci and cabal to devcontainer
  ([`c7da922`](https://github.com/ourPLCC/plcc-ng/commit/c7da922349e43187eb5f4d4428bea2e3ba779052))

### Chores

- **issues**: Close 066 and 103; add 106 and 107; update roadmap [skip ci]
  ([`d7b2adf`](https://github.com/ourPLCC/plcc-ng/commit/d7b2adf023ae677a964d393988401ffefb22873d))

Move completed issues 066 (JavaScript emitter) and 103 (__run__ docs fix) to done/. Add issues 106
  and 107 for JavaScript and Haskell language extension documentation. Update roadmap to 4 open
  issues.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **java**: Add class fragment support to Java emitter
  ([`34be97b`](https://github.com/ourPLCC/plcc-ng/commit/34be97bbf23ca0abd65c35d8cdaeb6b82c19bb67))

Pass class_fragments to the template and render them on the class declaration line after the extends
  clause, matching the original PLCC's /*Cls:class*/ hook behavior.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.49.0 (2026-06-23)

### Bug Fixes

- **haskell**: Add OverloadedStrings pragma for aeson 2.x compatibility
  ([`ab1f4a5`](https://github.com/ourPLCC/plcc-ng/commit/ab1f4a59963ced16b4ffda5bbba2685142f1d7a3))

aeson 2.x requires Key not String for (.:) and (.=). OverloadedStrings makes string literals
  polymorphic so they satisfy Key where needed.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **haskell**: Dispatch FromJSON on concrete rule_name; remove unused imports
  ([`7476563`](https://github.com/ourPLCC/plcc-ng/commit/74765634949943553a4da476fae65b026d05fa34))

- **haskell**: Emit DuplicateRecordFields pragma to allow shared field labels
  ([`7d7985a`](https://github.com/ourPLCC/plcc-ng/commit/7d7985a41cb57ebad6cfcabd6d7bd5ac3c354bdf))

- **haskell**: Remove unused containers dep from generated cabal file
  ([`3b9a793`](https://github.com/ourPLCC/plcc-ng/commit/3b9a793105b3e1891da1c14e395841f568eeeb7b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **haskell**: Run cabal update in e2e setup for fresh environments
  ([`7a9cd34`](https://github.com/ourPLCC/plcc-ng/commit/7a9cd340310d0229036c6aa550991fa4c0ba7cd7))

cabal build fails if the Hackage package index has never been fetched. Running cabal update in
  setup() makes the test self-contained in CI.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **haskell**: Use abstract class name ExprRest for evalRest fragment
  ([`3c50e47`](https://github.com/ourPLCC/plcc-ng/commit/3c50e47dc6b20170c52ef5822344aac23bc34da3))

In one-module-per-rule, body fragments must be tagged with the abstract class name (ExprRest), not a
  concrete alternative (AddRest). There is no ExprRest.hs — everything for the rule lives in
  ExprRest.hs.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Chores

- **ci**: Trigger
  ([`b4ea10a`](https://github.com/ourPLCC/plcc-ng/commit/b4ea10afdbe5ee6b9091c541fef2826a5982101b))

### Continuous Integration

- Cache cabal store in e2e job to speed up Haskell builds
  ([`e2b591e`](https://github.com/ourPLCC/plcc-ng/commit/e2b591e1388b65cd1b3dcd24bddd137c4311c698))

The first run downloads and compiles aeson's full dependency tree (~38 packages). Caching
  ~/.cabal/packages and ~/.cabal/store keyed on emit.py (which contains the fixed dep list) makes
  subsequent runs fast.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **issues**: #105 haskell fragment concrete class name silently ignored [skip ci]
  ([`1152ba2`](https://github.com/ourPLCC/plcc-ng/commit/1152ba2d329f07eea7634727b4ce5ae93540808c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Add Haskell emitter implementation plan [skip ci]
  ([`66d3f5d`](https://github.com/ourPLCC/plcc-ng/commit/66d3f5d2a3cb8642ba5d5875f9d8d8aedff3e8be))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add Haskell emitter design spec [skip ci]
  ([`744e090`](https://github.com/ourPLCC/plcc-ng/commit/744e0904c7d3cea89f351f8dea51c22b26571f9f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **haskell**: Add extension skeleton and entry points
  ([`c7238c9`](https://github.com/ourPLCC/plcc-ng/commit/c7238c913c0d15973921d7cc7bd7f8ccffc9ee07))

- **haskell**: Add GHC and cabal to devcontainer
  ([`72a656c`](https://github.com/ourPLCC/plcc-ng/commit/72a656c65c89026efe78f38fe1a474af7642ae4e))

- **haskell**: Add Token.hs runtime with parseField helper
  ([`bcff83e`](https://github.com/ourPLCC/plcc-ng/commit/bcff83e64a75ca1849050e904ec63cbbaadfcfec))

- **haskell**: Emit cabal file and copy Token.hs
  ([`79bc432`](https://github.com/ourPLCC/plcc-ng/commit/79bc432ac80af0ede75c78340cc833f318274d13))

- **haskell**: Emit data type declarations per rule module
  ([`171bff4`](https://github.com/ourPLCC/plcc-ng/commit/171bff4d40b724820fbcf17bef680b0e80a137f8))

- **haskell**: Emit FromJSON instances for rule modules
  ([`5751a34`](https://github.com/ourPLCC/plcc-ng/commit/5751a3493dab6d4909dee83ed8b23adc7588929a))

- **haskell**: Emit Main.hs entry point
  ([`9daeec2`](https://github.com/ourPLCC/plcc-ng/commit/9daeec2fc6988a7c86fece300f38bec86ba4ecba))

- **haskell**: Generate default _run for start rule when not provided
  ([`5b7cfcd`](https://github.com/ourPLCC/plcc-ng/commit/5b7cfcd9f6736959705ba18bd376753d82c17922))

- **haskell**: Handle top/import/body/file fragments in emitter
  ([`99ffa0c`](https://github.com/ourPLCC/plcc-ng/commit/99ffa0c6ab7697ed93718f62f9b826c56c8b436a))

### Testing

- **haskell**: Add BATS command and e2e tests
  ([`b339511`](https://github.com/ourPLCC/plcc-ng/commit/b339511448d391193a61e7031507017dcc709439))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **haskell**: Add unit tests for build.py and run.py
  ([`1d493df`](https://github.com/ourPLCC/plcc-ng/commit/1d493df5b56a4f71ae34e801711f00c8ce786445))


## v0.48.0 (2026-06-22)

### Chores

- **issues**: Add 103 - fix __run__ double underscore in language guide overview [skip ci]
  ([`f4c296d`](https://github.com/ourPLCC/plcc-ng/commit/f4c296db318211f92e07c4f128c887a112370eaa))

- **issues**: Move 071, 072, 102 to done; update roadmap to 4 open issues [skip ci]
  ([`6f324b8`](https://github.com/ourPLCC/plcc-ng/commit/6f324b8e27fc4b13b51686a069b2c73e08fd5b4f))

- **issues**: Move 080 to done; update roadmap to 1 open issue [skip ci]
  ([`f2613fd`](https://github.com/ourPLCC/plcc-ng/commit/f2613fdc8ce78d7ecc23601617ac68241ebcd074))

- **issues**: Move 081, 101 to done; update roadmap to 2 open issues [skip ci]
  ([`fc83670`](https://github.com/ourPLCC/plcc-ng/commit/fc83670bb02fa32c24f4aa138d9d764b4376a0b3))

- **roadmap**: Add 103, remove completed 080, update to 2 open issues [skip ci]
  ([`57242ee`](https://github.com/ourPLCC/plcc-ng/commit/57242ee1fb8b47a029f70e4095380c66f18bb5a6))

### Documentation

- Clarify class fragment in JS spec; add issue 104 for Java gap [skip ci]
  ([`4ffd0c8`](https://github.com/ourPLCC/plcc-ng/commit/4ffd0c8fd6a88bce4cf69355dc80890d1134287f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Fix __run__ → _run in overview examples [skip ci]
  ([`44b564c`](https://github.com/ourPLCC/plcc-ng/commit/44b564cc3cf880355ca435774f22ce14a3d84122))

Corrects the Python and Java semantic section examples to use the actual entry point name _run
  (single underscore) instead of __run__ (double).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Add JavaScript emitter implementation plan for issue 066 [skip ci]
  ([`767a604`](https://github.com/ourPLCC/plcc-ng/commit/767a6047ae1b4848e93e38bdf87b19fcc91041ae))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add JavaScript emitter design for issue 066 [skip ci]
  ([`d0b0585`](https://github.com/ourPLCC/plcc-ng/commit/d0b0585a3518104e08c134f452135ced60f3742c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **javascript**: Add emit.py and Jinja2 templates
  ([`044c57e`](https://github.com/ourPLCC/plcc-ng/commit/044c57ecd32d436fdf0e5b83a5414fe79027291f))

Implements the JavaScript emitter: reads model JSON from stdin, writes <ClassName>.js, _Start.js,
  main.js, and runtime/ to --output. Skips SIGINT test due to readline/communicate() race in
  subprocess.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **javascript**: Add run.py and register entry points
  ([`59dc256`](https://github.com/ourPLCC/plcc-ng/commit/59dc256195ffce26a832e4ca72fb68e114ac643e))

- **javascript**: Add runtime deserialize.js
  ([`7853bd1`](https://github.com/ourPLCC/plcc-ng/commit/7853bd12292ec9e06917c2b969bb15cdd46cb945))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **javascript**: Add runtime registry.js
  ([`c5935b7`](https://github.com/ourPLCC/plcc-ng/commit/c5935b7eb279a4f3920e79bca797f03a3614991e))

Implement Registry class with register() and lookup() methods.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **javascript**: Scaffold extension and add runtime base.js
  ([`17cb4fa`](https://github.com/ourPLCC/plcc-ng/commit/17cb4fa53c8cfc1f526eaa3056d4f1b4b69eee28))


## v0.47.2 (2026-06-22)

### Bug Fixes

- **mkdocs**: Add pymdownx.superfences to fix code blocks inside tabs
  ([`196d0ed`](https://github.com/ourPLCC/plcc-ng/commit/196d0ed508c291662f9a49b02c35b82d07e3dc5b))

Without superfences, fenced code blocks inside content tabs render as literal text with the ```
  markers visible instead of as code blocks.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Chores

- **issues**: Move 070 and 098 to done
  ([`3b360c6`](https://github.com/ourPLCC/plcc-ng/commit/3b360c664a77518ca590de6da4b7b6724a05dc0d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 100 to done [skip ci]
  ([`9471bd7`](https://github.com/ourPLCC/plcc-ng/commit/9471bd7317a3821da8d3f1c6aacc043f0454d4b0))

PR #221 implemented the CLI command classification and reference pages that issue 100 designed.

### Documentation

- **acknowledgments**: Add acknowledgments page placeholder [skip ci]
  ([`6934a6f`](https://github.com/ourPLCC/plcc-ng/commit/6934a6f5551f8730dcb7c5b79c9ff48deb3a9ace))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **acknowledgments**: Fill in contributors, institutions, and dependencies [skip ci]
  ([`e2a3d40`](https://github.com/ourPLCC/plcc-ng/commit/e2a3d40575e8a61201f059162ebcfb9e11cd0bb5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Restructure directories and nav for issue 100 [skip ci]
  ([`ab49034`](https://github.com/ourPLCC/plcc-ng/commit/ab490346ffa50fb474bde0a1379e27c09829541e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Write author-facing commands guide page [skip ci]
  ([`be44b6a`](https://github.com/ourPLCC/plcc-ng/commit/be44b6a274be3df63bc9ad742bb756f10e7ae390))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Write CLI landing page [skip ci]
  ([`29aa662`](https://github.com/ourPLCC/plcc-ng/commit/29aa66243014273295898ace8593198c0548eb84))

- **cli**: Write core pipeline reference pages [skip ci]
  ([`70599df`](https://github.com/ourPLCC/plcc-ng/commit/70599df1d93ed6ec2c50cd58c3a8249623497de4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Write diagram extension reference pages [skip ci]
  ([`bd4ea8b`](https://github.com/ourPLCC/plcc-ng/commit/bd4ea8b7a298276a02a3669588d10dd6480af014))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Write discovery and utility reference pages [skip ci]
  ([`d8ec4c6`](https://github.com/ourPLCC/plcc-ng/commit/d8ec4c6570960ac0551633cda8908343e7e91b0b))

- **cli**: Write extension guide pages [skip ci]
  ([`58a3345`](https://github.com/ourPLCC/plcc-ng/commit/58a33459b25e3258068c9622a4b61d9fabbd4cd3))

- **cli**: Write lang dispatch reference pages [skip ci]
  ([`284d199`](https://github.com/ourPLCC/plcc-ng/commit/284d1992657559faf6eb957838df3cdc01fb464a))

- **cli**: Write language extension reference pages [skip ci]
  ([`f30d839`](https://github.com/ourPLCC/plcc-ng/commit/f30d839a0b7e2f9ca7e2bbe61ec9bc9589f7c7ef))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Write plcc-diagram package reference pages [skip ci]
  ([`bcf78f0`](https://github.com/ourPLCC/plcc-ng/commit/bcf78f02fde2bc1149cb9397ce355f40d3ba9638))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Write plcc-make reference page [skip ci]
  ([`1e071de`](https://github.com/ourPLCC/plcc-ng/commit/1e071dee572d4a238cfda32af808d641058a7760))

- **cli**: Write plcc-parser-table reference page [skip ci]
  ([`4893159`](https://github.com/ourPLCC/plcc-ng/commit/489315995892c10128985812fa048b2de1b92bbc))

- **cli**: Write plcc-scan, plcc-parse, plcc-rep reference pages [skip ci]
  ([`928ff4a`](https://github.com/ourPLCC/plcc-ng/commit/928ff4a5502a04feaa166cee811496d25a7b5c3b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Write under-the-hood guide page [skip ci]
  ([`d7a1780`](https://github.com/ourPLCC/plcc-ng/commit/d7a1780c45e1888214479a3986dd93cf5d5b3a51))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **examples**: Remove explicit plcc-make build step [skip ci]
  ([`3c2f6d0`](https://github.com/ourPLCC/plcc-ng/commit/3c2f6d0203dc430ea2d5abf21cd642860fab955a))

- **installation**: Add installation page with upgrade, pinning, and uninstall [skip ci]
  ([`443182c`](https://github.com/ourPLCC/plcc-ng/commit/443182c260c77c9818c0351bfe124cad6c95e72e))

- **issues**: Add 101 acknowledgments page [skip ci]
  ([`1a43ac5`](https://github.com/ourPLCC/plcc-ng/commit/1a43ac5b497b3bf28314da6febb231800567a52c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 102 migration guide from PLCC to PLCC-ng [skip ci]
  ([`e83118b`](https://github.com/ourPLCC/plcc-ng/commit/e83118bf90ff8aa7241161ef2c8c4f21b40f8324))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add roadmap for 14 open issues [skip ci]
  ([`5a73a19`](https://github.com/ourPLCC/plcc-ng/commit/5a73a19cc9fbf780bd0d69026d1e8dfda50f053a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Integrate 101 and 102 into roadmap [skip ci]
  ([`07341b0`](https://github.com/ourPLCC/plcc-ng/commit/07341b0f8af285b0bbd1ef48ed42fb4b1e4ea5f6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Resolve phase 1 decisions and close already-done issues
  ([`156e8ab`](https://github.com/ourPLCC/plcc-ng/commit/156e8abaa57144110bff648cd4a7c146255fb32b))

- #100: record CLI command classification decision and doc structure - #083: close (absorbed by
  #100) - #079: close (keep PlantUML via Kroki; Mermaid easy to add later if needed) - #074: close
  (plcc-make already removed from quickstart; output already verified) - #076: close (home page has
  no install redundancy) - #077: close (licensing already on home page) - #073: close (Java JDK
  already in prerequisites) - #078: close (CC BY-SA 4.0 already stated on home page) - #099: close
  (repo_url already configured in mkdocs.yml)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Add Java tab to overview grammar example
  ([`a785e9a`](https://github.com/ourPLCC/plcc-ng/commit/a785e9adb168ca816631aea687bf5d5bfa99e61e))

- **language-guide**: Add Java tab to subtract.plcc example
  ([`7645e07`](https://github.com/ourPLCC/plcc-ng/commit/7645e07f6bf6e923caf1722d16b6f60af5a4dd3a))

- **language-guide**: Add Java tabs to semantic section examples
  ([`f748d59`](https://github.com/ourPLCC/plcc-ng/commit/f748d59243f79143e3859df8a3443c325c71dba5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **migration**: Add migration guide from PLCC to PLCC-ng [skip ci]
  ([`63fe25e`](https://github.com/ourPLCC/plcc-ng/commit/63fe25ec9ab623553aba396e4d692d72a280ea4f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **migration**: Fix missing first step in JSON parse tree pipeline [skip ci]
  ([`52a2d52`](https://github.com/ourPLCC/plcc-ng/commit/52a2d5201e77f37c80a91e0d76692b0ebd1f7cc0))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **mkdocs**: Enable content tabs feature and pymdownx.tabbed extension
  ([`a1d6812`](https://github.com/ourPLCC/plcc-ng/commit/a1d6812017d0624fc7709c48449daefe1579bc85))

- **plan**: Add implementation plan for issue 081 [skip ci]
  ([`8fca8c6`](https://github.com/ourPLCC/plcc-ng/commit/8fca8c61fdf38664ff1bd863dfa693ae55698960))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plan**: Add implementation plan for issue 101 acknowledgments page [skip ci]
  ([`c1a8538`](https://github.com/ourPLCC/plcc-ng/commit/c1a85380026087cc5ac19bba264c848da80ae57b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Add implementation plan for installation page and migration guide [skip ci]
  ([`2e59e9e`](https://github.com/ourPLCC/plcc-ng/commit/2e59e9e8f2d6362994da0b778725320b360906c9))

Covers issues 071, 072, and 102.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **quick-start**: Add Java tab to semantic section example
  ([`7d374d1`](https://github.com/ourPLCC/plcc-ng/commit/7d374d144a93d53e6c253b76d5c45bb7f4bc19a4))

- **quick-start**: Rename getting-started to quick-start [skip ci]
  ([`5592e69`](https://github.com/ourPLCC/plcc-ng/commit/5592e696a33bab4d628155eeef0b82dfe17da4eb))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **roadmap**: Update to reflect 7 open issues after #100 done [skip ci]
  ([`ee6a751`](https://github.com/ourPLCC/plcc-ng/commit/ee6a751fc80f3dad807f7750cbced4ec14c5adbc))

Phase 1 (CLI reference) is complete. Renumber remaining phases and update the issue count and date.

- **roadmap**: Update to reflect current open issues [skip ci]
  ([`9c82dfc`](https://github.com/ourPLCC/plcc-ng/commit/9c82dfcafc003f1e8606b8200266a3274ebc1757))

Remove resolved issues, renumber phases, and update issue count to 8. Phase 1 structural decisions
  are all resolved; roadmap now starts with implementing the #100 CLI classification decision.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Add design doc for issue 081 plcc-make removal from examples [skip ci]
  ([`a5aaf58`](https://github.com/ourPLCC/plcc-ng/commit/a5aaf582df1784d8dd5efb685aeed66e39496330))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Add design doc for issue 101 acknowledgments page [skip ci]
  ([`9cbb69a`](https://github.com/ourPLCC/plcc-ng/commit/9cbb69afbcf73ecd4661398052d9c9839fd664ed))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add CLI restructure design for issue 100 [skip ci]
  ([`fc250dc`](https://github.com/ourPLCC/plcc-ng/commit/fc250dcbdb8a16eb2d2fec123aef136c0955c158))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add design for installation page and PLCC migration guide [skip ci]
  ([`cc5bbee`](https://github.com/ourPLCC/plcc-ng/commit/cc5bbeeacabadcba1a0fa7a43f045a18112ed73d))

Covers issues 071 (upgrade instructions), 072 (version pinning), and 102 (migration guide from PLCC
  to PLCC-ng).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add design spec for issue 080 tabbed code blocks [skip ci]
  ([`7c16962`](https://github.com/ourPLCC/plcc-ng/commit/7c169623f1bdc31f9079bb4569cb5a228b8226ce))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add implementation plan and update spec for issue 080 tabbed code blocks [skip ci]
  ([`ee671e7`](https://github.com/ourPLCC/plcc-ng/commit/ee671e770cc6ca153060b358a4e7a2b9903f9262))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **superpowers**: Add implementation plan for CLI doc restructure [skip ci]
  ([`dafed24`](https://github.com/ourPLCC/plcc-ng/commit/dafed2417b49093b33aada92fc45834168d89676))


## v0.47.1 (2026-06-19)

### Bug Fixes

- **098**: Replace readline with read1 so one ^D submits partial line
  ([`1711e01`](https://github.com/ourPLCC/plcc-ng/commit/1711e014c6de6e72bdb2745bd69b8f253511cf03))

On a real TTY in canonical mode, readline() blocks after the first ^D flushes buffered content
  because it loops calling read() until it sees a newline or an empty read. A second ^D was required
  to produce the empty read that caused readline() to return. read1(65536) makes exactly one OS
  read() call and returns immediately with whatever was flushed.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **098**: Design spec for ^D partial-line regression fix [skip ci]
  ([`1291836`](https://github.com/ourPLCC/plcc-ng/commit/129183647cc80d0ac0284b574d65104ce4b4c23b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **098**: Implementation plan for ^D partial-line fix [skip ci]
  ([`e911059`](https://github.com/ourPLCC/plcc-ng/commit/e911059d4c9a9c3ec3f143965b0866c3a58d03c8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.47.0 (2026-06-19)

### Chores

- **096**: Guard setup in commands, integration, e2e with SKIP_SETUP
  ([`3774519`](https://github.com/ourPLCC/plcc-ng/commit/37745191c4e4e81fdaa4ea311fdddf92c694f8eb))

- **096**: Guard setup in units.bash with SKIP_SETUP
  ([`0fec840`](https://github.com/ourPLCC/plcc-ng/commit/0fec8408cccfaa23e8aa21672a1b7f14f390115a))

- **096**: Hoist setup into functional.bash; pass SKIP_SETUP=1 to leaf scripts
  ([`8c09c47`](https://github.com/ourPLCC/plcc-ng/commit/8c09c47148c51244d24cbb491deee635c625630f))

- **ci**: Trigger
  ([`0fa49b4`](https://github.com/ourPLCC/plcc-ng/commit/0fa49b407e491dc165d5bb673c852c7cb9720dcd))

### Documentation

- **096**: Add design spec for hoisting test setup [skip ci]
  ([`2b80e11`](https://github.com/ourPLCC/plcc-ng/commit/2b80e11a955582b0dd77c73345c58d467bd2ce89))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **096**: Add implementation plan for hoisting test setup [skip ci]
  ([`e8663a7`](https://github.com/ourPLCC/plcc-ng/commit/e8663a734f5a76fd19a58d32cf8b70825cdc67f5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **096**: Clarify plan constraint scope; note pre-existing typo [skip ci]
  ([`2d4253d`](https://github.com/ourPLCC/plcc-ng/commit/2d4253df3170f085f61a0917a7e3ec95efae37af))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 100 for CLI command classification discussion [skip ci]
  ([`d8027be`](https://github.com/ourPLCC/plcc-ng/commit/d8027be99e8481b2aff33bfdb8a8e717a294b08e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 096 and 097 to done [skip ci]
  ([`579d19a`](https://github.com/ourPLCC/plcc-ng/commit/579d19a7168f64cbc835fcbbc0acb491321ffdfb))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Add dark mode implementation plan [skip ci]
  ([`35eb4d4`](https://github.com/ourPLCC/plcc-ng/commit/35eb4d4b929652509be630f35dc857646c48626d))

- **specs**: Add dark mode design for issue 070 [skip ci]
  ([`1b27077`](https://github.com/ourPLCC/plcc-ng/commit/1b27077197848441cf1c9ae57203cbf0fe4989ad))

### Features

- **docs**: Add dark mode with system-preference detection and toggle
  ([`669d763`](https://github.com/ourPLCC/plcc-ng/commit/669d763d566cc8ef34710d2738115f9332efe42e))


## v0.46.1 (2026-06-18)

### Bug Fixes

- **097**: Use PIPESTATUS to eliminate exit-code race in run_cached
  ([`0c15039`](https://github.com/ourPLCC/plcc-ng/commit/0c150398cdaaca96eaa44b9d70a0470ddc4ce353))

Replaced the temp-file approach to capture exit codes with PIPESTATUS, which is more reliable and
  eliminates the race condition where the temp file write in a subshell might not be visible to the
  parent before reading. The fix:

- Removed mktemp and rm of _exit_tmp temp file - Removed trap on EXIT (no longer needed) - Added set
  -o pipefail inside run_cached to enable PIPESTATUS[0] access - Changed pattern from '{ "$@" 2>&1;
  echo "$?" > file }' to '"$@" 2>&1 | tee output || exit_code=PIPESTATUS[0]'

This is safe because callers source this file into scripts with set -euo pipefail active, but the
  function itself now explicitly sets pipefail to handle both cases correctly.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Continuous Integration

- **097**: Disable test output cache in CI with PLCC_NO_TEST_CACHE
  ([`207f5d7`](https://github.com/ourPLCC/plcc-ng/commit/207f5d76a3a884f57d5328667ec921ed50edcabb))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **097**: Add test output cache design spec [skip ci]
  ([`af42838`](https://github.com/ourPLCC/plcc-ng/commit/af428382f7752afe8e03faea3e345817e9955b41))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **097**: Add test output cache implementation plan [skip ci]
  ([`cfa749a`](https://github.com/ourPLCC/plcc-ng/commit/cfa749acc1dad9564b7df4564a57356452854785))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **097**: Update spec — rename env var, add CI update [skip ci]
  ([`e078749`](https://github.com/ourPLCC/plcc-ng/commit/e0787493b667733e12c9e1d2810becb8646c8f4c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 098 for ^D on non-empty line in plcc-rep [skip ci]
  ([`a85aeae`](https://github.com/ourPLCC/plcc-ng/commit/a85aeaec3a7bffe1e2fb745b772a95edd31a49a5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 099 for link from docs to source repository [skip ci]
  ([`3b4de2f`](https://github.com/ourPLCC/plcc-ng/commit/3b4de2ff4394998d0f2b89ed18a705189007eabc))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 093 to done [skip ci]
  ([`6a537a7`](https://github.com/ourPLCC/plcc-ng/commit/6a537a77d4561b6ab4efc35006dde90daa7d118e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **097**: Wrap composite test scripts with run_cached
  ([`7282014`](https://github.com/ourPLCC/plcc-ng/commit/7282014962677365887a87cd14af492a1492abf6))

- **097**: Wrap simple test scripts with run_cached
  ([`e864274`](https://github.com/ourPLCC/plcc-ng/commit/e864274cd2a61dd6437e16b322ceb7ef44e09066))

### Testing

- **097**: Add _cache.bash with run_cached helper
  ([`b3dfea6`](https://github.com/ourPLCC/plcc-ng/commit/b3dfea695d7f90ee89b32b28846a33f4193b28a1))

- **097**: Add cache management scripts and document test output cache
  ([`16349fa`](https://github.com/ourPLCC/plcc-ng/commit/16349fa4661ad1f67f6d5f83cf4f3caecc9fba68))

- **097**: Add cache/stats.bash summary script
  ([`ac5f79d`](https://github.com/ourPLCC/plcc-ng/commit/ac5f79dfe4e8e240617d7b1e52e2ff900ee517ef))

- **097**: Fix fallback test; sync docs to final file layout [skip ci]
  ([`d498f3e`](https://github.com/ourPLCC/plcc-ng/commit/d498f3eb16b7389f19e774e9f43614b616c6926a))

- Shadow git with a failing stub so the fallback path is deterministically exercised and assert no
  cache files are written - Update spec and plan docs to reference bin/test/cache/stats.bash (moved
  from bin/test/cache-stats.bash) and correct script count from six to seven

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.46.0 (2026-06-18)

### Bug Fixes

- **093**: Add same-line split e2e test and tighten plcc-rep assertion
  ([`ab6ca5d`](https://github.com/ourPLCC/plcc-ng/commit/ab6ca5d6db2b0f1f37ccb634a2050fd876c3633b))

- Add test case for same-line split: multiple sentences on one line should produce multiple parse
  trees - Tighten plcc-rep two-sentence test to assert exact output lines (3 and 4) instead of weak
  substring match

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: Gate hold-marker emission on --hold-markers flag
  ([`52e7484`](https://github.com/ourPLCC/plcc-ng/commit/52e7484c58bed8e572b10955601c0379899fa38c))

plcc-trees now only emits hold markers when called with --hold-markers. TreePipeline passes this
  flag so orchestrators keep incremental behavior. Direct plcc-trees consumers (e.g. standalone test
  harnesses) see the old byte-identical output without the extra hold record.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: Plcc-trees forwards --hold-markers to parser plugin
  ([`57c5100`](https://github.com/ourPLCC/plcc-ng/commit/57c51000e2dbc8596a7412c72766b047beb36d5a))

TreePipeline passes --hold-markers to plcc-trees, but plcc-trees was not accepting or forwarding the
  flag to plcc-parser-table. Add the flag to plcc-trees and forward it, restoring normal pipeline
  output.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: Scanhandler.feed returns bytes remainder not bool
  ([`3f828f0`](https://github.com/ourPLCC/plcc-ng/commit/3f828f03611cf0176a78d909460de15e54c7322e))

SourceRunner._incremental concatenates the returned remainder with the next line as bytes. Returning
  True caused TypeError on the next input.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

### Documentation

- **093**: Design for incremental parsing in interactive mode [skip ci]
  ([`27d4dfe`](https://github.com/ourPLCC/plcc-ng/commit/27d4dfea87cbedf6d2074bf8be79a836abd34d1a))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: Document incremental interactive mode and ^D [skip ci]
  ([`96e8922`](https://github.com/ourPLCC/plcc-ng/commit/96e8922952dc22adebe0fcbb70da3319071501b5))

Add Interactive mode paragraphs to both plcc-parse and plcc-rep sections describing line-by-line
  evaluation, the >>> and ... prompts, and the single-press ^D behavior (exit at empty buffer;
  force-submit at continuation).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: Implementation plan for incremental parsing [skip ci]
  ([`82daa00`](https://github.com/ourPLCC/plcc-ng/commit/82daa00e23a5f388c9c6c35d4abdb55691df0e14))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: Note docs responsibility for orchestrators.md [skip ci]
  ([`b28f9d3`](https://github.com/ourPLCC/plcc-ng/commit/b28f9d318e5fa1b1fc3055598f5c5898fd17e19c))

- **094**: Add design spec for docs follow-up [skip ci]
  ([`f0d348a`](https://github.com/ourPLCC/plcc-ng/commit/f0d348a519d5e2c71faa993f6b788e572c59303d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **094**: Add implementation plan [skip ci]
  ([`7e18670`](https://github.com/ourPLCC/plcc-ng/commit/7e1867046184584303c692d38d586cf86107fd87))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **094**: Document plcc-ll1 and fix plcc-trees example [skip ci]
  ([`d454699`](https://github.com/ourPLCC/plcc-ng/commit/d45469967dd927eed450467b86ee1f181cba420d))

- **094**: Fix plcc-trees pipeline example (plcc-tokens needs file, not stdin) [skip ci]
  ([`6606ce2`](https://github.com/ourPLCC/plcc-ng/commit/6606ce2c79270083d8d4333fd4accb74906f364a))

- **094**: Remove --tool from plcc-rep (095) [skip ci]
  ([`814a889`](https://github.com/ourPLCC/plcc-ng/commit/814a889fb8d93543293191aee941856b6ad8ff45))

- **094**: Remove < /dev/null workaround; files-only means no interactive mode [skip ci]
  ([`73d3ae6`](https://github.com/ourPLCC/plcc-ng/commit/73d3ae60446f80936228fc8418d9f02876c99b1e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **094**: Update examples for 089+095, verify all output [skip ci]
  ([`da9d373`](https://github.com/ourPLCC/plcc-ng/commit/da9d37375f3a597246e9771cbb17db2607143d48))

- **094**: Update semantic.md for 095 section format [skip ci]
  ([`10c5f08`](https://github.com/ourPLCC/plcc-ng/commit/10c5f08f66cd523b4dfaf7a4b75ddb9593b76d02))

- **issues**: Move 094 to done [skip ci]
  ([`511c1cf`](https://github.com/ourPLCC/plcc-ng/commit/511c1cf67ca5407939c220aafc3d9ce5bfbfe9f7))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 095 to done [skip ci]
  ([`94254cc`](https://github.com/ourPLCC/plcc-ng/commit/94254ccf9d550d25c8032e2a9604fc4e429a01f9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **093**: Add commit/hold split helper
  ([`41019ba`](https://github.com/ourPLCC/plcc-ng/commit/41019ba4c09870b7195ac5c2e960550b38f85b78))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: E2e tests for multi-sentence pipe parsing; fix scan SubmitOn import
  ([`fdeeaee`](https://github.com/ourPLCC/plcc-ng/commit/fdeeaee1aa18e60ea0bc17ef027527a0f8669b0a))

Add bats tests verifying that piping multiple newline-separated sentences to plcc-parse and plcc-rep
  produces one result per sentence (incremental split_committed with eof=True). Also fix scan.py and
  scan_test.py which still imported the removed SubmitOn enum from source_runner after task 5
  refactored it away.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: Emit hold marker and incomplete-fragment start
  ([`4708cb9`](https://github.com/ourPLCC/plcc-ng/commit/4708cb972936db7b944eb0b489f36d7d8a0fc50e))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: Handlers return remainder bytes
  ([`21acf94`](https://github.com/ourPLCC/plcc-ng/commit/21acf94dbd76977d39e3f258a011f4d3dc018e25))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: Incremental SourceRunner with single-press ^D
  ([`6cb3fe4`](https://github.com/ourPLCC/plcc-ng/commit/6cb3fe4c97db7d680b2ca23160438fd219345668))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: Parser reports sentence extensibility
  ([`7169672`](https://github.com/ourPLCC/plcc-ng/commit/7169672c180ce773399def898bfc89cc4a312312))

The parse() function now returns a third value, extensible, indicating whether the parser stopped at
  eof where real terminals could have continued the sentence. This enables incremental parsing and
  completion. Tests added for extensibility detection in nullable tails and arbno.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>

- **093**: Wire orchestrators to incremental runner
  ([`4cd24c4`](https://github.com/ourPLCC/plcc-ng/commit/4cd24c4bcbc838be5c724d243848b407bf6e04f1))

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>


## v0.45.1 (2026-06-17)

### Bug Fixes

- **cd**: Update smoke test from --grammar to --spec
  ([`d85e841`](https://github.com/ourPLCC/plcc-ng/commit/d85e841bd750e315f8ffbe52c5c57424ea1ee003))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.45.0 (2026-06-17)

### Bug Fixes

- **095**: Add language name path-traversal guard; clean stale tool key in fixture
  ([`221a77c`](https://github.com/ourPLCC/plcc-ng/commit/221a77ca592961506bc243f991102982e36a7327))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **095**: Update inline spec in plcc-parse-errors.bats to new format [skip ci]
  ([`1a799e9`](https://github.com/ourPLCC/plcc-ng/commit/1a799e91533dcbc9801fa2c1e9fbb4c5cb846bd9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **095**: Update test fixtures and bats tests to new semantic section format
  ([`ba0fd1a`](https://github.com/ourPLCC/plcc-ng/commit/ba0fd1aa9953ca1fa7f475e40273ac55ff50f15b))

All fixture .plcc files used the old '% tool Language' divider syntax. The new format uses a bare
  '%' divider with the language name as the first line of the section body. Also removes '--tool='
  flags from plcc-rep bats tests and updates output dir assertions from 'build/calculate' to
  'build/Python'.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **ci**: Trigger
  ([`c12c24d`](https://github.com/ourPLCC/plcc-ng/commit/c12c24d4d53694430c23a3fd6d8683f4edd0b2b4))

### Documentation

- **089**: Add design spec for phases 3 & 4 of grammar-to-spec rename [skip ci]
  ([`b3ac48f`](https://github.com/ourPLCC/plcc-ng/commit/b3ac48fbb91323d68449ad40dcbfaf060e254a0e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **089**: Add implementation plan for phases 3 & 4 [skip ci]
  ([`e107235`](https://github.com/ourPLCC/plcc-ng/commit/e107235fc431d4690edfa073b4ddef68d8db27a5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **089**: Fix --no-banner → -b/--banner in CLI docs and plan [skip ci]
  ([`c0d3b25`](https://github.com/ourPLCC/plcc-ng/commit/c0d3b25cc856b1f6b68e096dc762faf61121b483))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **089**: Update docs grammar-file references to spec-file [skip ci]
  ([`271ee10`](https://github.com/ourPLCC/plcc-ng/commit/271ee1079bfda0eb2fededc385a4b057c030cd7e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **095**: Add semantic section redesign implementation plan [skip ci]
  ([`f81cc44`](https://github.com/ourPLCC/plcc-ng/commit/f81cc44905c6676580aa2c046f2da651c04d51e6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **095**: Add semantic section redesign spec [skip ci]
  ([`99eeb7f`](https://github.com/ourPLCC/plcc-ng/commit/99eeb7fa9a7a61a70c6c9b4dc10a018c46055f83))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 096 and 097 for test infrastructure improvements [skip ci]
  ([`3b79d97`](https://github.com/ourPLCC/plcc-ng/commit/3b79d971d86388fd5435545f46edeadf087b108d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 085, 086, and 089 to done [skip ci]
  ([`95ff879`](https://github.com/ourPLCC/plcc-ng/commit/95ff879bdc9f3ecee31d18f0c015959c4e56af7a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **095**: Enforce single semantic section; Spec.semantics is now SemanticSpec | None
  ([`5d8725e`](https://github.com/ourPLCC/plcc-ng/commit/5d8725e115f4c17009025989c76bf8635e99026f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **095**: Plcc-make uses language name as output dir, removes validate_tool_name
  ([`f1d35fe`](https://github.com/ourPLCC/plcc-ng/commit/f1d35fe2d02853ca6c28ad7cd4358fe9339c434a))

- **095**: Plcc-rep removes --tool flag, reads language from spec semantics
  ([`312360f`](https://github.com/ourPLCC/plcc-ng/commit/312360fc689b6ccdd27be66826e37d47a5e6aadf))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **095**: Simplify Divider and extract language from semantic section body
  ([`e79bddf`](https://github.com/ourPLCC/plcc-ng/commit/e79bddf13e9d9b5e78fc090176591b55fea8ed1a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **095**: Update spec/model schemas and build_model — semantics is nullable object, no tool
  ([`91d986f`](https://github.com/ourPLCC/plcc-ng/commit/91d986fc4f5867c13170a19079c80e75c79ab7af))

### Refactoring

- **089**: Rename build/grammar → build/spec, .grammar → .spec
  ([`1517e3e`](https://github.com/ourPLCC/plcc-ng/commit/1517e3e21b11317630f192dd4ca954ff511fc97b))

- **089**: Rename cmd/grammar → cmd/spec and its symbols
  ([`21ebbd9`](https://github.com/ourPLCC/plcc-ng/commit/21ebbd9aeacf6262d1ba94ea74064bc622e6aed6))

- **089**: Update consumer test files to use build/spec and cmd/spec
  ([`ed242bc`](https://github.com/ourPLCC/plcc-ng/commit/ed242bc2f954b066ff80917a89621dc490466b11))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **089**: Update make.py to use build/spec and cmd/spec
  ([`3064f4b`](https://github.com/ourPLCC/plcc-ng/commit/3064f4b625f61fe38891d0c82be4a4300f2f8fb8))

- **089**: Update scan, parse, rep, diagram to use build/spec and cmd/spec
  ([`b9b9b35`](https://github.com/ourPLCC/plcc-ng/commit/b9b9b3532bbfc17466f48ba7e96f816e7362e0f5))

- **095**: Add error messages and tighten type annotation per code review
  ([`8f25c89`](https://github.com/ourPLCC/plcc-ng/commit/8f25c89719423c1b81e1968db5eb32732541c825))

- UnexpectedTokensOnDividerError: add message explaining bare-% rule -
  MissingLanguageDeclarationError: add message explaining language-name placement -
  MultipleSemanticsError: add message stating only one section is allowed - parse_semantic_spec:
  narrow parameter type from list to list[Divider|Line|Block] - parse_semantic_spec_test: remove
  unused LanguageDeclaration import

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **089**: Rename stale grammar→spec in make_test.py function names
  ([`5f9aa9c`](https://github.com/ourPLCC/plcc-ng/commit/5f9aa9c39957d19c5114f2507d9855d60f804fae))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **089**: Update bats tests to use .spec instead of .grammar
  ([`354e10c`](https://github.com/ourPLCC/plcc-ng/commit/354e10cdb5f0ecff751c02a20d1b5bd826d93667))

Replace all references to build/.grammar with build/.spec in the plcc-make bats test file, including
  test names, assertions, and the seeded file used by the stored-spec-missing test.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.44.0 (2026-06-16)

### Documentation

- **089**: Add design spec for phases 1 & 2 of grammar-to-spec rename [skip ci]
  ([`a60a8a4`](https://github.com/ourPLCC/plcc-ng/commit/a60a8a441381a5938f1334715e283d14c4f935cc))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **089**: Add grammar CLI refactor design spec [skip ci]
  ([`e8c607e`](https://github.com/ourPLCC/plcc-ng/commit/e8c607ec9273965d45ce4bacec4db44fe74391aa))

- **089**: Add grammar CLI refactor implementation plan [skip ci]
  ([`b24486e`](https://github.com/ourPLCC/plcc-ng/commit/b24486e1523c29864a85f0a06b52c34cb4ef6e94))

- **089**: Add implementation plan for phases 1 & 2 [skip ci]
  ([`0604913`](https://github.com/ourPLCC/plcc-ng/commit/06049132f736f88a01833a550ed98bc9a0a95818))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **089**: Correct design spec per code review [skip ci]
  ([`12e81e8`](https://github.com/ourPLCC/plcc-ng/commit/12e81e84b99c1d31bd82b32560fa0467860684a6))

- **issues**: Move 084 and 088 to done [skip ci]
  ([`8978a7d`](https://github.com/ourPLCC/plcc-ng/commit/8978a7dde43b5640857499cb182b23328f985001))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **089**: Fix stale 'grammar banner' in make --help text
  ([`a46c2a0`](https://github.com/ourPLCC/plcc-ng/commit/a46c2a0c67072d4f1af4482df0132a0fb04cf0c4))

- **089**: Rename CLI flag --grammar/-g → --spec/-s
  ([`8216e72`](https://github.com/ourPLCC/plcc-ng/commit/8216e724b3324ba1ae0c4380f32a2672a26eeff9))

- **089**: Rename default spec file grammar.plcc → spec.plcc
  ([`92b5e5a`](https://github.com/ourPLCC/plcc-ng/commit/92b5e5a6836f9f64dfb18473087617f9d66d0d3b))

- **089**: Update banner test assertions grammar: → spec:
  ([`ebe21e7`](https://github.com/ourPLCC/plcc-ng/commit/ebe21e714525966bf565a936825d1da8289e0e73))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **089**: Update help text in scan, parse, rep, diagram docstrings
  ([`4e7c133`](https://github.com/ourPLCC/plcc-ng/commit/4e7c13368d5f979f597562251dfcb610fc7a7f0b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **089**: Update make error messages, banner, and default spec filename
  ([`2cb1fa1`](https://github.com/ourPLCC/plcc-ng/commit/2cb1fa1c23a174cdb0313a8c8b2160d34ec21caf))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **089**: Update rep error message and remaining stale test assertions
  ([`b6fba4c`](https://github.com/ourPLCC/plcc-ng/commit/b6fba4c123de4fdc81738a035d9e0502f510b746))

### Refactoring

- **build**: Add DEFAULT_GRAMMAR_FILE and resolve_grammar_path
  ([`580a078`](https://github.com/ourPLCC/plcc-ng/commit/580a078cf5ec9f2c9e488b48c0dd0d5980094574))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **build**: Fix import placement in grammar_test.py
  ([`13307d4`](https://github.com/ourPLCC/plcc-ng/commit/13307d4f902dcedd0b9b66197b71291fb476c10d))

- **cmd**: Add shared grammar CLI helpers
  ([`d265700`](https://github.com/ourPLCC/plcc-ng/commit/d265700aaa4e3423cf293388caac2c8d3b8954c0))

- **diagram**: Use shared grammar CLI helpers
  ([`3a7f7cc`](https://github.com/ourPLCC/plcc-ng/commit/3a7f7cc6b4f5eda548994f3257f6b46c2a668662))

- **make**: Use resolve_grammar_path and GRAMMAR_OPTION
  ([`4cddb25`](https://github.com/ourPLCC/plcc-ng/commit/4cddb251f13512756a642ba38d1e5298822fd824))

- **parse**: Use shared grammar CLI helpers
  ([`bc92046`](https://github.com/ourPLCC/plcc-ng/commit/bc92046a34ae5009d5850fe5c2782e3858e95b81))

- **rep**: Use shared grammar CLI helpers
  ([`f76d598`](https://github.com/ourPLCC/plcc-ng/commit/f76d598ce5e4d2030749dd550803470a28d4ae2c))

- **scan**: Use shared grammar CLI helpers
  ([`4d30896`](https://github.com/ourPLCC/plcc-ng/commit/4d3089606716b96780711379f1dbea7d1be96f62))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **089**: Update bats and pytest assertions for grammar-to-spec rename
  ([`b9823e2`](https://github.com/ourPLCC/plcc-ng/commit/b9823e2dd05f0dff58e52021f0d9cb3ee7e6e257))

Replace all --grammar/-g flags with --spec/-s, grammar.plcc with spec.plcc, and "grammar file not
  found" with "spec file not found" across all bats and pytest test files.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **089**: Update packaging smoke test to use spec.plcc
  ([`02d07bc`](https://github.com/ourPLCC/plcc-ng/commit/02d07bc6b658a1207f42c80df6b68faa8f03061c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.43.0 (2026-06-16)

### Bug Fixes

- **ci**: Trigger
  ([`2345b45`](https://github.com/ourPLCC/plcc-ng/commit/2345b452e083b97c900114a7f9d93d606ad52800))

- **lexical**: Reject keyword-prefix words like tokenize with KeywordExpected
  ([`927e8f5`](https://github.com/ourPLCC/plcc-ng/commit/927e8f5470bda5bcf79faefc2c6c41fd889972c7))

### Chores

- **bin**: Add close-worktree.bash utility script
  ([`eb05296`](https://github.com/ourPLCC/plcc-ng/commit/eb05296a54b01c5c6a1ecbdb8fde524f93a7d69b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **088**: Add design spec for required token/skip keyword [skip ci]
  ([`e85f3fa`](https://github.com/ourPLCC/plcc-ng/commit/e85f3fa0e305483de3619755d330ca16877ffc36))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **088**: Add implementation plan for required lexical keyword [skip ci]
  ([`eb41547`](https://github.com/ourPLCC/plcc-ng/commit/eb415472ee8e5ec017c465962e912051a6490f58))

### Features

- **lexical**: Add KeywordExpected error class [skip ci]
  ([`af6a03d`](https://github.com/ourPLCC/plcc-ng/commit/af6a03d4eb78f2adc7d713273e9350b9281e10d5))

- Create KeywordExpected class following the established pattern of other error classes
  (NameExpected, PatternExpected, etc.) - Export from __init__.py and Parser.py for use in parser
  and tests - Add test_keyword_is_required test (currently failing as parser enforcement is not yet
  implemented in Task 2)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **lexical**: Require token or skip keyword in lexical rules [skip ci]
  ([`69046aa`](https://github.com/ourPLCC/plcc-ng/commit/69046aacf661b80c3fa272782d1d525b76eabd56))

### Testing

- **lexical**: Fix pattern compile test and rename implicit token test [skip ci]
  ([`25938c0`](https://github.com/ourPLCC/plcc-ng/commit/25938c08e60dfcb7e6c4096cf6e7487af91004d6))

- Fix test_pattern_must_compile to test the actual PatternCompilationError instead of relying on the
  side effect of missing keyword - Rename test_implicit_token_rule to
  test_keyword_missing_produces_error to accurately reflect what the test validates - Add
  PatternCompilationError to imports

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **lexical**: Fix stale comment in cli test [skip ci]
  ([`e6ae3da`](https://github.com/ourPLCC/plcc-ng/commit/e6ae3da70ea0c75fa195e160e6dbd7749098f659))

- **lexical**: Update tests for required token/skip keyword
  ([`5431d92`](https://github.com/ourPLCC/plcc-ng/commit/5431d9252843e72d91134e53a75bfa7410ff20f0))

- Repurpose test_implicit_token_rule to verify bare syntax now produces KeywordExpected error -
  Remove test_implicit_token_produces_TokenRule (behavior no longer exists) - Add 'token' keyword to
  tests whose purpose was testing other behaviors (name validation, pattern errors, duplicates,
  etc.) - Updates cover all affected tests in parse_lexical_test.py and plcc_spec_cli_test.py

All 984 unit tests pass.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.42.0 (2026-06-15)

### Documentation

- **084**: Design spec for opt-in banner via --banner/-b [skip ci]
  ([`34be57d`](https://github.com/ourPLCC/plcc-ng/commit/34be57dbf08b33ff66e3705639388491fa33ed00))

- **084**: Implementation plan for --banner/-b opt-in [skip ci]
  ([`aa3d84f`](https://github.com/ourPLCC/plcc-ng/commit/aa3d84f7070ab58ea0c9135af2489359ce4f5bc8))

### Features

- **084**: Add print_banner() writing version+grammar to stderr
  ([`2a29435`](https://github.com/ourPLCC/plcc-ng/commit/2a294358f4c6ba2e9c33267d35cb2a10acc1d03f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **084**: Replace --no-banner with --banner/-b in plcc-diagram
  ([`97246e3`](https://github.com/ourPLCC/plcc-ng/commit/97246e324d8eb7c70351dc9f2ac88bc9fee216d6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **084**: Replace --no-banner with --banner/-b in plcc-make
  ([`64ce31a`](https://github.com/ourPLCC/plcc-ng/commit/64ce31aa4d49c3d2b7d497733fc93fc8ef1d92c2))

Banner is now opt-in via --banner/-b and prints to stderr instead of defaulting to stdout.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **084**: Replace --no-banner with --banner/-b in plcc-parse
  ([`ced110b`](https://github.com/ourPLCC/plcc-ng/commit/ced110b92049fc07edf488b8ae2b30f566b567f0))

- **084**: Replace --no-banner with --banner/-b in plcc-rep
  ([`2e696c1`](https://github.com/ourPLCC/plcc-ng/commit/2e696c10324d6cbb7c318f23ac3755a2580ce7ea))

Banner is now opt-in via -b/--banner (stderr), matching plcc-make/scan/parse.

- **084**: Replace --no-banner with --banner/-b in plcc-scan
  ([`3dd7e69`](https://github.com/ourPLCC/plcc-ng/commit/3dd7e694a5149635c0860a838d6b77d5570643d5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **084**: Consolidate print_banner import at top of output_test.py
  ([`027ea69`](https://github.com/ourPLCC/plcc-ng/commit/027ea69f8afb7a02baa04d5712705ce96fdf9c56))

- **084**: Remove dead print_version_line and print_grammar_line
  ([`a3f115f`](https://github.com/ourPLCC/plcc-ng/commit/a3f115f5f01850d115cdd9d687165ceb20864a85))


## v0.41.0 (2026-06-15)

### Documentation

- **086**: Design spec for Token __str__ and __repr__ [skip ci]
  ([`c53f671`](https://github.com/ourPLCC/plcc-ng/commit/c53f67197e5f01dabcb273b48ebaa33df6167e49))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **086**: Implementation plan for Token __str__ and __repr__ [skip ci]
  ([`964b8d1`](https://github.com/ourPLCC/plcc-ng/commit/964b8d15a26ad13e7489978d43b8dc43bd61d1e6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **086**: Token.__repr__ returns lexeme
  ([`2b4d2e8`](https://github.com/ourPLCC/plcc-ng/commit/2b4d2e8fcc4fccf7ff1292a7fe38123acfc20410))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **086**: Token.__str__ returns lexeme
  ([`885d8a7`](https://github.com/ourPLCC/plcc-ng/commit/885d8a7708d1fedc5e8985705346fbf087483a7a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.40.1 (2026-06-15)

### Bug Fixes

- **rep**: Flush message and harden SIGINT test
  ([`3a23635`](https://github.com/ourPLCC/plcc-ng/commit/3a236350115f0cda1118c1f6306f2ff154c69c90))

Add flush=True to the KeyboardInterrupt print to match all other protocol writes. Replace
  stderr==b'' assertion with 'Traceback' not in stderr and add TimeoutExpired cleanup to the SIGINT
  test.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **rep**: Suppress KeyboardInterrupt stack trace in generated main.py
  ([`18cd3b5`](https://github.com/ourPLCC/plcc-ng/commit/18cd3b5f97b745d0726284f08610f13ed3e6e1b7))

On ^C, generated Python interpreters now print 'User interrupted execution by ^C.' and exit 130
  instead of crashing with a traceback.

Strip COV_CORE_* env vars from the test subprocess so pytest-cov's .pth injection does not interfere
  with SIGINT exit-code assertions.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **rep**: Suppress KeyboardInterrupt stack trace in generated main.py
  ([`d7aecdd`](https://github.com/ourPLCC/plcc-ng/commit/d7aecdd1886fe1a6a42dd8517524fbc3595f5176))

On ^C, generated Python interpreters now print 'User interrupted execution by ^C.' and exit 130
  instead of crashing with a traceback.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Continuous Integration

- **docs**: Set mike default version so site root doesn't 404
  ([`49d80f2`](https://github.com/ourPLCC/plcc-ng/commit/49d80f28bc43913c57ad322b1b6e6c3ece5d7d9b))

Only set the default to dev if latest doesn't exist yet, so a release-promoted latest isn't
  overwritten on the next push to main.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Fix typos and remove resolved TODOs [skip ci]
  ([`4f1a111`](https://github.com/ourPLCC/plcc-ng/commit/4f1a111a711ef41de8b9b4b2c3b028c881a5cdc3))

- Update examples.md to new semantic section format [skip ci]
  ([`6cd2e59`](https://github.com/ourPLCC/plcc-ng/commit/6cd2e59828b32da6487ed971c3fcae6ab92771c2))

- **085**: Add design spec for KeyboardInterrupt fix in generated main.py [skip ci]
  ([`8eb3ab9`](https://github.com/ourPLCC/plcc-ng/commit/8eb3ab9a30457d8030018d3267361b058b78bef8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **085**: Add implementation plan for KeyboardInterrupt fix [skip ci]
  ([`e47ad19`](https://github.com/ourPLCC/plcc-ng/commit/e47ad19eb9aefa63fb600f7f5892d9551493f7b5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Consolidate semantic section issues 087/090/091/092 into 095 [skip ci]
  ([`0c24145`](https://github.com/ourPLCC/plcc-ng/commit/0c241459895e0c7c6447faa74a68675cab9433fd))

Issues 087, 090, 091, and 092 approached the semantic section redesign piecemeal and partially
  contradicted each other. Replace them with a single authoritative issue describing the final
  design: bare % divider, language declared as first non-blank line of the semantics body,
  case-sensitive, no tool naming.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.40.0 (2026-06-15)

### Bug Fixes

- **docs**: Set fence_prefix and tag_format on kroki plugin [skip ci]
  ([`6e60c26`](https://github.com/ourPLCC/plcc-ng/commit/6e60c266117e0a85d7db901c8172c18eac6ac1d2))

fence_prefix: '' — use plain ```plantuml blocks (default is kroki-plantuml)

tag_format: svg — embed SVG inline at build time, not img tags pointing to kroki.io

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Chores

- **docs**: Add bin/docs/serve.bash to start the MkDocs dev server [skip ci]
  ([`a6b497f`](https://github.com/ourPLCC/plcc-ng/commit/a6b497f2d1e1f84dd824f163e3a70740e83b7f62))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **docs**: Add project venv to PATH in serve.bash [skip ci]
  ([`6256eb3`](https://github.com/ourPLCC/plcc-ng/commit/6256eb3292985e75a153d68a2a4136ee458c2a1c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **docs**: Fix serve.bash to find .venv in main repo root [skip ci]
  ([`ffc17f3`](https://github.com/ourPLCC/plcc-ng/commit/ffc17f3fb6080d1d851c506f8284563618204ab8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 084 make no-banner the default [skip ci]
  ([`11e8bb3`](https://github.com/ourPLCC/plcc-ng/commit/11e8bb3f311774efcf1a86ac2d351c31694ebc4d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 085 plcc-rep KeyboardInterrupt on ^C [skip ci]
  ([`0814d3e`](https://github.com/ourPLCC/plcc-ng/commit/0814d3ea5573b9c3229b2efc9efc22b4de2fdee9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 086 Token string conversion method [skip ci]
  ([`ca19fe2`](https://github.com/ourPLCC/plcc-ng/commit/ca19fe204d222ba5699e3835cb8d894f1976aa2e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 075 and 082 to done [skip ci]
  ([`931e632`](https://github.com/ourPLCC/plcc-ng/commit/931e632378dfaa24a34eab5b6414d1a1dec3058d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add What's New section to home page [skip ci]
  ([`39ea3dd`](https://github.com/ourPLCC/plcc-ng/commit/39ea3dd24d3b919bd44ad95da828558a80250b27))

Closes #075

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Draft getting started page [skip ci]
  ([`cf8296e`](https://github.com/ourPLCC/plcc-ng/commit/cf8296e76fa97fff3593baff0cbcd0f14414b3a7))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Draft home page [skip ci]
  ([`c0471ed`](https://github.com/ourPLCC/plcc-ng/commit/c0471ed32ea6f003d7f34b1ec4494aa72e774795))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Expand test drive section and refine home page copy [skip ci]
  ([`9e84eab`](https://github.com/ourPLCC/plcc-ng/commit/9e84eab54553723650db87c17874a4f83dc6b8a3))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Fix quickstart output with real verified output [skip ci]
  ([`36cdaaa`](https://github.com/ourPLCC/plcc-ng/commit/36cdaaaca4992d77f5c41ada08351bc299f758eb))

Closes #074

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Fix typos and broken link on home page [skip ci]
  ([`fee522b`](https://github.com/ourPLCC/plcc-ng/commit/fee522b0fa7c1e8598a9444fd80027a34d043001))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Remove --no-banner from quickstart examples [skip ci]
  ([`9ba4666`](https://github.com/ourPLCC/plcc-ng/commit/9ba4666f518efc20d75b04c57ec3843ee63ecc02))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Revise getting started (rename section, update grammar, clean output) [skip ci]
  ([`c761cf1`](https://github.com/ourPLCC/plcc-ng/commit/c761cf1a066e2d5817027259d1c6f8596991d5f8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Revise home page description and simplify licenses section [skip ci]
  ([`963dd1f`](https://github.com/ourPLCC/plcc-ng/commit/963dd1f63b48e59ab38ddad9a7495f6c577c9e39))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Rewrite home page with project description and features [skip ci]
  ([`8b000df`](https://github.com/ourPLCC/plcc-ng/commit/8b000df5a56e1d7fa79b3f7703e3958606e02217))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update docs to reflect new spec file syntax and terminology [skip ci]
  ([`0aaae1c`](https://github.com/ourPLCC/plcc-ng/commit/0aaae1c489218afb13c0e0e60e514b077e603acc))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update home page navigation link descriptions [skip ci]
  ([`e0f9270`](https://github.com/ourPLCC/plcc-ng/commit/e0f9270d9f018f0adb6f21a3473019a7b26f33f3))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update quickstart to sum-integers example with semantics [skip ci]
  ([`ec7b1c3`](https://github.com/ourPLCC/plcc-ng/commit/ec7b1c3ac22ef888055fe6d3720fee0841f9df3d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update quickstart with verified command output [skip ci]
  ([`7854d76`](https://github.com/ourPLCC/plcc-ng/commit/7854d76b2fd623a2d9d34038bb467b8706c6002e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Draft CLI overview page [skip ci]
  ([`9f97321`](https://github.com/ourPLCC/plcc-ng/commit/9f9732163f93746415542b09a1a835c8551380f5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Draft orchestrators page [skip ci]
  ([`0353f93`](https://github.com/ourPLCC/plcc-ng/commit/0353f9341a3838e3beb1031806d39f4b78f8f7cf))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Draft primitives page [skip ci]
  ([`46e9422`](https://github.com/ourPLCC/plcc-ng/commit/46e942246f83f5b3be800c8d3975bd754766fad8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cli**: Show Level 2 orchestrators before Level 0 primitives [skip ci]
  ([`747b5c6`](https://github.com/ourPLCC/plcc-ng/commit/747b5c6fbcb04cea701b24bf10f35691aec76c58))

Closes #082

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 093 incremental parsing in plcc-rep interactive mode [skip ci]
  ([`feafd76`](https://github.com/ourPLCC/plcc-ng/commit/feafd76156f7acb331e78f9ce9c3974d6f55269f))

- **issues**: Add documentation issues 070-083 and move 065 to done [skip ci]
  ([`c743ac4`](https://github.com/ourPLCC/plcc-ng/commit/c743ac4f71c7dc50b2ffcc4e2de21ff45f56c3a2))

- **issues**: Add issue 087 — swap semantic divider to % Language tool [skip ci]
  ([`b2e62f4`](https://github.com/ourPLCC/plcc-ng/commit/b2e62f4294e18f4a0746479a4414b395bd549d87))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issue 088 — require token or skip keyword in lexical rules [skip ci]
  ([`a472902`](https://github.com/ourPLCC/plcc-ng/commit/a472902cdb571354c5f51284da0c27dab38ebae9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issue 089 — rename grammar file to specification file [skip ci]
  ([`b1255ab`](https://github.com/ourPLCC/plcc-ng/commit/b1255aba835305986dd5887e47bc1290b861ddfa))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issue 090 — case-sensitive language name in separator [skip ci]
  ([`63db460`](https://github.com/ourPLCC/plcc-ng/commit/63db4607512f675b4ce2c76b641b0cf433fb84c6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issue 091 — remove multiple semantic sections and tool name [skip ci]
  ([`6c66f3c`](https://github.com/ourPLCC/plcc-ng/commit/6c66f3c400d0d3298fbb32606e29f4ff84a1d847))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issue 092 — move language specifier to first line of semantics section [skip ci]
  ([`3f2be08`](https://github.com/ourPLCC/plcc-ng/commit/3f2be0892b73dbca1ece96d28280f8e0b405b4ff))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Add filename comment to overview example [skip ci]
  ([`a0ae70d`](https://github.com/ourPLCC/plcc-ng/commit/a0ae70da882ae5f37069fe73abdbce191554baad))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Add pipeline diagram to overview [skip ci]
  ([`b8d69fe`](https://github.com/ourPLCC/plcc-ng/commit/b8d69fee18b3401dec2c357195cf59add5be9234))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Draft code generation page [skip ci]
  ([`8d8c0a1`](https://github.com/ourPLCC/plcc-ng/commit/8d8c0a132d4a9468febda83895ec45f3c3104fb8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Draft examples page [skip ci]
  ([`6c3b7a8`](https://github.com/ourPLCC/plcc-ng/commit/6c3b7a80598a78a5e21934fbaa4547f870e5d2f5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Draft grammar rules page [skip ci]
  ([`f136d66`](https://github.com/ourPLCC/plcc-ng/commit/f136d66289ba44bc48990e3eca7e61bd7a1afd87))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Draft language guide overview [skip ci]
  ([`42e2c01`](https://github.com/ourPLCC/plcc-ng/commit/42e2c01b1d7ae1ff14f7c59028f8d6d088bb40b8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Draft token rules page [skip ci]
  ([`66d6b18`](https://github.com/ourPLCC/plcc-ng/commit/66d6b18e79b10c6d13a3814a555aca84d07c8b68))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Expand lexical rules and scanning algorithm [skip ci]
  ([`36ef2fc`](https://github.com/ourPLCC/plcc-ng/commit/36ef2fc978b9706a6708875e7cf3c838af860c16))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Expand semantic section with field access, entry point, and packaging [skip
  ci]
  ([`ae90d63`](https://github.com/ourPLCC/plcc-ng/commit/ae90d638311b6ab7b1e880b48cf28ae3e74a927e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Expand syntactic and semantic section docs [skip ci]
  ([`c0951c4`](https://github.com/ourPLCC/plcc-ng/commit/c0951c48edb4910e3d68ef5536eb5d9110193779))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Fix samples line numbers to match scanner output [skip ci]
  ([`140f295`](https://github.com/ourPLCC/plcc-ng/commit/140f295f28c242c6bb840bd8b7bf6538abceaacf))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Improve repetition rule example with xList/yList values [skip ci]
  ([`a95fe0f`](https://github.com/ourPLCC/plcc-ng/commit/a95fe0f60a0adf9b1ec8258f9c33b5fa7940acb2))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Minor wording fixes in syntactic section [skip ci]
  ([`6befdfd`](https://github.com/ourPLCC/plcc-ng/commit/6befdfdd9b123a802804c664373097e4749d40ce))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Refine lexical section content and examples [skip ci]
  ([`916f544`](https://github.com/ourPLCC/plcc-ng/commit/916f5448b69074b318471115bb4537072a41c6a5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Rename tokens.md to lexical.md [skip ci]
  ([`74a1d5d`](https://github.com/ourPLCC/plcc-ng/commit/74a1d5d1d64a3e48f607d287eea4b0312d2df2fd))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Restructure sections as lexical/syntactic/semantic [skip ci]
  ([`aafc966`](https://github.com/ourPLCC/plcc-ng/commit/aafc966a899c4fd6dc1aad19f6ce291a9c3df825))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Simplify hooks example [skip ci]
  ([`4de477c`](https://github.com/ourPLCC/plcc-ng/commit/4de477c8b949962e11a0dd4d524823359ee2c0f2))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **language-guide**: Simplify pipeline diagram, remove duplicate prose [skip ci]
  ([`46e5d91`](https://github.com/ourPLCC/plcc-ng/commit/46e5d91530e590e727d0d22d21036d980da8249f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Add initial user docs implementation plan [skip ci]
  ([`2a76d36`](https://github.com/ourPLCC/plcc-ng/commit/2a76d363dcd540727188f2012108feaf6b922933))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add initial user docs mapping plan [skip ci]
  ([`812e0db`](https://github.com/ourPLCC/plcc-ng/commit/812e0db62acc535c2cc71e683cd5cd77bcff66f5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add PlantUML docs diagrams design [skip ci]
  ([`0589a4d`](https://github.com/ourPLCC/plcc-ng/commit/0589a4d6538ed71f3fcf125106e5d614f5bc5120))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add PlantUML docs diagrams implementation plan [skip ci]
  ([`d7fda69`](https://github.com/ourPLCC/plcc-ng/commit/d7fda699d1cfa8e0845686ed685aa1f0d3772394))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **docs**: Add mkdocs-kroki-plugin for PlantUML diagram support [skip ci]
  ([`336fc97`](https://github.com/ourPLCC/plcc-ng/commit/336fc97fa6b2d0f03f1b299c914a2a614b1b7cf9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.39.2 (2026-06-07)

### Bug Fixes

- **docs**: Fix empty changelog page
  ([`8122c2e`](https://github.com/ourPLCC/plcc-ng/commit/8122c2eeac7432490a3d9de03854ab69166e7aec))

PSR replaced CHANGELOG.md entirely, removing the <!-- version list --> marker that docs/changelog.md
  used as a start anchor. Without the marker include-markdown included nothing. Remove the start
  filter to include the full file, and suppress MD041 since the linter cannot see past the include
  directive to the # CHANGELOG heading PSR generates.

### Build System

- **release**: Add [skip ci] to PSR release commit message
  ([`951fc04`](https://github.com/ourPLCC/plcc-ng/commit/951fc0456008350823e1fefe6971a18084d0b2c3))

PSR pushes a version bump commit to main using the GitHub App token, which triggers the release
  workflow again. Since the App token is not subject to GitHub's re-trigger suppression (unlike
  GITHUB_TOKEN), the second run would be a no-op but wastes CI minutes. Adding [skip ci] prevents
  the re-trigger. The docs site still updates via the release: published trigger that fires moments
  later.


## v0.39.1 (2026-06-07)

### Bug Fixes

- **ci**: Fix dev docs deployment to gh-pages subdirectory
  ([`502c367`](https://github.com/ourPLCC/plcc-ng/commit/502c36723f89756d019cccc89ac9a786d72e9182))

mkdocs gh-deploy has no --dest-dir option, and it replaces the entire gh-pages branch (wiping
  mike-managed user docs). Switch to building with mkdocs build then deploying with
  peaceiris/actions-gh-pages, which supports destination_dir and keep_files to update only dev-docs/
  without touching the rest of the branch.

- **docs**: Correct changelog insertion flag and add mike plugin [skip ci]
  ([`6d24523`](https://github.com/ourPLCC/plcc-ng/commit/6d245231446f75af89a2f3742dd8b257d5dfe57d))

- **docs**: Revert version_toml and serialize gh-pages deploys
  ([`f6a54a0`](https://github.com/ourPLCC/plcc-ng/commit/f6a54a07a70a78fb738ca3eaf514fa13ae13104f))

version_toml was incorrectly set to pyproject.toml:project.version — the version is SCM-derived (no
  project.version field exists). Reverted to [].

deploy-dev-docs now waits on deploy-user-docs so both jobs don't push to gh-pages concurrently,
  which could cause non-fast-forward push failures.

### Build System

- **docs**: Add mkdocs, material, mike, include-markdown-plugin [skip ci]
  ([`7e574fc`](https://github.com/ourPLCC/plcc-ng/commit/7e574fc576f9714adad53ac06746269e8cc67e94))

- **release**: Enable CHANGELOG.md auto-generation [skip ci]
  ([`644f681`](https://github.com/ourPLCC/plcc-ng/commit/644f68150ed89467555efbbc8555417a30b6a706))

### Continuous Integration

- **docs**: Add GitHub Actions workflow for user and developer docs [skip ci]
  ([`b35ab03`](https://github.com/ourPLCC/plcc-ng/commit/b35ab03f3f3612871f9f5adb95e7fd2e695e9f41))

- **docs**: Add token and concurrency group to docs workflow [skip ci]
  ([`48254b5`](https://github.com/ourPLCC/plcc-ng/commit/48254b5ce73bc9a5ad37bdb8deacd6580e026a7e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **release**: Use GitHub App token to bypass branch protection on push
  ([`6a55af3`](https://github.com/ourPLCC/plcc-ng/commit/6a55af35d0b1308650201eaaf7154d678663092d))

Replaces the RELEASE_TOKEN PAT with a short-lived installation token from the ourPLCC Release Bot
  GitHub App. The app is installed on plcc-ng with Contents read/write permission and listed as a
  bypass actor in the main branch ruleset. Tokens expire after 1 hour — nothing long-lived is stored
  beyond the app's private key.

- **release**: Use RELEASE_TOKEN to bypass branch protection on push
  ([`508e11a`](https://github.com/ourPLCC/plcc-ng/commit/508e11abb47e5c0c403d0415c5abbb5605dde1d6))

GITHUB_TOKEN cannot push to main when branch protection requires PRs. RELEASE_TOKEN is a
  fine-grained PAT scoped to this repo with contents read/write, owned by an org admin who has
  bypass rights.

### Documentation

- Add mkdocs config and user docs stub pages [skip ci]
  ([`617bf53`](https://github.com/ourPLCC/plcc-ng/commit/617bf53cf747b302964d4b4dacc26f036afa9732))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add mkdocs-dev config and developer docs stub pages [skip ci]
  ([`aefef67`](https://github.com/ourPLCC/plcc-ng/commit/aefef6766d4ebd6566dd71d1b9011320e90378cf))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **065**: Add documentation design spec [skip ci]
  ([`1f691fd`](https://github.com/ourPLCC/plcc-ng/commit/1f691fd753250debb887e721c00db2468d66044f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **065**: Add documentation implementation plan [skip ci]
  ([`bd89cfb`](https://github.com/ourPLCC/plcc-ng/commit/bd89cfba772e22a2d5fd17d04d6b4c44c193b3e6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **contributing**: Clarify when to use skip-ci tag
  ([`c3bf5ca`](https://github.com/ourPLCC/plcc-ng/commit/c3bf5cabd07b5a50fa48f8162c496338f2f583bf))

- **issues**: Move 010 to done — flakiness not observed in a long time [skip ci]
  ([`00cef9c`](https://github.com/ourPLCC/plcc-ng/commit/00cef9c15b29812e9e374c7488dd5ca88ad9ee26))

- **issues**: Move 053 to done — need stronger justification before pursuing [skip ci]
  ([`e2db8b6`](https://github.com/ourPLCC/plcc-ng/commit/e2db8b666cd8ae716b2817c7efee6ec3941f7b29))

- **issues**: Move completed issues 054 and 069 to done [skip ci]
  ([`d51b960`](https://github.com/ourPLCC/plcc-ng/commit/d51b960903eaf4840517151670290dd35145a14a))

Both were merged to main via PRs #186 and #187.

- **readme**: Slim README and add docs site link [skip ci]
  ([`4127ad2`](https://github.com/ourPLCC/plcc-ng/commit/4127ad21e21fe68eb30a700e9e6f41cb7167ed27))

### Refactoring

- **docs**: Move docs/superpowers/reviews to dev-docs/reviews [skip ci]
  ([`e42bd01`](https://github.com/ourPLCC/plcc-ng/commit/e42bd013f16173c6d7d9a05d22e1fe3a737b0427))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **docs**: Move internal docs to dev-docs/ [skip ci]
  ([`f92b054`](https://github.com/ourPLCC/plcc-ng/commit/f92b054e38c60c72c9322b108ea528418213a9dd))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.39.0 (2026-06-06)

### Bug Fixes

- **069**: Emit complete events for ARBNO iterations in tracer
  ([`d7d92f0`](https://github.com/ourPLCC/plcc-ng/commit/d7d92f068fd392f2385f5f313695099ce3f28c88))

_parse_arbno emitted predict but never complete, leaving dangling frames on _render_trace's stack
  that corrupted subsequent complete pops for enclosing rules.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **069**: Unconditional _render_trace import; add ARBNO render test
  ([`6f8e9c6`](https://github.com/ourPLCC/plcc-ng/commit/6f8e9c66cf011a40bf4a4768e27f991596094436))

Remove try/except ImportError guard — _render_trace is always present now. Drop skipif decorators
  that depended on it. Add test for balanced ARBNO events rendering correctly.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.38.0 (2026-06-06)

### Bug Fixes

- **syntax**: Address code review findings
  ([`f54259e`](https://github.com/ourPLCC/plcc-ng/commit/f54259e9e718068992d9f4476245a42322dcda57))

- _matchLeft raises MalformedBNFError on no-match instead of returning None - Fix stale line string
  in _TRIVIAL_SPEC to use <Program> - Correct _getNames return type to tuple[str, str | None]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **syntax**: Update MalformedBNFError examples for new BNF syntax
  ([`c1a571f`](https://github.com/ourPLCC/plcc-ng/commit/c1a571f3d13a82a74a6253c7b65fbae8284aa0fe))

- Update example strings to show annotations inside angle brackets: <NonTerminal:ClassName> - Adjust
  regex pattern in _compute_column() to match new syntax: <[^>]+> instead of <\S+>(?::\S+)? - All 11
  tests pass including test_str_includes_all_five_example_forms

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tests**: Update remaining integration bats and scan-verbosity fixture for PascalCase
  ([`76621d2`](https://github.com/ourPLCC/plcc-ng/commit/76621d2a297e8d41cfea7eabfaa43fe89830adaf))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **069**: Add parse trace design spec [skip ci]
  ([`a2dd1f8`](https://github.com/ourPLCC/plcc-ng/commit/a2dd1f868c6a400b0a5a34df552ddc675d0eb276))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **069**: Add parse trace implementation plan [skip ci]
  ([`ec2e63f`](https://github.com/ourPLCC/plcc-ng/commit/ec2e63f44d91ebe9645a480b682db43e164f965a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 042 and 057 to done [skip ci]
  ([`8c0b2fd`](https://github.com/ourPLCC/plcc-ng/commit/8c0b2fd46bc2816fde65c4540849d7ae4ddedc35))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 042 and 057 to done [skip ci]
  ([`d16d29c`](https://github.com/ourPLCC/plcc-ng/commit/d16d29cb8741936c686b2e3784f52412835cc452))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Add implementation plan for 054 reconsider BNF syntax [skip ci]
  ([`7bfc7a4`](https://github.com/ourPLCC/plcc-ng/commit/7bfc7a4dc53c33a24130883edfb024ad3af94d68))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add design for 054 reconsider BNF syntax [skip ci]
  ([`6e75c31`](https://github.com/ourPLCC/plcc-ng/commit/6e75c3139e4f12d8e080ef8d9e05709dadc7a630))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **069**: Add _render_trace for Style B parse trace output
  ([`a62f004`](https://github.com/ourPLCC/plcc-ng/commit/a62f004f271a958d2aa44d328abf55b3ec100d42))

- **069**: Buffer parse-step records and render trace before errors
  ([`da620e8`](https://github.com/ourPLCC/plcc-ng/commit/da620e8dd4ba74533ecb1f40d8bb159f12501b10))

- **069**: Remove --trace flag and dead trace code
  ([`fa4a270`](https://github.com/ourPLCC/plcc-ng/commit/fa4a2701668056a500b52020d697433741d17cdd))

Removes the --trace/-t flag from plcc-parse since parse-step records are now emitted unconditionally
  on ParseError. Cleans up the _print_parse_step function and trees_flags logic that are no longer
  needed.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **fixtures**: Update all .plcc fixtures to new BNF syntax
  ([`2cf32a7`](https://github.com/ourPLCC/plcc-ng/commit/2cf32a7766468d6e3e6d7e8d7e1f636559abfb4c))

Update fixture files and bats tests to use PascalCase nonterminal names and inside-bracket :name
  annotations (e.g. <NUM:num> instead of <NUM>:num).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **syntax**: Add shared is_valid_class_name utility
  ([`cf45768`](https://github.com/ourPLCC/plcc-ng/commit/cf45768063a9625c428f88e49e154b822d535636))

- **syntax**: Move :name annotation inside angle brackets
  ([`9f983b6`](https://github.com/ourPLCC/plcc-ng/commit/9f983b66dd81e9b1173ad355a1cd0e1aceefd81b))

- **syntax**: Require PascalCase for LHS nonterminal names and altNames
  ([`18bb31a`](https://github.com/ourPLCC/plcc-ng/commit/18bb31a7da24613df0f121842a884ce4506eadbf))

- **syntax**: Require PascalCase for RHS nonterminal names
  ([`86af11a`](https://github.com/ourPLCC/plcc-ng/commit/86af11a764750246f29588cc9e68553cc1f6369d))

Use is_valid_class_name to validate RHS nonterminals, and allow single-character altNames by
  relaxing the altName regex to [a-z][a-zA-Z0-9_]*. Update tests to use PascalCase nonterminals and
  inside-bracket syntax.

### Refactoring

- **model**: Drop redundant capitalize transforms now that names are PascalCase
  ([`5f6cadc`](https://github.com/ourPLCC/plcc-ng/commit/5f6cadca8e6a3a1db352359fd4f508f039c3df1e))

- **syntax**: Use #nil for synthetic altName and new line syntax in repeating rule expansion
  ([`e4f477d`](https://github.com/ourPLCC/plcc-ng/commit/e4f477d3e8ea323be3f3560893f9ff152291bb10))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **069**: Add failing feed() trace buffering tests [skip ci]
  ([`8e0e2a3`](https://github.com/ourPLCC/plcc-ng/commit/8e0e2a3274a682ae52e91b4a16a1b105792d6139))

- **069**: Add failing tests for _render_trace [skip ci]
  ([`fddf3e3`](https://github.com/ourPLCC/plcc-ng/commit/fddf3e395619036347bcccf5762a0a20fba6c301))

- **069**: Add shift and complete step record helpers
  ([`d1f3492`](https://github.com/ourPLCC/plcc-ng/commit/d1f34923e6f37523da4b8e123863a0a58d9e4a2c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **069**: Replace --trace bats tests with Style B trace tests
  ([`5424a1a`](https://github.com/ourPLCC/plcc-ng/commit/5424a1a9b4539bf94b0dfe7f3524fdb2251bd3cd))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **syntax**: Update validate_syntactic_spec test for PascalCase names
  ([`ab2113f`](https://github.com/ourPLCC/plcc-ng/commit/ab2113f447826c460507462ab685f8ecda6edc95))


## v0.37.1 (2026-06-06)

### Bug Fixes

- **ci**: Trigger
  ([`2263a00`](https://github.com/ourPLCC/plcc-ng/commit/2263a00b2aa3c64d27f16f92825a87fcb384f41f))

### Documentation

- **plans**: Add implementation plan for 042 diagram stderr forwarding [skip ci]
  ([`ec3ed66`](https://github.com/ourPLCC/plcc-ng/commit/ec3ed6642729621c4d7c8f10e948bcb08ff5f5e6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add design for 042 diagram stderr forwarding [skip ci]
  ([`ec7d322`](https://github.com/ourPLCC/plcc-ng/commit/ec7d3221344b2e810b5bc15a851f77da3fdc2899))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Fix design doc inaccuracies flagged in code review [skip ci]
  ([`5017c7d`](https://github.com/ourPLCC/plcc-ng/commit/5017c7d4174d208487826a83503a84d335e3af33))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **diagram**: Use VerboseContext parse/reformat for child stderr
  ([`71b5554`](https://github.com/ourPLCC/plcc-ng/commit/71b5554de35aadaceedce897b9acbb598a4a87ad))

### Testing

- **diagram**: Add failing test for plain-text stderr forwarding
  ([`b912776`](https://github.com/ourPLCC/plcc-ng/commit/b9127769ea227c58e472ac3da26aea398d72774f))

- **diagram**: Verify empty child stderr produces no output
  ([`5c2871d`](https://github.com/ourPLCC/plcc-ng/commit/5c2871d3952a78aaa11379bb0f8feef8b173548f))

Confirm that parse_child_events('') is a no-op and produces no output on stderr when a child process
  produces no output.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Verify JSONL child events are reformatted as text
  ([`d45c63e`](https://github.com/ourPLCC/plcc-ng/commit/d45c63e1ee946aca7268e9eb0525796feb525406))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.37.0 (2026-06-05)

### Documentation

- **issues**: Move 067 to done [skip ci]
  ([`08b69c4`](https://github.com/ourPLCC/plcc-ng/commit/08b69c4da040ca99385336361ff3c57182335b53))

- **issues**: Move 068 to done [skip ci]
  ([`ffa6a10`](https://github.com/ourPLCC/plcc-ng/commit/ffa6a102b0b70ad97b995132d9518321dff770bb))

- **plans**: Add implementation plan for issue 057 java emitter underscore prefix [skip ci]
  ([`18288cf`](https://github.com/ourPLCC/plcc-ng/commit/18288cf9db7a4fefb1b912c9b2ade3f075453326))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add design doc for issue 057 java emitter underscore prefix [skip ci]
  ([`1b41669`](https://github.com/ourPLCC/plcc-ng/commit/1b41669283abbc49e9016adce3f349717568421a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs,plans**: Fix inaccuracies flagged in code review [skip ci]
  ([`4582af4`](https://github.com/ourPLCC/plcc-ng/commit/4582af48098602e9fa4f6a1f816669bca97ebb7d))

- Clarify $run→_run is a breaking change for existing grammars - Narrow "done when" criterion to
  avoid false-positive on negative assertion - Fix grep command in plan to match entry-point
  patterns only

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **java-emitter**: Rename \$run to _run to match Python convention
  ([`c5c02dd`](https://github.com/ourPLCC/plcc-ng/commit/c5c02ddc6a436eeb74593076b1ef0bf900d01b94))

### Testing

- **java-emitter**: Update fixture and bats test name for _run rename
  ([`5017ac6`](https://github.com/ourPLCC/plcc-ng/commit/5017ac610b88f049de9914fe43505577239dabad))


## v0.36.0 (2026-06-05)

### Bug Fixes

- **lexical**: Remove dead PatternCompilationError import from parse_lexical_test
  ([`9bc3e27`](https://github.com/ourPLCC/plcc-ng/commit/9bc3e27b5223fcbdb4d6f044909aee74f275b1dc))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **plans**: Implementation plan for issue 068 — remove lexical second pattern [skip ci]
  ([`fd945c8`](https://github.com/ourPLCC/plcc-ng/commit/fd945c8364a024bc59292fd6f9dee9da2fb75ae2))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Design for issue 068 — remove lexical second pattern [skip ci]
  ([`17c0477`](https://github.com/ourPLCC/plcc-ng/commit/17c0477bd503fe560fc47cf56dd6584ea26c688e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **lexical**: Remove close_pattern and make_block_result from LexicalRule protocol
  ([`589e07b`](https://github.com/ourPLCC/plcc-ng/commit/589e07beaba49bc42070530955ddc6ab822525c6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **lexical**: Remove close_pattern from TokenRule and SkipRule
  ([`fbd51e4`](https://github.com/ourPLCC/plcc-ng/commit/fbd51e41dd2fa9ef43abefb794181b016ba8f099))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **lexical**: Remove optional second pattern from Parser
  ([`4f497b9`](https://github.com/ourPLCC/plcc-ng/commit/4f497b9edcf35c29104612cabf03e9e830308a26))

Removes the block-scanning feature by: - Deleting _parseOptionalPattern method - Updating
  _processLine to no longer pass close_pattern to rule constructors - Removing five block-related
  test functions - Updating test_junk_at_the_end_of_a_line to expect UnexpectedContent instead of
  PatternDelimiterExpected

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Remove block scanning; delete BlockOpened and UnclosedBlockError
  ([`b95b568`](https://github.com/ourPLCC/plcc-ng/commit/b95b5680257d53bfe127aa41d6886f68ed317962))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **schema**: Remove close_pattern; remove block bats test
  ([`1e3f733`](https://github.com/ourPLCC/plcc-ng/commit/1e3f7333f5ba254ad555d626731675c6f40e543b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tokens**: Remove UnclosedBlockError handling and close_pattern from spec_loader
  ([`702f263`](https://github.com/ourPLCC/plcc-ng/commit/702f263294dcc3cd269494c87bafa5164c93e41d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.35.0 (2026-06-05)

### Bug Fixes

- **banner**: Limit --no-banner pre-docopt check to option portion of argv
  ([`5c3be05`](https://github.com/ourPLCC/plcc-ng/commit/5c3be0542f978633d8cef3dada495a9aa896f50f))

Prevents a file literally named --no-banner passed as a positional SOURCE argument from incorrectly
  suppressing the version line.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **issues**: Add issue 065 design end user documentation [skip ci]
  ([`de52263`](https://github.com/ourPLCC/plcc-ng/commit/de52263b344241593fa7d809c02c222ff7f16b66))

- **issues**: Add issue 066 extend to another language [skip ci]
  ([`ae220d9`](https://github.com/ourPLCC/plcc-ng/commit/ae220d90f9b94d2d966851a176b61d60c05661c4))

- **issues**: Add issue 067 version header prints first [skip ci]
  ([`44e29c6`](https://github.com/ourPLCC/plcc-ng/commit/44e29c6c0473796d71c06aebb0d05523b3e530d6))

- **issues**: Add issue 068 remove lexical second pattern [skip ci]
  ([`5f8e123`](https://github.com/ourPLCC/plcc-ng/commit/5f8e12368ce35786805fc21f1e0da4aa354fd1f5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issue 069 improve plcc-parse --trace output [skip ci]
  ([`fa24534`](https://github.com/ourPLCC/plcc-ng/commit/fa24534a8392b73eeaca3906b50de1f65e8bc735))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 055 to done — keeping %%% as block delimiter [skip ci]
  ([`dcd329a`](https://github.com/ourPLCC/plcc-ng/commit/dcd329adad5eb959ce2b61f908ba929fdbefc374))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 056 to done [skip ci]
  ([`0f1f8ac`](https://github.com/ourPLCC/plcc-ng/commit/0f1f8ac54cb6fcc19ec4b2591044e37fc4ddbf20))

- **issues**: Move 063 to done [skip ci]
  ([`787007b`](https://github.com/ourPLCC/plcc-ng/commit/787007be03b730d39a89013224e5a365d5c78d9b))

- **issues**: Move 064 to done [skip ci]
  ([`07073e5`](https://github.com/ourPLCC/plcc-ng/commit/07073e53ca14e0450f802ee00af0767cfce2b2a1))

- **issues**: Update 054 BNF syntax to Type:name order [skip ci]
  ([`d3e2bcb`](https://github.com/ourPLCC/plcc-ng/commit/d3e2bcb708ba476fb593f94fac7b2d975ac2ebb5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Add implementation plan for issue 067 version header prints first [skip ci]
  ([`c791bf5`](https://github.com/ourPLCC/plcc-ng/commit/c791bf539286b55bbe7156510aca3f833ac837d1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add design for issue 067 version header prints first [skip ci]
  ([`2837325`](https://github.com/ourPLCC/plcc-ng/commit/28373258a33c9cd66a39d395bd6dc67e04499bb5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **diagram**: Add version banner and --no-banner flag
  ([`08903da`](https://github.com/ourPLCC/plcc-ng/commit/08903da92e609b5fbdb64d201a20e6cb50f13853))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **make**: Add version banner and --no-banner flag
  ([`59990c3`](https://github.com/ourPLCC/plcc-ng/commit/59990c31edf9db7cb2948ca97063a48ccfe577cc))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parse**: Print version first, add --no-banner, split banner output
  ([`45b056f`](https://github.com/ourPLCC/plcc-ng/commit/45b056f490f753f3669ccacb92626321d2c9c066))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **rep**: Print version first, add --no-banner, split banner output
  ([`20a2f64`](https://github.com/ourPLCC/plcc-ng/commit/20a2f64ae186ab6ea2324f8654863587d9fa4d06))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Print version first, add --no-banner, split banner output
  ([`af65289`](https://github.com/ourPLCC/plcc-ng/commit/af652890c060a8d5b7af1e10529003441de99ede))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.34.1 (2026-06-05)

### Bug Fixes

- **scan**: Block rules now include opening and closing delimiters in lexeme
  ([`1e3b378`](https://github.com/ourPLCC/plcc-ng/commit/1e3b378a42e1e3cc4a9172c21761fedb2e67f654))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **plans**: Implementation plan for issue 064 — block rules discard delimiters [skip ci]
  ([`9975673`](https://github.com/ourPLCC/plcc-ng/commit/9975673d63f53362de44f65903ab533776ee7566))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Design for issue 064 — block rules discard delimiters [skip ci]
  ([`ab7dc00`](https://github.com/ourPLCC/plcc-ng/commit/ab7dc00cd7e869d4736219f21a9c4b700428574b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.34.0 (2026-06-05)

### Bug Fixes

- **scan**: Remove stale plcc-parse annotation from SubmitOn.EOF comment [skip ci]
  ([`b75383d`](https://github.com/ourPLCC/plcc-ng/commit/b75383deb7d6d44acb284e3b033ef448e4340a6a))

EOF mode is now used by plcc-scan, plcc-parse, and plcc-rep.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **issues**: Add 063 — plcc-scan must run in multi-line mode for block tokens/skips [skip ci]
  ([`15fc1e6`](https://github.com/ourPLCC/plcc-ng/commit/15fc1e63a984707427b675832f09df8f07132b1e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 064 — block rules discard opening/closing delimiters [skip ci]
  ([`a7c18d4`](https://github.com/ourPLCC/plcc-ng/commit/a7c18d49c4e15c8736ba81892f58b0c3427dd8fa))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Add implementation plan for issue 063 — plcc-scan multi-line mode [skip ci]
  ([`aa76f79`](https://github.com/ourPLCC/plcc-ng/commit/aa76f7902e760e611f4565fa620b23887c6571a4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Rescue orphaned 062 plan from issue-059-060-design worktree [skip ci]
  ([`65032de`](https://github.com/ourPLCC/plcc-ng/commit/65032ded8e36f9db6cccd8f6791184521601c97b))

The plan was never committed before the branch was merged via PR #174. The implementation it
  describes (fix 062) is already in main.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add design for issue 063 — plcc-scan multi-line mode [skip ci]
  ([`a9215aa`](https://github.com/ourPLCC/plcc-ng/commit/a9215aa27ce5c538a7ced5e81c2b98f09a17cdb6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **scan**: Switch to EOF submit mode for multi-line block token support
  ([`ef945c2`](https://github.com/ourPLCC/plcc-ng/commit/ef945c2322063cf7f81936fd683d050e52816475))

Fixes issue 063. plcc-scan now accumulates interactive input until ^D before submitting to
  plcc-tokens, matching plcc-parse and plcc-rep. Block tokens/skips that span multiple lines now
  work end-to-end.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.33.0 (2026-06-05)

### Bug Fixes

- **062**: Handle UnclosedBlockError in tokens_cli — emit error record
  ([`b99d7c1`](https://github.com/ourPLCC/plcc-ng/commit/b99d7c1750eb46c0e34f5982bac35b8961598cb4))

Wires UnclosedBlockError dispatch into the CLI's scanner output loop, emitting properly formatted
  error records when EOF is reached inside a block token (closing pattern not found).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **lexical**: Annotate line as Line | None; move block imports to top of scanner_test
  ([`2fb1aa6`](https://github.com/ourPLCC/plcc-ng/commit/2fb1aa6946d35e858fb0f19bf50b6d89a25733aa))

- **lines**: Normalize CRLF and bare CR line endings to LF in parse_from_strings
  ([`64a69f3`](https://github.com/ourPLCC/plcc-ng/commit/64a69f350c0f6b351506b78609e71fcd1dff1462))

- **lines**: Preserve trailing newline in parse_from_string via splitlines(keepends=True)
  ([`1d1c82c`](https://github.com/ourPLCC/plcc-ng/commit/1d1c82c0b4f36f512a481d5cf55d755075975d04))

- **scan**: Remove manual newline injection from _scanBlock; newlines come from Line.string
  ([`65a9128`](https://github.com/ourPLCC/plcc-ng/commit/65a9128918c20571a7c8283880d17caf61a72ef5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Update downstream code for Line.string keepends invariant
  ([`dca0ec7`](https://github.com/ourPLCC/plcc-ng/commit/dca0ec70018f133f151838d3fa4565d4e7ba4f03))

Fixes FileNotFoundError in parse_includes (newline captured in path), double-newline output in
  SpecError.__str__, and stale Line literals in parseRough_test and parse_includes_test that didn't
  include trailing \n.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **062**: Add design spec for UnclosedBlockError handling in tokens_cli
  ([`d893a81`](https://github.com/ourPLCC/plcc-ng/commit/d893a812d0b83f9f52dd67812f325ff99362ac40))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Spec for issue-061 Line.string newline normalization
  ([`1bdbcd8`](https://github.com/ourPLCC/plcc-ng/commit/1bdbcd8d824dcb288e5ccd9cb6c2c29629bbb180))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 061 double-newline in block scanner, 062 UnclosedBlockError crash in tokens-cli
  ([`025cb4d`](https://github.com/ourPLCC/plcc-ng/commit/025cb4d0c669227e2aabde31d933001323d75461))

- **issues**: Move 059, 060, 061, 062 to done
  ([`99ef19d`](https://github.com/ourPLCC/plcc-ng/commit/99ef19dad4928239cf0f5339da4aafe4cb03560c))

- **plan**: Implementation plan for block lexical rule (issue 060)
  ([`21b7728`](https://github.com/ourPLCC/plcc-ng/commit/21b7728bd905b69a9da2bbad79bcb7b30f8ad22b))

- **plan**: Implementation plan for issue-061 Line.string newline normalization [skip ci]
  ([`b825e19`](https://github.com/ourPLCC/plcc-ng/commit/b825e1961fb94585840ebd452bd9f6886e1261a4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Design for block lexical rule (issue 060)
  ([`195ff75`](https://github.com/ourPLCC/plcc-ng/commit/195ff7595b80c112e310729003a139070c6441d7))

- **spec**: Fix circular import note and index arithmetic in block rule design [skip ci]
  ([`61a04c9`](https://github.com/ourPLCC/plcc-ng/commit/61a04c96cb4887e2a12e7f3324f4bed438109329))

### Features

- **062**: Add format_unclosed_block_error_record to jsonl_formatter
  ([`573ffe3`](https://github.com/ourPLCC/plcc-ng/commit/573ffe3a1ddebc52785ff627a684110279b2c582))

Implement formatter function to handle UnclosedBlockError records, which occur when EOF is reached
  inside a block token with no closing delimiter. This allows the plcc-tokens CLI to properly emit
  error records instead of crashing.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **lexical**: Parse optional second pattern for block token/skip rules
  ([`737a615`](https://github.com/ourPLCC/plcc-ng/commit/737a615de1fd532f97ea1db2cb49e5076f4b29c8))

Extend Parser._processLine to extract _parsePattern and add _parseOptionalPattern, enabling block
  rules like `token BODY '<<<' '>>>'`. Update test for junk-after-pattern to reflect new
  PatternDelimiterExpected behavior (junk is now treated as a malformed second pattern).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Add BlockOpened sentinel and UnclosedBlockError
  ([`35dff98`](https://github.com/ourPLCC/plcc-ng/commit/35dff98681f2edfb6b4858f349100584f2679ee2))

Adds BlockOpened (returned by Matcher when a rule's close_pattern is set and the opening pattern
  matches) and UnclosedBlockError (yielded by Scanner at EOF while in block mode) as pure
  data-carrier dataclasses, with instantiation tests and exports from scan/__init__.py.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Scanner block mode for token/skip rules with close_pattern
  ([`9c9bd8a`](https://github.com/ourPLCC/plcc-ng/commit/9c9bd8a9d1781d9f5154873419273035f45e84fb))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Export TokenRule and SkipRule from spec package
  ([`b896901`](https://github.com/ourPLCC/plcc-ng/commit/b89690196d38e191787ff7f23a3b1dcd6d85b220))

- **tokens**: Spec_loader emits TokenRule/SkipRule; schema adds close_pattern
  ([`394926a`](https://github.com/ourPLCC/plcc-ng/commit/394926aaa2bd8f738fd5bbd17d08db1c17c4aea8))

Update spec_loader to directly import TokenRule and SkipRule, and pass the optional close_pattern
  parameter when instantiating rules from spec JSON. Add close_pattern as an optional property in
  the spec schema.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **lexical**: Replace LexicalRule dataclass with TokenRule/SkipRule + Protocol
  ([`c8659a0`](https://github.com/ourPLCC/plcc-ng/commit/c8659a0ca002524a1cd963172ce0a3c81f430512))

Splits the single LexicalRule dataclass into concrete TokenRule and SkipRule types, introducing a
  LexicalRule Protocol for type annotations. Updates all callsites (Parser, spec_loader, test
  helpers) to use the concrete types.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Inline rule.make_match; remove _makeSkipOrToken wrapper
  ([`c479010`](https://github.com/ourPLCC/plcc-ng/commit/c479010d63242cecbdfe6562ca9001112e705521))

The _makeSkipOrToken method was a one-line wrapper that added no value. Inlined the call to
  rule.make_match() at the call site and deleted the method.

Also strengthened the skip block test to assert result.rule and result.column, matching the
  assertions in the token block test for consistency.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Matcher delegates result construction to rule.make_match
  ([`6657459`](https://github.com/ourPLCC/plcc-ng/commit/6657459332446fd0d974c65e8caf19ef03b4f63b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **lexical**: Add unit tests for TokenRule/SkipRule; type match param
  ([`3eb2648`](https://github.com/ourPLCC/plcc-ng/commit/3eb26489cde6d0d0b21e26ead436b8a3482cc7c5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Update scanner tests for Line.string keepends invariant
  ([`c004a12`](https://github.com/ourPLCC/plcc-ng/commit/c004a128c584c4fc27a6c49bf6aaa666cd719e6b))

Now that Line.string includes the trailing \n, adjust slice indices (0:11, 11:), token counts (8,
  7), expected block-content lexeme, and filter-vs-count assertions to match the new per-line string
  shape.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Verify token NEWLINE rule matches line endings via Line.string invariant
  ([`d34dd46`](https://github.com/ourPLCC/plcc-ng/commit/d34dd464fdeb2dc15f8d7718d660fcc6076569c9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.32.0 (2026-06-04)

### Bug Fixes

- **ci**: Trigger
  ([`5990109`](https://github.com/ourPLCC/plcc-ng/commit/59901096f09eff953e2a2a0ff0ea6aef5e68991b))

### Documentation

- **issues**: Add 060 block lexical rule type [skip ci]
  ([`6883e88`](https://github.com/ourPLCC/plcc-ng/commit/6883e880277077f5fa9770709691a001850e67f1))

- **issues**: Close 058, add 059 plcc-generated-spec-parser [skip ci]
  ([`2273089`](https://github.com/ourPLCC/plcc-ng/commit/22730890236589c967e8087d4be97c5dc494ac7e))

Issue 058 (collocate lexical patterns) is superseded by the larger architectural goal of parsing
  PLCC grammar files with a PLCC-generated parser. Issue 059 captures that goal with its
  prerequisites and decomposition.

- **issues**: Move issue 049 to done [skip ci]
  ([`7b7a97f`](https://github.com/ourPLCC/plcc-ng/commit/7b7a97fc1ff9b94fe21fcf3f6548c5427471f39e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Clarify max() tiebreaking; mark grammar audit done [skip ci]
  ([`bc019e6`](https://github.com/ourPLCC/plcc-ng/commit/bc019e67f6c3d2a85f57efa5c128b99fe41f3d69))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Correct fixture audit claim to include \s* skip [skip ci]
  ([`6d55fdb`](https://github.com/ourPLCC/plcc-ng/commit/6d55fdb247d757097547fd04f6224ab89b886aab))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Design spec for first-longest-match scanner algorithm [skip ci]
  ([`e7823ca`](https://github.com/ourPLCC/plcc-ng/commit/e7823cacc3659447d73558d5b408a411e903f915))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Implementation plan for first-longest-match scanner [skip ci]
  ([`458d3ee`](https://github.com/ourPLCC/plcc-ng/commit/458d3ee7c1990645948b1d5b62099c8f2683858d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **scan**: Replace skip-priority algorithm with first-longest-match
  ([`a4d85b3`](https://github.com/ourPLCC/plcc-ng/commit/a4d85b313af2370e4469bac3ea343cb744320668))

The previous algorithm gave skips categorical priority: if any skip matched, the first-declared skip
  won immediately. This new algorithm treats all rules equally, with the longest match winning and
  declaration order breaking ties.

Changes: - Remove skip-priority short-circuit from match() - Delete _removeSkips() helper (no longer
  needed) - Pass all matches to _getLongestMatch() instead of filtering skips

This allows skips and tokens to compete fairly, enabling longer tokens to win even when skips are
  declared first. Tests updated in Task 1 now pass.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.31.0 (2026-06-02)

### Bug Fixes

- **cmd**: Guard against None from read_grammar in banner calls
  ([`1a1d6d9`](https://github.com/ourPLCC/plcc-ng/commit/1a1d6d909f542bcf4899be8acfa1e7dc67b35b19))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **design**: Add spec for issue 049 level-2 startup info
  ([`cfe563d`](https://github.com/ourPLCC/plcc-ng/commit/cfe563db468ba41f9617ba4254754ee93cd0be52))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add alternatives to issue 055 block delimiters [skip ci]
  ([`aea92fb`](https://github.com/ourPLCC/plcc-ng/commit/aea92fb80065ed221813c2d6af4e6df7809f2787))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add analysis and decision to issue 054 bnf syntax [skip ci]
  ([`c75f754`](https://github.com/ourPLCC/plcc-ng/commit/c75f754c782169e1972c6f8fb20d3d5165990405))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add analysis and flex/lex observation to issue 056 scanner algorithm [skip ci]
  ([`4c16ae2`](https://github.com/ourPLCC/plcc-ng/commit/4c16ae2edf284d1c0e6a5f92a620667efbd4225b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add before/after example to issue 054 [skip ci]
  ([`321a933`](https://github.com/ourPLCC/plcc-ng/commit/321a933a8258beb4aa447fdff85e24a75fa8d83d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issue 053 render ll1.json in human-readable format [skip ci]
  ([`d4bbbf7`](https://github.com/ourPLCC/plcc-ng/commit/d4bbbf774da92232c76134a9bd31be8775964fcd))

- **issues**: Add issue 054 reconsider BNF section syntax [skip ci]
  ([`74511ec`](https://github.com/ourPLCC/plcc-ng/commit/74511ec1de81e2996465362459946006796b9ca8))

- **issues**: Add issue 055 consider alternative block delimiters [skip ci]
  ([`c32e950`](https://github.com/ourPLCC/plcc-ng/commit/c32e950c8af04b198950133e6e08b07183bf4c33))

- **issues**: Add issue 056 reconsider scanner algorithm [skip ci]
  ([`ee6c201`](https://github.com/ourPLCC/plcc-ng/commit/ee6c20172bd7eda2e0ef49e9d8ce1d0478bf0596))

- **issues**: Add issue 057 java emitter underscore prefix [skip ci]
  ([`40e37c6`](https://github.com/ourPLCC/plcc-ng/commit/40e37c6beefbb188d6ffec5baf0b1e958f5700bb))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issue 058 collocate lexical patterns [skip ci]
  ([`1e947d6`](https://github.com/ourPLCC/plcc-ng/commit/1e947d6f91c7f1ebac3a331cc85c7938f9defa69))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Fix before example to use lowercase non-terminals in 054 [skip ci]
  ([`13baf0f`](https://github.com/ourPLCC/plcc-ng/commit/13baf0fd6627ee3826e631b75be69d43d2c602a6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move issue 031 to done [skip ci]
  ([`2a4a97a`](https://github.com/ourPLCC/plcc-ng/commit/2a4a97a232e3d9c7e8554e89fa91266940b32276))

- **issues**: Update issue 053 to consider diagrams via PlantUML [skip ci]
  ([`4353ed8`](https://github.com/ourPLCC/plcc-ng/commit/4353ed8a2c6f3044132989cb4982d2648a667db7))

- **plan**: Add implementation plan for issue 049 level-2 startup info [skip ci]
  ([`02df955`](https://github.com/ourPLCC/plcc-ng/commit/02df9559d9a9a187470ce122d48abea2e831eeee))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **cmd**: Add print_startup_banner to output.py
  ([`92c0c0f`](https://github.com/ourPLCC/plcc-ng/commit/92c0c0f25a1a6b696564e53cfce9d33c35c4bda7))

- **parse**: Print startup banner after make
  ([`450232f`](https://github.com/ourPLCC/plcc-ng/commit/450232f3e6741d74a275381419abd69ea8c87088))

- **rep**: Print startup banner after make
  ([`b25c56d`](https://github.com/ourPLCC/plcc-ng/commit/b25c56d0d75f653f580a6aeb57dcbcf07340a94d))

- **scan**: Print startup banner after make
  ([`265fa87`](https://github.com/ourPLCC/plcc-ng/commit/265fa878d170260b29a08e0059b74db0194f14e7))

### Refactoring

- **cmd**: Remove or '' fallback from read_grammar calls
  ([`85e3f19`](https://github.com/ourPLCC/plcc-ng/commit/85e3f19669cea6678a9e76019a1b3f3d61b7f8e0))

plcc-make always writes build/.grammar before returning 0, so the fallback is never reached in
  practice. Keeping it would silently produce os.path.abspath('') == <cwd> as the grammar path,
  which is more misleading than the TypeError that surfaces the invariant violation.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **bats**: Update output checks to account for startup banner
  ([`87b8ac5`](https://github.com/ourPLCC/plcc-ng/commit/87b8ac51d9da649df4343ed031da943b4d703b0e))

Commands now print a startup banner to stdout before results. Tests that matched the full output
  string exactly now check the last output line instead.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **e2e**: Update plcc-rep output checks for startup banner
  ([`25481dd`](https://github.com/ourPLCC/plcc-ng/commit/25481dd17442e0e9faadccd902a1060099965a49))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.30.0 (2026-06-01)

### Bug Fixes

- **fixtures**: Remove entry_point token from arith.plcc
  ([`6a4acf1`](https://github.com/ourPLCC/plcc-ng/commit/6a4acf18b5a87ffc792bad74ae8451d9a0893510))

- **fixtures**: Remove entry_point token from trivial-python and trivial-arbno
  ([`938d999`](https://github.com/ourPLCC/plcc-ng/commit/938d999e95f9ddbefb0391575aee87a9b13a1312))

- **rough**: Use regex match span for extra-token column in error
  ([`3736ef9`](https://github.com/ourPLCC/plcc-ng/commit/3736ef919aaa504f70b004ff673c58ac45132b04))

- **schemas**: Remove entry_point from spec and model JSON schemas
  ([`35260f8`](https://github.com/ourPLCC/plcc-ng/commit/35260f845a69c9935fd4ce019f87cb8bff377990))

### Documentation

- **issues**: Move 052 to done after merge [skip ci]
  ([`95dc157`](https://github.com/ourPLCC/plcc-ng/commit/95dc157cf9ba8832990eac6e7c8e32fe9ac7764f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plan**: Implementation plan for removing entry_point from grammar syntax [skip ci]
  ([`26a8b09`](https://github.com/ourPLCC/plcc-ng/commit/26a8b09d3730e36eb921713a468ef85e21edde4d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Design doc for removing entry_point from grammar syntax (issue 031) [skip ci]
  ([`f17d8af`](https://github.com/ourPLCC/plcc-ng/commit/f17d8af2f5474fa2c0399a1bdf154cddaa2c28aa))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **rough**: Raise error for extra token on divider line; remove entry_point parsing
  ([`3282b8e`](https://github.com/ourPLCC/plcc-ng/commit/3282b8ef44e12c14ab26216101acb8138ef4f8dc))

### Refactoring

- **java-emit**: Use _DEFAULT_ENTRY_POINT directly; remove entry_point tests
  ([`5c75824`](https://github.com/ourPLCC/plcc-ng/commit/5c75824c27ecaed260f87177851048023f432cfe))

- **model**: Remove entry_point from semantic section model dict
  ([`185bcbd`](https://github.com/ourPLCC/plcc-ng/commit/185bcbd91965c1b2314883ae227f6ad65181382a))

- **python-emit**: Use _DEFAULT_ENTRY_POINT directly; remove entry_point tests
  ([`c90cc51`](https://github.com/ourPLCC/plcc-ng/commit/c90cc518040df5289b6d86a1060f279c721165d8))

- **spec**: Remove entry_point from Divider and SemanticSpec
  ([`f40c2d9`](https://github.com/ourPLCC/plcc-ng/commit/f40c2d9a7ababd3bd29f40bf8d26efce89fad789))

### Testing

- **integration**: Remove obsolete null entry_point bats test
  ([`2250d75`](https://github.com/ourPLCC/plcc-ng/commit/2250d750ae7cd206e3288e21fac479947b053579))


## v0.29.4 (2026-06-01)

### Bug Fixes

- **fixtures**: Update test grammars to use colon RHS alt name syntax
  ([`5f010f3`](https://github.com/ourPLCC/plcc-ng/commit/5f010f3abf5bbe74feb7b0d329e810122574edc0))

Fixes command test failures introduced when issue 052 made the no-colon form a syntax error. All
  four fixtures used <word>name; updated to <word>:name.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **issues**: Move completed issue 050 to done [skip ci]
  ([`a848966`](https://github.com/ourPLCC/plcc-ng/commit/a8489664703ab08dcfbd37fe87898864dcc97761))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move completed issue 051 to done [skip ci]
  ([`4925551`](https://github.com/ourPLCC/plcc-ng/commit/4925551d9c4aff344afd12657816cd1aa0c0fb03))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plan**: Add implementation plan for issue 051 remove %%{ / %%} syntax [skip ci]
  ([`8f80449`](https://github.com/ourPLCC/plcc-ng/commit/8f804497fe2da86089abdccfcdb1101ec421e164))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plan**: Fix inaccurate expected failure for test_pprc_is_a_plain_line [skip ci]
  ([`bd3a2b3`](https://github.com/ourPLCC/plcc-ng/commit/bd3a2b3f4979d50b2b2ee562db185ef0b96a5577))

%%} alone is not a block opener so test_pprc_is_a_plain_line already passes before the
  implementation change. Clarify that only test_pplc_is_a_plain_line is the red step.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Add design doc for issue 051 remove %%{ / %%} syntax [skip ci]
  ([`5259ec8`](https://github.com/ourPLCC/plcc-ng/commit/5259ec8e6a6cbbbf0ae0545813f803c033826b2c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Add design doc for issue 052 colon-required RHS alt name
  ([`e58b157`](https://github.com/ourPLCC/plcc-ng/commit/e58b157f842858b465c4c68237a70c0dd3a16fb3))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **rough**: Remove %%{ / %%} block delimiter syntax (issue 051)
  ([`75a2ba8`](https://github.com/ourPLCC/plcc-ng/commit/75a2ba871b36f13c0f8526b83d6631b5db99bea8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **syntax**: Require colon in RHS <...>:name syntax (issue 052)
  ([`901f619`](https://github.com/ourPLCC/plcc-ng/commit/901f619ff9b462bdbaacee22c39d4671003df74e))

<word>hello now raises MalformedBNFError; only <word>:hello is accepted, consistent with the LHS
  parser. Removes the silent strip(":") workaround.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **052**: Convert no-colon RHS named terminal test to error case
  ([`e6234b0`](https://github.com/ourPLCC/plcc-ng/commit/e6234b092a336f27feef4e3e1d7a65da336f5ee5))

Replace test_named_rhs_non_terminal with test_named_rhs_non_terminal_without_colon_is_an_error to
  assert that <word>hello (without colon) is invalid BNF syntax.

The test currently fails because the implementation incorrectly accepts this syntax. Fix for this
  error case will come in the next task.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.29.3 (2026-05-31)

### Bug Fixes

- Update release workflow smoke test to use --grammar (issue 050)
  ([`22203a7`](https://github.com/ourPLCC/plcc-ng/commit/22203a76511dd4c95cb61074ae6e600d084ab840))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for issue 050 rename --grammar-file to --grammar
  ([`7dbaa8d`](https://github.com/ourPLCC/plcc-ng/commit/7dbaa8da0621635555bbaf3d06341076774864a5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issue 050 [skip ci]
  ([`c8333f8`](https://github.com/ourPLCC/plcc-ng/commit/c8333f8bd21002ed63ee9dfd929400b5d8c94762))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move completed issues to done [skip ci]
  ([`331df48`](https://github.com/ourPLCC/plcc-ng/commit/331df48b81e827720f092aa04cfd9847999b41cd))

Move 047 and 048 to done/ — both merged to main.

### Refactoring

- Fix stale test name and add -g short-form smoke test
  ([`9f2fab3`](https://github.com/ourPLCC/plcc-ng/commit/9f2fab3229e0dfed60bb8ba291be03400384947c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Rename --grammar-file to --grammar / -g in all commands (issue 050)
  ([`67802fb`](https://github.com/ourPLCC/plcc-ng/commit/67802fb26e0760cae07fd7dbb18c49d447cceea4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.29.2 (2026-05-30)

### Bug Fixes

- **ll1**: Add count to LL1Error and pass it from check_parsing_table_for_ll1
  ([`e64ba3d`](https://github.com/ourPLCC/plcc-ng/commit/e64ba3da0b38762a724edf9e62b64a1903feca2e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **ll1**: Use list in parsing table and _predictSet to detect identical predict set conflicts
  ([`d172ef0`](https://github.com/ourPLCC/plcc-ng/commit/d172ef069fe2d47fc59e0c74677f458459f9b6cd))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for issue 048 - LL(1) identical predict set conflict detection
  ([`315d690`](https://github.com/ourPLCC/plcc-ng/commit/315d690df1eaca6dba331bcc947ae7cbff0b2564))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issue 048 [skip ci]
  ([`434a3cf`](https://github.com/ourPLCC/plcc-ng/commit/434a3cf1189734aa04d4ecf43725fcecde76c76a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Revise 048 design to fix FIRST/FOLLOW overlap and epsilon leaking via _predictSet
  ([`3f86df0`](https://github.com/ourPLCC/plcc-ng/commit/3f86df09c9ee85c5bb754efda8067d4cab32e3aa))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Revise 048 design to use list instead of parallel count dict
  ([`79ce129`](https://github.com/ourPLCC/plcc-ng/commit/79ce1294d746bb178e8882e26c2e219a4ba97a9e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **ll1**: Align check_parsing_table_for_ll1_test to list semantics and add count assertions
  ([`59cb297`](https://github.com/ourPLCC/plcc-ng/commit/59cb297839d7617898df1b82d9a9adb225c33346))


## v0.29.1 (2026-05-30)

### Bug Fixes

- **make**: Write build/.grammar before build stages so sticky grammar survives syntax errors
  ([`82318b5`](https://github.com/ourPLCC/plcc-ng/commit/82318b5bd72d4d338e0a05a49435e9c63a585778))

### Chores

- Add bin/issues/new.bash and .next-id.txt to prevent duplicate issue numbers
  ([`ef60483`](https://github.com/ourPLCC/plcc-ng/commit/ef60483474e0618430fccb8852c43e2e0351f88c))

Completed issues move to done/, so scanning the directory for the next number risks collisions.
  Store the next ID in .next-id.txt and always allocate through bin/issues/new.bash.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **design**: Spec for fix-047 sticky grammar on syntax error
  ([`bec70c4`](https://github.com/ourPLCC/plcc-ng/commit/bec70c45d814bfa13e41193b28e12339976b3b68))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 047 - sticky grammar not persisted on syntax error [skip ci]
  ([`153b6ee`](https://github.com/ourPLCC/plcc-ng/commit/153b6ee8ceae0c14684ade7f42491d19ed9f7eb0))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 048 - LL(1) conflict detection misses identical predict sets [skip ci]
  ([`fc6f8d5`](https://github.com/ourPLCC/plcc-ng/commit/fc6f8d588327fdbb80d5df48d075ae71fc361dd8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 049 - level-2 commands should print startup info [skip ci]
  ([`ed3ebba`](https://github.com/ourPLCC/plcc-ng/commit/ed3ebba7639ad09f9a286734065016dda1315717))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 050 - rename --grammar-file to --grammar [skip ci]
  ([`2342a6a`](https://github.com/ourPLCC/plcc-ng/commit/2342a6adbd1378936b1e6db151e07d1826531e12))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 051 - remove %%{ / %%} semantic block bracket syntax [skip ci]
  ([`6a583d9`](https://github.com/ourPLCC/plcc-ng/commit/6a583d99e5af4556c9c2dce05440fab140ad9a10))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 052 - require colon in <...>:name syntax; reject <...>name [skip ci]
  ([`1410e50`](https://github.com/ourPLCC/plcc-ng/commit/1410e505b0d50e1aa81643d5283131e94a3d0c9a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move completed issues to done [skip ci]
  ([`f677199`](https://github.com/ourPLCC/plcc-ng/commit/f677199460dfffc84e705afaa22e58632897d44e))

030 (parse trace), 038 (rep stale build), 039 (level-2 errors to stdout), 043 (ll1 message
  whitespace), 046 (sticky grammar) all landed via merged PRs.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plan**: Implementation plan for fix-047 sticky grammar on syntax error [skip ci]
  ([`b4cc922`](https://github.com/ourPLCC/plcc-ng/commit/b4cc92207428486c98bd944ac0bbbb19d15d8a92))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **make**: Add failing test - build/.grammar written before build stages run
  ([`23e1dca`](https://github.com/ourPLCC/plcc-ng/commit/23e1dca1325f65489aa8f0acea0ef2099e39dc01))

- **make**: Cli test - build/.grammar written even on plcc-spec failure
  ([`015c51d`](https://github.com/ourPLCC/plcc-ng/commit/015c51dd9406e93c4fbddef33dde7ea3d23c6040))


## v0.29.0 (2026-05-29)

### Bug Fixes

- Address five code review issues in sticky grammar implementation
  ([`b3638b8`](https://github.com/ourPLCC/plcc-ng/commit/b3638b8fc84f6a7734e93cbcf1bbf1dac0b83895))

- build/grammar.py: return None for empty/whitespace .grammar content - grammar_test.py: remove
  unused Path and pytest imports; add empty test - make.py: use is_dir() instead of exists() to
  avoid NotADirectoryError when build/ is a file or symlink - make.py: validate grammar file
  existence before wiping build/ on grammar switch, preventing build destruction on a misspelled
  path - make.py: write build/.grammar on the fast path (build is current) so sticky grammar works
  even when no rebuild is needed

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **test**: Update parse and rep bats tests for sticky grammar error path
  ([`a381b6f`](https://github.com/ourPLCC/plcc-ng/commit/a381b6fcdc09738c5c21176e08b9d30bba9ebd32))

Removing [default: grammar.plcc] means no-grammar errors now come from plcc-make (which says
  "grammar file not found") rather than from the command itself (which said "Run 'plcc-X --help'").
  Update the tests to match the new behavior, consistent with the scan fix.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add implementation plan for sticky grammar (issue 046)
  ([`f1b16db`](https://github.com/ourPLCC/plcc-ng/commit/f1b16db7be16415c39df540b7453e93ebc4a3e0c))

- Add issue 046 and design spec for sticky grammar
  ([`fc919b4`](https://github.com/ourPLCC/plcc-ng/commit/fc919b4dd89ab6eeda4b547018c3fb47e71aa4ab))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Add plcc.build.grammar module for sticky grammar tracking
  ([`3e4c305`](https://github.com/ourPLCC/plcc-ng/commit/3e4c30590a0d8666045e9909224ef9d889a29a33))

- **diagram**: Delegate grammar resolution to plcc-make
  ([`838e2c7`](https://github.com/ourPLCC/plcc-ng/commit/838e2c743efd2be72d4ffbb541386b73c22a9c60))

- **make**: Add grammar resolution rules and stored-grammar error path
  ([`3d93995`](https://github.com/ourPLCC/plcc-ng/commit/3d939956043573148af80c7bebd55c87e1e2ac4b))

When no --grammar-file flag is given, resolve the grammar from build/.grammar (stored by a previous
  run), falling back to grammar.plcc. When the stored grammar path is missing, emit a helpful error
  pointing to --grammar-file.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **make**: Wipe build/ when grammar file changes
  ([`dc1d069`](https://github.com/ourPLCC/plcc-ng/commit/dc1d06997fd7dcce68e305a04149971da6b41a4f))

When --grammar-file is given explicitly and differs from the stored grammar, wipe build/ entirely
  before rebuilding. This prevents stale build artifacts from the previous grammar from confusing
  the user.

Two new tests verify: - test_explicit_grammar_differs_from_stored_wipes_build: build/ is wiped -
  test_explicit_grammar_same_as_stored_does_not_wipe: build/ is preserved when grammar hasn't
  changed

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **make**: Write build/.grammar after successful build; add bats tests
  ([`2117ed3`](https://github.com/ourPLCC/plcc-ng/commit/2117ed3b6544157f44bd76485c0b5ecf1b266a8a))

- **parse**: Delegate grammar resolution to plcc-make
  ([`40058e2`](https://github.com/ourPLCC/plcc-ng/commit/40058e26f5b12f2b63e4c52429c215830247c85c))

- **rep**: Delegate grammar resolution to plcc-make
  ([`da6b793`](https://github.com/ourPLCC/plcc-ng/commit/da6b793fd49307dddfb3e28748916f64303add11))

- **scan**: Delegate grammar resolution to plcc-make
  ([`b06a149`](https://github.com/ourPLCC/plcc-ng/commit/b06a14990982a0a7173439372adf3ce1542e73d6))

- Remove default grammar.plcc check from scan - Only pass --grammar-file to plcc-make if user
  explicitly provided it - Let plcc-make own grammar resolution logic - Update test to expect error
  from plcc-make, not plcc-scan


## v0.28.1 (2026-05-29)

### Bug Fixes

- **parse**: Handle list-valued arbno children in _print_tree
  ([`2369545`](https://github.com/ourPLCC/plcc-ng/commit/236954501e90310c2d4293a68f608de1d12ced99))


## v0.28.0 (2026-05-29)

### Documentation

- **design**: Add 030 parse trace spec [skip ci]
  ([`7139693`](https://github.com/ourPLCC/plcc-ng/commit/7139693ac7632f49add97e21683d286a01d620d2))

- **plan**: Add 030 parse trace implementation plan [skip ci]
  ([`edcb1bd`](https://github.com/ourPLCC/plcc-ng/commit/edcb1bd962c01a1f9eec31612749b232e221553d))

- **schema**: Add parse-step.schema.json for parse-step JSONL records
  ([`8b33c7e`](https://github.com/ourPLCC/plcc-ng/commit/8b33c7e8e7749e29316b1aab60e5b7d84ea26bd2))

### Features

- **parse**: Add --trace flag and parse-step rendering
  ([`798a00f`](https://github.com/ourPLCC/plcc-ng/commit/798a00fbb943e63f92bf690db8ba6b9a56d7fa23))

Adds -t/--trace option to plcc-parse that passes --trace through to plcc-trees and renders
  parse-step records as indented plain text output.

- **parser**: Add --trace flag to plcc-parser-table
  ([`2a17d13`](https://github.com/ourPLCC/plcc-ng/commit/2a17d13bf1f976d7ce644f4ff6b1dca1738d8b0a))

Adds -t/--trace option that emits parse-step JSONL records (predict, shift, complete) before each
  tree on success, and always on ParseError.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add Tracer class to predictive_parser
  ([`399ba07`](https://github.com/ourPLCC/plcc-ng/commit/399ba072473d12d1d5c90666e71a54f4174bda0d))

- **parser**: Instrument parse() with optional Tracer
  ([`4d9ca64`](https://github.com/ourPLCC/plcc-ng/commit/4d9ca6494c9311b46c9b9365df5cdcaa25172eb0))

Adds tracer=None parameter to parse(); calls tracer.predict/push/shift/pop/complete at the
  appropriate points in _parse_regular and _parse_arbno. Adds 13 new tests covering predict, shift,
  complete events, depth tracking, error partial traces, and arbno iteration counts.

- **trees**: Forward --trace flag to parser plugin
  ([`0e00298`](https://github.com/ourPLCC/plcc-ng/commit/0e002987c86ca4f15358f75ecb5a1003dc3412b4))

### Testing

- **bats**: Add --trace tests for plcc-parser-table and plcc-parse
  ([`31cf1ac`](https://github.com/ourPLCC/plcc-ng/commit/31cf1ac184e070bc3b9dd4c98b52486995acb134))

Wire TreePipeline.trees_flags so --trace reaches plcc-trees without leaking into verbose child
  flags; add bats tests for predict/shift/complete output, -t shorthand, trace-before-tree ordering,
  and auto-trace on failure.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.27.0 (2026-05-28)

### Bug Fixes

- **parse**: Route parse/scan errors to stdout via print_user_error
  ([`c6e2dc8`](https://github.com/ourPLCC/plcc-ng/commit/c6e2dc8af5fc8158d37c9d2fa2e7a5e49cfbc90e))

Updates print_parse_error() to use print_user_error() instead of printing directly to stderr,
  routing parse/scan errors from both plcc-parse and plcc-rep commands to stdout as intended.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **rep**: Route interpreter/semantic errors to stdout via print_user_error
  ([`baab2af`](https://github.com/ourPLCC/plcc-ng/commit/baab2af66fcf3bd5ddfdd05e2e8ce087e8a65e65))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **design**: Add 039 level-2 errors to stdout design [skip ci]
  ([`d94c13f`](https://github.com/ourPLCC/plcc-ng/commit/d94c13fc3f9e5ade8d17bc2faa965862626bc8b3))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Fix 039 spec - note test rename for stderr→stdout [skip ci]
  ([`ddfaacf`](https://github.com/ourPLCC/plcc-ng/commit/ddfaacfcfae368f368d3a7dcec4e60bf4d93265a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 039 - level-2 errors should go to stdout
  ([`742e959`](https://github.com/ourPLCC/plcc-ng/commit/742e959623e770d1bb58cb589ccc43d7dc778c34))

- **plan**: Add 039 level-2 errors to stdout implementation plan [skip ci]
  ([`da50d53`](https://github.com/ourPLCC/plcc-ng/commit/da50d53dcd55577070e0fb6f47547938a0985445))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **cmd**: Add print_user_error helper to encode stdout intent
  ([`56c2f76`](https://github.com/ourPLCC/plcc-ng/commit/56c2f76de80fd284d28daa12ba2cfe93886ab183))

User-facing language errors (scan errors, parse errors, semantic/interpreter errors) should go to
  stdout. This helper makes that distinction explicit at every call site, replacing direct calls to
  print(..., file=sys.stderr).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **scan**: Use print_user_error for scan errors (intent, no behaviour change)
  ([`2db75c5`](https://github.com/ourPLCC/plcc-ng/commit/2db75c585034aa125a5e78c85b88dd62fe17dbf6))

### Testing

- Fix parse_test.py and plcc-parse-errors.bats for stdout errors
  ([`1ef3dd0`](https://github.com/ourPLCC/plcc-ng/commit/1ef3dd080fc21a2075972f3d9f54347f4699da95))

parse_test.py (ParseHandler) and tests/bats/integration/plcc-parse-errors.bats were asserting
  parse/scan errors on stderr. Update to assert on stdout to match the behaviour change from
  print_parse_error() using print_user_error().

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.26.2 (2026-05-27)

### Bug Fixes

- **verbose**: Preserve indentation and blank lines in plain-text stderr passthrough
  ([`ad158d1`](https://github.com/ourPLCC/plcc-ng/commit/ad158d1c52497106f7025b1bba71deaa5902c6e3))

parse_child_events stripped leading whitespace and dropped blank lines before forwarding non-JSON
  stderr lines. This broke LL(1) conflict message formatting when plcc-parse or plcc-rep captured
  plcc-make's stderr and re-emitted it.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.26.1 (2026-05-27)

### Bug Fixes

- **make**: Blank line before each LL(1) conflict block
  ([`d368f88`](https://github.com/ourPLCC/plcc-ng/commit/d368f882920bb7bedcad3be0e2d93b9f7fc48a0e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **make**: Drop 'see ll1.json' from LL(1) error header
  ([`07e8627`](https://github.com/ourPLCC/plcc-ng/commit/07e86278946aa8fd19c3da085f1a74ab38ae0687))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **issues**: Add 043 - improve LL(1) conflict message whitespace
  ([`ebb4a20`](https://github.com/ourPLCC/plcc-ng/commit/ebb4a207fbfd856a48f68d7f5f11848bbfc454e5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Close issue 036 (LL(1) conflict error messages) [skip ci]
  ([`5c54e82`](https://github.com/ourPLCC/plcc-ng/commit/5c54e82bdcc500a324530ee2c9eabcaa891d4980))

Completed in PR #149.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Update 043 - drop 'see build/ll1.json' from error line
  ([`609e970`](https://github.com/ourPLCC/plcc-ng/commit/609e97086173b5c4cc050470d8c7ae2b93278ba1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Implementation plan for issue 043 - LL(1) message formatting [skip ci]
  ([`2df1fba`](https://github.com/ourPLCC/plcc-ng/commit/2df1fbaeccaaffa7edd2ba9dafe3339ff2c3bd2d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Design for issue 043 - LL(1) conflict message formatting [skip ci]
  ([`9c83aef`](https://github.com/ourPLCC/plcc-ng/commit/9c83aef29bf352333b2e2844b2018d866c8fe5ed))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.26.0 (2026-05-27)

### Bug Fixes

- **ll1**: Handle underscore terminals and empty LCP in conflict formatter
  ([`6aca6ca`](https://github.com/ourPLCC/plcc-ng/commit/6aca6ca71985382a8bedfa73950a33461e72d6a7))

- _TERMINAL_RE: add underscore prefix support ([A-Z_][A-Z0-9_]*) to correctly render terminals like
  _SKIP as non-bracketed symbols - _first_first_lines: guard against empty LCP (arises when
  FIRST/FIRST conflict occurs via nullable leading symbols); show a restructuring tip instead of a
  malformed left-factoring example - design spec: correct JSON examples to use bare nonterminal
  names (e.g. "elsePart") matching actual ll1.json output, not "<elsePart>"

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for LL(1) conflict error messages (issue 036) [skip ci]
  ([`84efea1`](https://github.com/ourPLCC/plcc-ng/commit/84efea1e984efa6c9ebb9fde9cf43c16c2fbed00))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for LL(1) conflict messages (issue 036) [skip ci]
  ([`a6ac385`](https://github.com/ourPLCC/plcc-ng/commit/a6ac3853326ad0b96148b81694727d387a95712b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Close issues 043, 044, 045 [skip ci]
  ([`cbf2d7d`](https://github.com/ourPLCC/plcc-ng/commit/cbf2d7dad6b65b2ce9da9f6b40cc3a085f442b23))

- 043 (parseSpec drops rough-parse errors): fixed in PR #144 - 044 (syntax error caret wrong
  column): fixed in PR #144 - 045 (altname lost in ll1 pipeline): fixed in PR #147

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Field-aware symbol rendering in conflict messages
  ([`b81ef72`](https://github.com/ourPLCC/plcc-ng/commit/b81ef72b78402e7f912bd5a3032dfded35a71300))

Capturing symbols in FIRST/FIRST left-factoring suggestions now render as valid PLCC grammar syntax
  students can copy-paste:

- Non-capturing (field=None): terminal → TOKEN, nonterminal → <nt> - Capturing, default alt (field
  == sym.lower()): → <SYM> - Capturing, explicit alt (field != sym.lower()): → <SYM>field

Updated _render_symbol signature to accept field parameter. Updated _render_production and
  _first_first_lines to pass s["field"]. Added _render_symbol to test imports; added 9 new
  field-aware tests.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **ll1**: Add _longest_common_prefix helper for left-factoring suggestion
  ([`71d9136`](https://github.com/ourPLCC/plcc-ng/commit/71d91361f03e35acf6fe3f8b08813a40156fc9c1))

- **ll1**: Add conflict_type field to ll1.json conflict entries
  ([`c20afe6`](https://github.com/ourPLCC/plcc-ng/commit/c20afe6c8605bc4e36ff74ddaf4d621ecdcfe452))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **ll1**: Add format_conflict_message module with production rendering
  ([`4c3024e`](https://github.com/ourPLCC/plcc-ng/commit/4c3024ebbabc1cdc99b73fb2868f8e3a07117a93))

Implements the message formatter skeleton with production rendering logic: -
  format_conflict_message() creates LL(1) conflict messages - _render_production() formats
  individual productions with proper nonterminal/terminal symbols - Stubs for conflict-type-specific
  message lines (first_follow, first_first)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **ll1**: Implement FIRST/FIRST message body with left-factoring suggestion
  ([`b1fcfb4`](https://github.com/ourPLCC/plcc-ng/commit/b1fcfb49ffc4927964fb8e9ea81f2345d5a621f9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **ll1**: Implement FIRST/FOLLOW conflict message body
  ([`40d80a9`](https://github.com/ourPLCC/plcc-ng/commit/40d80a91ac98b4dd9d6f6eb83af14817cca05121))

- **make**: Use format_conflict_message for human-readable LL(1) conflict output
  ([`415585d`](https://github.com/ourPLCC/plcc-ng/commit/415585dce3f3dd63f380a2a3b7f747b1ce8c6075))

### Refactoring

- **ll1**: Remove unused pytest import; document LCP invariant
  ([`3d12c0d`](https://github.com/ourPLCC/plcc-ng/commit/3d12c0d0682be012f4ac3a776a043bfa616a3d14))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.25.0 (2026-05-27)

### Bug Fixes

- Concrete alt-name subclasses use own name as rule_name
  ([`987cb37`](https://github.com/ourPLCC/plcc-ng/commit/987cb373e7ec2313124ac768e9ad0ff1171d8225))

- Strengthen conflict-production schema; correct design doc for _handle_arbno
  ([`11ac0dc`](https://github.com/ourPLCC/plcc-ng/commit/11ac0dc5111e7eaabc2e84b85e3cec7822eee677))

- Update ll1.schema.json parse_table cell shape to {alt, production}
  ([`3588a25`](https://github.com/ourPLCC/plcc-ng/commit/3588a255dacd9bea42787cc230dd32c8dadb5704))

### Documentation

- Add design spec for issue 045 (altname lost in ll1 pipeline)
  ([`5be969f`](https://github.com/ourPLCC/plcc-ng/commit/5be969f6e62de3a646fe0ecc6de62696a4797d54))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issue 045 (altname ll1 pipeline)
  ([`ca39138`](https://github.com/ourPLCC/plcc-ng/commit/ca39138315c291690dac9f8b1c12357d4c3c7f90))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add issue 045 (altname lost in ll1 pipeline) [skip ci]
  ([`5120bd1`](https://github.com/ourPLCC/plcc-ng/commit/5120bd1e44063158fec1c3e8ae380a2502fb83b4))

- Close issue 039 (prefix semantics) [skip ci]
  ([`b160481`](https://github.com/ourPLCC/plcc-ng/commit/b1604812314f067bb9b8d60416fb420bea2f130a))

- Restore _arbno_grammar_and_rules docstring in ll1_result_builder_test
  ([`911a0c8`](https://github.com/ourPLCC/plcc-ng/commit/911a0c885c6cda8c7883e146fdd75d40901c6a02))

- Restore docstrings and WHY-comment in spec_json_decoder
  ([`9c4e43a`](https://github.com/ourPLCC/plcc-ng/commit/9c4e43af837eba5407cc39e8c53180df3fcd108f))

### Features

- Add Rule dataclass to spec_json_decoder
  ([`c65b99d`](https://github.com/ourPLCC/plcc-ng/commit/c65b99d415a7dd46a8478ae868916f71d494f63c))

- Decode() reads altName into Rule.alt; productions replaces field_map
  ([`15c4106`](https://github.com/ourPLCC/plcc-ng/commit/15c4106ce7856ce8a91f9daa8cd05cfd919cfb47))

- Updated decode() to build productions dict mapping (nt, rhs_tuple) to Rule objects - Rule objects
  now capture both alt name from LHS and fields list - Updated tests to assert Rule objects instead
  of field lists - All 20 decoder tests pass

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Ll1_result_builder emits new cell shape {alt, production}
  ([`2c0a45f`](https://github.com/ourPLCC/plcc-ng/commit/2c0a45f9ee6b133bdaa7f4e6041e0e14de6dc3c4))

Update ll1_result_builder to consume Rule objects from productions dict and emit parse table cells
  with {alt, production} structure instead of bare lists. This preserves alternative names from the
  spec through the LL(1) pipeline.

- Rename parameter field_map → productions throughout - Update _prod_entry to return {alt,
  production} dict cell structure - Update tests to use Rule dataclass and assert new cell format -
  Update ll1_cli to use new parameter name

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Predictive_parser uses cell alt name for tree node rule
  ([`069f017`](https://github.com/ourPLCC/plcc-ng/commit/069f017ba77e967b3b7c1a6513f6c2acf1e4d5f4))

### Testing

- Update table_cli fixtures to new cell shape {alt, production}
  ([`8c5ba3b`](https://github.com/ourPLCC/plcc-ng/commit/8c5ba3b12c554ac9c803c26e4217cd6ff71e7d35))


## v0.24.0 (2026-05-26)

### Bug Fixes

- **ci**: Trigger
  ([`72a49a0`](https://github.com/ourPLCC/plcc-ng/commit/72a49a02d606845e6b0f920e7d4d9ff2c2c61f1c))

### Documentation

- Add design spec for plcc-version command (034) [skip ci]
  ([`0ed61c1`](https://github.com/ourPLCC/plcc-ng/commit/0ed61c1504625da2b1ebce7f661b7176f0cca5fc))

- Add implementation plan for plcc-version (034) [skip ci]
  ([`ab5757b`](https://github.com/ourPLCC/plcc-ng/commit/ab5757babde6c538735dc5fabcfc25b871e8bb13))

- Close issue 034 (plcc-version) [skip ci]
  ([`024b62d`](https://github.com/ourPLCC/plcc-ng/commit/024b62d2c463e8b068a0446a4faed517e2b07931))

### Features

- **version**: Add get_version and main to plcc.version
  ([`effbee3`](https://github.com/ourPLCC/plcc-ng/commit/effbee36157a925f2343ab387f8727810ad6c61e))

- **version**: Register plcc-version entry point
  ([`68d37e7`](https://github.com/ourPLCC/plcc-ng/commit/68d37e70530b25ce385ded9125bd072bce978cb1))

### Testing

- **version**: Add bats CLI contract tests for plcc-version
  ([`25f7533`](https://github.com/ourPLCC/plcc-ng/commit/25f75338c088ebb47354008be93825a9fc2e32a7))

- **version**: Remove unused sys import
  ([`db115da`](https://github.com/ourPLCC/plcc-ng/commit/db115dae0fe65a72b57e2557ff91810a9620efa3))


## v0.23.0 (2026-05-26)

### Bug Fixes

- Drop rough-parse errors in parseSpec (043) and fix caret alignment in plcc-spec errors (044) #144
  ([`40f6641`](https://github.com/ourPLCC/plcc-ng/commit/40f66415e39874c1bf6aafc3e3703f1d822f8493))

parseSpec now surfaces rough-phase errors (circular includes, unclosed blocks) alongside lexical and
  syntactic errors plcc-spec error output now routes through verbose.emit_error, producing a
  properly aligned caret and examples hint in both text and JSON verbose modes
  VerboseContext.emit_error and reformat_child_events now render source_line and hint fields when
  present

- Route plcc-spec errors through verbose.emit_error with source line and caret (closes 044)
  ([`10160dd`](https://github.com/ourPLCC/plcc-ng/commit/10160dd3b0af475c083d39d7a86cba55f89099c9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Stop dropping rough-parse errors in parseSpec (closes 043)
  ([`9fafa0e`](https://github.com/ourPLCC/plcc-ng/commit/9fafa0e4f62ae92dd131c5758a2be7f40181346a))

### Documentation

- Add design spec for issues 043 and 044
  ([`ca0332f`](https://github.com/ourPLCC/plcc-ng/commit/ca0332fd74483782d0f000e08de1c29001749a7a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issues 043 and 044
  ([`79d3141`](https://github.com/ourPLCC/plcc-ng/commit/79d31419e3380efdd32c6abdcaf80fe2aa40de8b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add issue 044 (syntax error caret points to wrong column)
  ([`20e121f`](https://github.com/ourPLCC/plcc-ng/commit/20e121f9b07ab437467f0e6e9618593db8d9b3d8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Add kind and hint properties to MalformedBNFError
  ([`0f20a74`](https://github.com/ourPLCC/plcc-ng/commit/0f20a747d9c4aaa5b8545f63717dcba685da0722))

- Add kind and hint properties to SpecError
  ([`fa9b89c`](https://github.com/ourPLCC/plcc-ng/commit/fa9b89c688760463cb915d347d9609623df4b41c))

- Render source_line and hint in emit_error and reformat_child_events text mode
  ([`83179ac`](https://github.com/ourPLCC/plcc-ng/commit/83179ac0382da091615ecbaf1f90291e4487fd85))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- Add bats test for plcc-spec caret alignment in error output
  ([`8cfa461`](https://github.com/ourPLCC/plcc-ng/commit/8cfa46121fab5da1495e9da9fbf9945e7be68089))


## v0.22.0 (2026-05-26)

### Bug Fixes

- Surface MalformedBNFError as human-readable message in plcc-spec output
  ([`c88be47`](https://github.com/ourPLCC/plcc-ng/commit/c88be4710003f7e5e902f42083b50da8797ff152))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for issue 037 spec parser syntax error messages
  ([`8e8d0b4`](https://github.com/ourPLCC/plcc-ng/commit/8e8d0b4109d8756e18384d97a51baeb8a31392d5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issue 037 spec parser syntax error messages
  ([`85b75f1`](https://github.com/ourPLCC/plcc-ng/commit/85b75f135387b97244c53b901ba9424b48f48be2))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add issue 043 (parseSpec drops rough errors); close issue 037
  ([`fa6a008`](https://github.com/ourPLCC/plcc-ng/commit/fa6a0086bb05dce2dc066c88a45ee7098cf8ca56))

- Move issue 040 to done
  ([`b3019e9`](https://github.com/ourPLCC/plcc-ng/commit/b3019e928af00ed1fee3d9c8a9b94b5f03b0e016))

Fixed in PR #141 (fix/semantics-comments-empty-files).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Move issue 041 to done
  ([`8c1ebc2`](https://github.com/ourPLCC/plcc-ng/commit/8c1ebc2fa203c5f4e8e27b475af0d1179bce8b11))

### Features

- Give MalformedBNFError a readable __str__ with column and examples
  ([`5a12c58`](https://github.com/ourPLCC/plcc-ng/commit/5a12c58fbab93aa534f49d27a943478c609fc693))

- Syntacticparser collects MalformedBNFError instead of raising
  ([`e00faf2`](https://github.com/ourPLCC/plcc-ng/commit/e00faf261908efedcfae4a81fc3fab2f65dcd826))

parse_syntactic_spec now returns (SyntacticSpec, list[MalformedBNFError]) so callers can handle
  parse errors gracefully while parsing continues.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- Return self._errors in early-return branch for consistency
  ([`d7e9b9a`](https://github.com/ourPLCC/plcc-ng/commit/d7e9b9a4cb5d4d827a8d7f05ab1a4420db565508))

- Use _ for unused errors in valid-input syntactic spec tests
  ([`a80aedf`](https://github.com/ourPLCC/plcc-ng/commit/a80aedfece017ea70776ef2a61b3ebecf8541ee3))


## v0.21.4 (2026-05-25)

### Bug Fixes

- Treat # comment lines in semantics section as empty
  ([`01523f8`](https://github.com/ourPLCC/plcc-ng/commit/01523f897a8736f4d6cb7a7b01a3ad09637ae823))

Closes issue 040.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for issue 040 (semantics comments create empty files)
  ([`bea4086`](https://github.com/ourPLCC/plcc-ng/commit/bea40860b28cf4e37b31de405beeed905cb95140))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issue 040
  ([`0cd6a3a`](https://github.com/ourPLCC/plcc-ng/commit/0cd6a3ad303fe5d9f04967a419f84a167f2cc7f8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- Remove # comment guard from java emitter (dead code after 040 fix)
  ([`e96e540`](https://github.com/ourPLCC/plcc-ng/commit/e96e5407df774da88f79e0b66b52d918329fd0f1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- Cover indented # comment lines in parse_code_fragments
  ([`bc508e8`](https://github.com/ourPLCC/plcc-ng/commit/bc508e84e3d7fd561ee1dbb3328dfd8353094363))

Pins the lstrip() behavior so future refactors cannot silently drop it.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.21.3 (2026-05-25)

### Bug Fixes

- **diagram**: Handle missing file viewer gracefully
  ([`a97ac97`](https://github.com/ourPLCC/plcc-ng/commit/a97ac972c663c5f05b4ad5afa34868cfde3946a0))

When xdg-open (Linux) or another viewer is not installed, the run commands crashed with a Python
  traceback. Wrap _open_file in main() with try/except and print a clean error message, matching the
  error-handling pattern established in build.py.

Affects both plcc-plantuml-diagram-run and plcc-mermaid-diagram-run.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Mermaid run prints path instead of opening viewer
  ([`c20ddec`](https://github.com/ourPLCC/plcc-ng/commit/c20ddec6d6ef8f2936496b5fab7e16d86ad33103))

- **diagram**: Orchestrate emit, build, run directly; drop --through=diagram from make
  ([`adff700`](https://github.com/ourPLCC/plcc-ng/commit/adff700850b2f098311aec2b5d90c70f39e7b3d5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Plantuml run prints path instead of opening viewer
  ([`96cd124`](https://github.com/ourPLCC/plcc-ng/commit/96cd124f32bffd82bb4211828f785f5c50625f5b))

- **make**: Remove diagram operations; rename --through=diagram to --through=model
  ([`7030d45`](https://github.com/ourPLCC/plcc-ng/commit/7030d4537a8e059b670334df819af140940709f1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Cross-link superseded diagram specs; track stderr-forwarding concern
  ([`23cdeae`](https://github.com/ourPLCC/plcc-ng/commit/23cdeaedebdaa6f0a96669f7a68ce03ad5c779d8))

- **plan**: Diagram decouple from make implementation plan
  ([`cca578a`](https://github.com/ourPLCC/plcc-ng/commit/cca578a1b5d9fec5eb68d47ea8720c47dfbccb5d))

- **spec**: Decouple diagram operations from plcc-make
  ([`2688128`](https://github.com/ourPLCC/plcc-ng/commit/268812807f70630ab22fce583c2ff622537bdc2c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **diagram**: Hoist _SOURCE_EXT to module scope
  ([`1cb43db`](https://github.com/ourPLCC/plcc-ng/commit/1cb43db7ca7d32aeae9b79c01c49de1c9734df8e))

### Testing

- **diagram**: Assert --format propagated to emit, build, run
  ([`1c12867`](https://github.com/ourPLCC/plcc-ng/commit/1c128675c4bb72f0b61e3460b43e4ac1599b4168))


## v0.21.2 (2026-05-25)

### Bug Fixes

- **diagram**: Add User-Agent header to plantuml.com requests
  ([`70d1c3b`](https://github.com/ourPLCC/plcc-ng/commit/70d1c3bdfcb2ec1bab5c4fad0cfb769dc21a4609))

Cloudflare Bot Fight Mode on plantuml.com returns 403 (error 1010) when requests carry no
  User-Agent. Python's urllib sends none by default. Set User-Agent: plcc-ng/1.0 on every request.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.21.1 (2026-05-25)

### Bug Fixes

- **diagram**: Replace plantuml PyPI dep with stdlib implementation
  ([`bc75d35`](https://github.com/ourPLCC/plcc-ng/commit/bc75d3562233a3c3ca0d5fd28c6c0a526c2941db))

plantuml 0.3.0 imports `six` which is not declared as a dependency, causing `import plantuml` to
  fail with ModuleNotFoundError in any fresh install. Replace with a stdlib-only implementation
  (zlib, base64, urllib.request) that encodes PlantUML source and calls plantuml.com directly,
  removing the need for any optional dependency.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Strip base64 padding from plantuml URL encoding
  ([`ea7eb01`](https://github.com/ourPLCC/plcc-ng/commit/ea7eb0113f8bacaccdca6b04fb7f8dcb6bb8eeb6))

= padding chars are not part of the PlantUML alphabet and pass through the alphabet translation
  unchanged, producing invalid plantuml.com URLs. Strip them before translating.

Strengthen encode tests with a known-good fixture, a no-padding assertion, and an alphabet-only
  assertion.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **issues**: Add issue 041 — diagram-build should not run during make-all
  ([`4956b87`](https://github.com/ourPLCC/plcc-ng/commit/4956b873b12ee55913b89070845fbdcd731e1204))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.21.0 (2026-05-25)

### Bug Fixes

- **diagram**: Address Copilot review: package name, file ext, duplicate test
  ([`d9e1043`](https://github.com/ourPLCC/plcc-ng/commit/d9e1043f8393d448024e60c14f8137b5421aca9c))

- Use plcc-ng[diagram] (not plcc[diagram]) in error message and docs - Choose diagram source file
  extension based on format (.puml for plantuml, .mmd for mermaid) - Remove
  test_configures_timeout_on_server (duplicate of test_calls_plantuml_server_and_writes_png) -
  Update spec doc URL from http:// to https://

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Use HTTPS and add 30s timeout for plantuml.com requests
  ([`f0a673a`](https://github.com/ourPLCC/plcc-ng/commit/f0a673aaa3b8689c7d311fb08e8eeb040f47e04b))

- **diagram**: Widen error handler and strengthen build tests
  ([`348e0a9`](https://github.com/ourPLCC/plcc-ng/commit/348e0a9420a71504fb02bb8fc7494a275dfab29c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Build System

- **diagram**: Register plantuml build/run entry points and plantuml optional dep
  ([`cac7b40`](https://github.com/ourPLCC/plcc-ng/commit/cac7b40fdd59cc25e6ef4162b4c231f059991b12))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Capture ideas for improved LL(1) conflict error messages [skip ci]
  ([`afa6cc4`](https://github.com/ourPLCC/plcc-ng/commit/afa6cc4360d814a969d5f71de7f6b73d3c514172))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Capture ideas for spec parser syntax error messages [skip ci]
  ([`351b8fc`](https://github.com/ourPLCC/plcc-ng/commit/351b8fc5827b9aea601fdb66ab577d7fb7736c19))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Implementation plan for plantuml pip default [skip ci]
  ([`98296a6`](https://github.com/ourPLCC/plcc-ng/commit/98296a65dd6b0a0fa97984fdb73a78fc1f54dd35))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Spec for plantuml pip install as default diagram backend
  ([`80884a9`](https://github.com/ourPLCC/plcc-ng/commit/80884a9db68a772814419d609a7f7e3dc10b5a3f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issues 038, 039, 040 from stakeholder reports [skip ci]
  ([`239989c`](https://github.com/ourPLCC/plcc-ng/commit/239989c23acc7a50ed0fa4fa7d45fcc7e509f7f4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move resolved issues 033 and 035 to done [skip ci]
  ([`f189a1c`](https://github.com/ourPLCC/plcc-ng/commit/f189a1c034776c93d6dbdd32151636de1be9de4a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **diagram**: Add plcc-plantuml-diagram-build plugin using plantuml PyPI
  ([`1aeb6a3`](https://github.com/ourPLCC/plcc-ng/commit/1aeb6a333ff19d35053144831d6fc791b47635ce))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Add plcc-plantuml-diagram-run plugin
  ([`d73402b`](https://github.com/ourPLCC/plcc-ng/commit/d73402b0c403f4836fc16adc3f915608492309cf))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Change default diagram format from mermaid to plantuml
  ([`abb0025`](https://github.com/ourPLCC/plcc-ng/commit/abb0025c65dc7b48e7aba037d03802c29ee4143c))


## v0.20.1 (2026-05-25)

### Bug Fixes

- **diagram**: Remove unused call import from build_test
  ([`6a5ee13`](https://github.com/ourPLCC/plcc-ng/commit/6a5ee1377c3aaf7cb9ebbf69fdc322fa6ae10146))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Replace Python mmdc wrapper with npm mmdc CLI subprocess
  ([`4d2cbaf`](https://github.com/ourPLCC/plcc-ng/commit/4d2cbaf1fb7bfe0d19a17db267fb4052455921f5))

The Python mmdc package required PhantomJS (EOL) and wasn't reliably available on PyPI. Switch
  plcc-mermaid-diagram-build to shell out to the mmdc npm CLI (@mermaid-js/mermaid-cli) instead.
  Error message now points to the correct install command.

Also removes mmdc from pyproject.toml optional-dependencies and dev deps.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.20.0 (2026-05-24)

### Bug Fixes

- **diagram**: Apply Copilot suggestions and fix test isolation
  ([`6fc5baf`](https://github.com/ourPLCC/plcc-ng/commit/6fc5baf2e1c6bf172fd6c96cd755bb83ed98bac3))

- Add best-effort diagram steps to --through=all (warn and skip if PhantomJS/mmdc unavailable;
  'diagram' stage added to sentinel only on success so caching works without optional deps) - Fix
  _required['all'] docstring: diagram not required for caching - Fix list.py docstrings to reference
  plcc-*-diagram-emit pattern - Replace Windows subprocess start with os.startfile in mermaid/run.py
  - Add Windows os.startfile test to mermaid/run_test.py - Catch RuntimeError in mermaid/build.py to
  suppress Python traceback - Use --separate-stderr in plcc-rep bats tests so diagram warnings on
  stderr don't contaminate $output assertions - Add mmdc>=0.4.1 to dev dependencies

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Close file handle in mermaid-diagram-build
  ([`cedd859`](https://github.com/ourPLCC/plcc-ng/commit/cedd8595422d2cdbaa6e45852c43fd10bf8115a1))

- **diagram**: Decouple diagram build from --through=all and fix test names
  ([`fe217f9`](https://github.com/ourPLCC/plcc-ng/commit/fe217f9f7f1bfddfb07edac42e4fdf334476ceef))

- Remove 'diagram' from _REQUIRED['all'] and change execution guard from `through in ('diagram',
  'all')` to `through == 'diagram'` so that `plcc-make --through=all` (and plcc-rep) do not require
  mmdc (optional dep) - Rename plcc-plantuml-diagram.bats → plcc-plantuml-diagram-emit.bats and
  update command references to the new plcc-plantuml-diagram-emit name - Update e2e happy-path tests
  to use plcc-plantuml-diagram-emit instead of the retired plcc-diagram --output=DIR interface

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Fix plantuml emit interface, forward stderr, and update docstring
  ([`0d8ac75`](https://github.com/ourPLCC/plcc-ng/commit/0d8ac75059f7b82b4ae11c3ac22de0e61371fcc1))

- Make --output=DIR optional in plcc-plantuml-diagram-emit; writes to stdout when omitted - Fix
  VerboseContext name from 'plcc-plantuml-diagram' to 'plcc-plantuml-diagram-emit' - Forward
  captured stderr from child processes in diagram.py so errors reach the user - Update
  --diagram-format docstring in make.py to remove misleading --through=all reference - Update
  emit_test.py: replace no-args-exits-nonzero test with stdout-write test

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **make**: Init model_json to None and simplify write_sentinel call
  ([`771ca58`](https://github.com/ourPLCC/plcc-ng/commit/771ca58c1e86ed565f09e7935375cd112d7399c1))

- **packaging**: Update packaging test for diagram redesign entry points
  ([`d030401`](https://github.com/ourPLCC/plcc-ng/commit/d03040136e5d5bfc8293f23a4d78c7b5fe7e86e7))

### Build System

- Update entry points for diagram redesign
  ([`215321b`](https://github.com/ourPLCC/plcc-ng/commit/215321b62aaf13d6e952f2e0521bb52584bf8d3e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Code Style

- **diagram**: Remove redundant default in emit.py
  ([`c5e04f4`](https://github.com/ourPLCC/plcc-ng/commit/c5e04f4f55217839e8ea9a9e52174303d6304102))

### Documentation

- **issues**: Add design spec for issue 035 plcc-diagram redesign [skip ci]
  ([`0ca4723`](https://github.com/ourPLCC/plcc-ng/commit/0ca47233f4a3e4130c6825673d9a7e15acb59a5a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Add implementation plan for issue 035 diagram redesign [skip ci]
  ([`26ee4f6`](https://github.com/ourPLCC/plcc-ng/commit/26ee4f6abec9801d29992a0aa98aeb0b3c889558))

### Features

- **diagram**: Add plcc-diagram Level 2 command
  ([`043e42f`](https://github.com/ourPLCC/plcc-ng/commit/043e42f3e56aae31b8b2375d06d8c1b9cf6fa0a2))

Implements the user-facing plcc-diagram command that validates the grammar file, calls plcc-make
  --through=diagram, then calls plcc-diagram-run to display the resulting image.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Add plcc-diagram-build dispatcher
  ([`5c7b6f8`](https://github.com/ourPLCC/plcc-ng/commit/5c7b6f84228e2fbea6bafac98b8ca33501fb7515))

- **diagram**: Add plcc-diagram-emit dispatcher (replaces plcc-diagram)
  ([`f4a97c6`](https://github.com/ourPLCC/plcc-ng/commit/f4a97c64a443b55f98f03b808b372ebf83a11cd5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Add plcc-diagram-run dispatcher
  ([`355c892`](https://github.com/ourPLCC/plcc-ng/commit/355c89201bbae804b8db53057dd55157feb40dcd))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Add plcc-mermaid-diagram-build plugin
  ([`d07ed59`](https://github.com/ourPLCC/plcc-ng/commit/d07ed598f7b948227621c71bbdeb518b8b100521))

- **diagram**: Add plcc-mermaid-diagram-emit plugin
  ([`60e7912`](https://github.com/ourPLCC/plcc-ng/commit/60e79128971d498b21c2c5ed76b22e980f1f9776))

- **diagram**: Add plcc-mermaid-diagram-run plugin
  ([`4707895`](https://github.com/ourPLCC/plcc-ng/commit/4707895b837536b04791e62f41fde0689cdfa92e))

- **diagram**: Update plcc-diagram-list to discover plcc-*-diagram-emit plugins
  ([`ba8cd70`](https://github.com/ourPLCC/plcc-ng/commit/ba8cd70ad5d70c149fcccd86fa80dcdf467da587))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **make**: Add --through=diagram, --diagram-format, and set-based staleness
  ([`f9be706`](https://github.com/ourPLCC/plcc-ng/commit/f9be706a419f354ff14e484560b2936cba25971c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **build**: Replace linear staleness levels with set-based sentinel
  ([`2b59816`](https://github.com/ourPLCC/plcc-ng/commit/2b5981631858529ddccc1aa32540ec1204fd3a55))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **diagram**: Update and add bats command tests for diagram redesign
  ([`f6af6c0`](https://github.com/ourPLCC/plcc-ng/commit/f6af6c05370af75d70a858c7915c209d64b0fc1d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.19.3 (2026-05-24)

### Bug Fixes

- **java-emit**: Match language case-insensitively in section lookup
  ([`ab7c7f7`](https://github.com/ourPLCC/plcc-ng/commit/ab7c7f7da3fea57cde78e67ba4e312cb06581b3a))

- **model**: Normalize language field to lowercase in build_model
  ([`8bb86ad`](https://github.com/ourPLCC/plcc-ng/commit/8bb86ad88f44b773536362c2418ece7f4e46468a))

- **python-emit**: Match language case-insensitively in section lookup
  ([`88c02b3`](https://github.com/ourPLCC/plcc-ng/commit/88c02b3d535221e590f1129dd93fa4f5950385e4))

### Documentation

- Add implementation plan for language case normalization
  ([`ec8c91c`](https://github.com/ourPLCC/plcc-ng/commit/ec8c91c06dc2f196fac40acc46e1c9395fbb77c3))

- Add issue 035 and design spec for language case normalization
  ([`d71a7e6`](https://github.com/ourPLCC/plcc-ng/commit/d71a7e6135d0ea84eea16f79d253d8db708f45f4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update design spec to reflect lowercase normalization and emitter changes
  ([`e77cac4`](https://github.com/ourPLCC/plcc-ng/commit/e77cac464b50c357f237af6aed6f9c26189f020e))

- **issues**: Add issue 035 for plcc-diagram --output=build hang [skip ci]
  ([`cabe5d8`](https://github.com/ourPLCC/plcc-ng/commit/cabe5d8fd33bc0743c70423beabf9caa9868f6df))


## v0.19.2 (2026-05-24)

### Bug Fixes

- **parse**: Stop at first error in ParseHandler.feed()
  ([`d00f226`](https://github.com/ourPLCC/plcc-ng/commit/d00f2262611d9e2053d0e917090e29f3c953fd0d))

Multiple error records (e.g. from several lex errors) are now truncated to the first — students see
  one clear error to fix.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Pass all lex errors through plcc-parser-table
  ([`f55f58d`](https://github.com/ourPLCC/plcc-ng/commit/f55f58de4275bd572c200d9e9b260e60e1cf94d3))

Previously only the last lex error record was retained and emitted; earlier errors were silently
  overwritten. Now all lex error records are emitted immediately as they arrive.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **rep**: Stop at first error in RepHandler.feed()
  ([`8866456`](https://github.com/ourPLCC/plcc-ng/commit/88664569e0ab8ae33fc8d7fd2b157cdb4e463494))

Mirrors the ParseHandler change: multiple error records are truncated to the first so the
  interactive prompt shows one clear error to fix.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add first-error-wins design spec for plcc-parse and plcc-rep
  ([`031f7fb`](https://github.com/ourPLCC/plcc-ng/commit/031f7fb52cadabfd6fcefdc885ebf0968c55a68c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add first-error-wins implementation plan [skip ci]
  ([`56de598`](https://github.com/ourPLCC/plcc-ng/commit/56de598be732490174f34e15bb0dc7aa6a62d13d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **parser**: Rename flag and skip token accumulation after error
  ([`bce70f5`](https://github.com/ourPLCC/plcc-ng/commit/bce70f519004f8fd00ca280aa1cc704f205fa5e4))

- Rename has_lex_error → has_error_record (the flag tracks any error record, not specifically lex
  errors) - Skip appending to tokens[] once an error record has been seen, avoiding unnecessary
  memory use on large inputs - Fix verification command in spec doc (bin/test-unit →
  bin/test/units.bash)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **parser**: Update bats test for multi-error lex passthrough
  ([`3d64eee`](https://github.com/ourPLCC/plcc-ng/commit/3d64eeeae18e43b865f84c2cdef06e5facc481e1))

plcc-parser-table now emits all lex error records (not just the last), so the command-level test
  must parse JSONL and assert all records are errors.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.19.1 (2026-05-23)

### Bug Fixes

- **source-runner**: Increase read1 buffer to 65536 to avoid MAX_CANON truncation
  ([`69a9fee`](https://github.com/ourPLCC/plcc-ng/commit/69a9feeb1b0153619728059611fd3f7eb8a74337))

Linux's canonical-mode limit (MAX_CANON) is 4096 bytes. read1(4096) can return a full line split at
  exactly that boundary — no trailing \n — which _is_partial_eof() misidentifies as a ^D press and
  force-submits with eof=True. read1(65536) fits any canonical line in one call, so only a genuine
  ^D (where the terminal flushes content without \n) triggers the partial-EOF path.

Also updates _read1_tty to honor the n argument so tests can exercise the boundary, and adds a
  regression test that would fail with read1(4096) and passes with read1(65536).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **source-runner**: Use read1() in EOF mode so one ^D submits typed content
  ([`3dcc43a`](https://github.com/ourPLCC/plcc-ng/commit/3dcc43a720888bcd566cfe4073b1205732a740e1))

In Unix canonical mode, ^D flushes typed bytes to the OS read buffer without a newline. readline()
  sees a partial read and blocks, waiting for \n or a zero-length read (second ^D). read1() makes at
  most one OS read call and returns immediately with whatever is available, so the first ^D submits
  as expected.

Also removes two incorrect tests added during earlier mis-diagnosis and adds a correct failing test
  (using a read1-based mock) that the fix makes pass.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.19.0 (2026-05-23)

### Documentation

- **plan**: Add 033 rep-submit-on-eof implementation plan [skip ci]
  ([`9707f48`](https://github.com/ourPLCC/plcc-ng/commit/9707f4872000647963dec609c65822829d864738))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Add 033 rep-submit-on-eof design
  ([`d11176a`](https://github.com/ourPLCC/plcc-ng/commit/d11176a175e19595cb36e07039d432e9c387f8a1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **rep**: Switch to SubmitOn.EOF — ^D submits, Enter accumulates
  ([`5509d43`](https://github.com/ourPLCC/plcc-ng/commit/5509d436d1289a526d0b712c7209e59aae5b6b31))

### Refactoring

- **rep**: Tidy test imports — move SubmitOn import to module level
  ([`596b6a6`](https://github.com/ourPLCC/plcc-ng/commit/596b6a640679c47e035bc8841636d923d2a44206))


## v0.18.0 (2026-05-23)

### Bug Fixes

- **ci**: Trigger
  ([`9eb9c16`](https://github.com/ourPLCC/plcc-ng/commit/9eb9c16c84c2c7f31aedfc4a7d46c1d5367727af))

### Documentation

- **issues**: Add 033 rep EOF mode, 034 plcc-version; move 032 to done [skip ci]
  ([`e6caeaa`](https://github.com/ourPLCC/plcc-ng/commit/e6caeaab09f94879058e5ecbb859af3d8f21d8b9))

- **rep**: Add ^D handling design spec [skip ci]
  ([`f5b48db`](https://github.com/ourPLCC/plcc-ng/commit/f5b48dbb6a9a71eabe0ec42f73707ae74275c22e))

- **rep**: Fix spec — plcc-rep uses EOL mode, not EOF; align test strategy note [skip ci]
  ([`62fba0a`](https://github.com/ourPLCC/plcc-ng/commit/62fba0ad541b21c554a08da4d48a94d052214839))

- **source-runner**: Add ^D handling implementation plan [skip ci]
  ([`35471be`](https://github.com/ourPLCC/plcc-ng/commit/35471be59323edfc5e6e4c9b0edd0753e2935a39))

### Features

- **source-runner**: Add pending_exit field to _InteractiveState
  ([`11021c1`](https://github.com/ourPLCC/plcc-ng/commit/11021c11f5d7a39937f30a5cfa7c1f481e029fce))

- **source-runner**: Eof mode accumulates on Enter, only ^D submits
  ([`43abec0`](https://github.com/ourPLCC/plcc-ng/commit/43abec0839ea68e0fb19e624bc9800426bdcc27f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **source-runner**: Warn on first ^D on empty prompt, exit on second
  ([`2e1d977`](https://github.com/ourPLCC/plcc-ng/commit/2e1d977bd7665da79397fbc4f2baf78d351266d6))

### Refactoring

- **source-runner**: Remove dead code and duplicate test
  ([`895db63`](https://github.com/ourPLCC/plcc-ng/commit/895db636d66d353231ff065d0710cefb6b7ecd32))

### Testing

- **source-runner**: Rename eof mode test to reflect new accumulate behavior
  ([`a6a02f9`](https://github.com/ourPLCC/plcc-ng/commit/a6a02f9fd120105bf1ef071f40b982294546a5cc))


## v0.17.1 (2026-05-23)

### Bug Fixes

- **scan**: Discard zero-length matches in Matcher to prevent scanner hang
  ([`650e624`](https://github.com/ourPLCC/plcc-ng/commit/650e624b5075caf5377b4d6229795a76f263d04d))

Closes #032

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **issues**: Document scanner hang on zero-length skip match
  ([#032](https://github.com/ourPLCC/plcc-ng/pull/32),
  [`9a73f5c`](https://github.com/ourPLCC/plcc-ng/commit/9a73f5cfccebb528e86c0aad57e39eb6425e57c3))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Add design spec for fix 032 scanner zero-length skip hang [skip ci]
  ([`7fcb295`](https://github.com/ourPLCC/plcc-ng/commit/7fcb295bb5cd772e51a44b1b8b64478ca2bd68f0))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Add implementation plan for fix 032 scanner zero-length skip hang [skip ci]
  ([`4347e21`](https://github.com/ourPLCC/plcc-ng/commit/4347e21f5a6c87a6d8d7691fe74785f729a23180))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **scan**: Add regression fixture and bats test for issue 032 zero-length skip hang
  ([`1da7c3d`](https://github.com/ourPLCC/plcc-ng/commit/1da7c3d03738412b446bdcc7449f4a9c47301f68))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Add scanner integration test for zero-length skip pattern
  ([`dd5523b`](https://github.com/ourPLCC/plcc-ng/commit/dd5523b2990580ed647010973c4e1dbeee5dbc14))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.17.0 (2026-05-23)

### Bug Fixes

- **test**: Add whitespace skip to remaining fixture grammars
  ([`9c90165`](https://github.com/ourPLCC/plcc-ng/commit/9c90165c2a24e2641225bb9a0655a9f3a823f9ed))

trivial-python.plcc, lexical-only.plcc, and trivial-full.plcc also lacked skip WS, causing trailing
  newlines from echo to produce LexErrors after the scanner newline preservation change.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **test**: Add whitespace skip to trivial.plcc fixture
  ([`fe67caf`](https://github.com/ourPLCC/plcc-ng/commit/fe67caf1497fc0f1244bdb766beb424df7b9319b))

After preserving newlines in scanner input, grammars without a whitespace skip now produce LexErrors
  for trailing newlines. The trivial fixture needs skip WS to match realistic grammar behavior and
  keep integration/command tests passing.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **scan**: Add design spec for scanner newline support [skip ci]
  ([`f6ef3a7`](https://github.com/ourPLCC/plcc-ng/commit/f6ef3a7863bc42761bcf7f0b2b687848a5c0f43f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Add implementation plan for scanner newline support [skip ci]
  ([`cc0f986`](https://github.com/ourPLCC/plcc-ng/commit/cc0f9866b949e8707281abe0522e1e755c671972))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **scan**: Preserve newlines in scanner input, matching original PLCC behavior
  ([`1e0e094`](https://github.com/ourPLCC/plcc-ng/commit/1e0e094f5ac1bc1e70c9c6cc5c0e58e2fb0c2c83))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.16.0 (2026-05-22)

### Bug Fixes

- **ci**: Trigger
  ([`a8af998`](https://github.com/ourPLCC/plcc-ng/commit/a8af9983384e13abc32e8aecaa9dfe4fcb9240a4))

### Documentation

- **015**: Add design spec for _Start default generated code
  ([`7f10b28`](https://github.com/ourPLCC/plcc-ng/commit/7f10b28894adfd5c0d257fc1b0657b20c60be91a))

[skip ci]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **015**: Add implementation plan for _Start default generated code
  ([`050405b`](https://github.com/ourPLCC/plcc-ng/commit/050405b32b5d17df91bc6de6fd4c16d504b293bc))

[skip ci]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issue 031 — custom entry point with no default implementation
  ([`2910bfb`](https://github.com/ourPLCC/plcc-ng/commit/2910bfbf26c43a7617c35b05323d7ea8c510281a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move issue 015 to done [skip ci]
  ([`fdfa4f5`](https://github.com/ourPLCC/plcc-ng/commit/fdfa4f5e563ed11dc689f108aad67618b44d718b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **java-emit**: Generate _Start.java and wire start class to extend it
  ([`42a09e1`](https://github.com/ourPLCC/plcc-ng/commit/42a09e18de0b44a2a9b2a82847f0663d7fdff2a1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **python-emit**: Generate _Start.py and wire start class to extend it
  ([`8d77b3b`](https://github.com/ourPLCC/plcc-ng/commit/8d77b3be7f7458b576105f988990059f824c3c39))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **integration**: Verify no-semantics grammar emits and runs for Java
  ([`fe7c076`](https://github.com/ourPLCC/plcc-ng/commit/fe7c076d1711e818b5ad1d092e08ef9406af4214))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **integration**: Verify no-semantics grammar emits and runs for Python
  ([`204eaab`](https://github.com/ourPLCC/plcc-ng/commit/204eaab6976313c148f32407616d60428368a0f6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.15.3 (2026-05-22)

### Bug Fixes

- **parser**: Stop error cascade in plcc-parser-table
  ([`0f4e3cd`](https://github.com/ourPLCC/plcc-ng/commit/0f4e3cd5bf2fd2fc5a3d44763ec217a3d2bfeb2f))

Remove conditional break/cursor-advance logic from the except ParseError block so any parse error
  immediately breaks the loop instead of continuing to parse subsequent tokens.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **design**: Spec for stopping error cascade in plcc-parser-table
  ([`3e9b72f`](https://github.com/ourPLCC/plcc-ng/commit/3e9b72ff4420e4ecf40296beb6d8c4174cd8cdf5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plan**: Implementation plan for stop-error-cascade [skip ci]
  ([`ea128e6`](https://github.com/ourPLCC/plcc-ng/commit/ea128e6d5a0637535b063a7666e14af01f192f01))

- **spec**: Narrow requirement and fix plan accuracy per review feedback
  ([`858fa7d`](https://github.com/ourPLCC/plcc-ng/commit/858fa7d45d900200b87de6d9757f4ee19d8dff34))

- Requirement 1: scoped to ParseError path; note epsilon-advance is separate - Design: 'No other
  files change' -> 'No other runtime code paths change' - Plan architecture: 'three new tests' ->
  'one renamed + two new'; same wording fix

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **parser**: Add red test for non-eof error stopping the loop
  ([`d269fb3`](https://github.com/ourPLCC/plcc-ng/commit/d269fb38c2ffdba975f5851f39ef7aa40e1d27a5))

Rename test_skip_and_retry_emits_error_then_tree to test_non_eof_error_stops_loop and rewrite it to
  assert the new behaviour: a non-eof parse error breaks the loop immediately, emitting exactly one
  error record and zero trees.

This is the TDD red phase — the test fails until the cascade is removed.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add red test for three-bad-token cascade scenario
  ([`e487cdb`](https://github.com/ourPLCC/plcc-ng/commit/e487cdbd1307428f017610536db9a4f1bb1ef583))

Adds test_three_invalid_tokens_emit_one_error to cover the 3 2 1 spec scenario: grammar program →
  NUM PLUS NUM given [NUM, NUM, NUM, eof] should emit exactly one error, not three cascaded errors.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add red test — error after success stops further parsing
  ([`66a0417`](https://github.com/ourPLCC/plcc-ng/commit/66a0417146aec5baaedeb78c6ab775a736b10c63))

Covers the batch-file scenario: after one successful tree parse, a bad token should produce exactly
  one error and stop — not cascade to recover a second tree.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.15.2 (2026-05-21)

### Bug Fixes

- **ci**: Trigger
  ([`a3665c9`](https://github.com/ourPLCC/plcc-ng/commit/a3665c9c5b0446b4c567e32fa4a62c24abbd0627))

- **cmd**: Capture child stderr in TreePipeline and reformat verbose events
  ([`a77c0d4`](https://github.com/ourPLCC/plcc-ng/commit/a77c0d493f38d2f704d31443d7255fdb4702f49d))

Add verbose parameter to TreePipeline, capture stderr from both child processes (plcc-tokens and
  plcc-trees), and reformat any verbose JSON events through VerboseContext when verbose is set.

- **cmd**: Only pipe child stderr when VerboseContext is set
  ([`c8a4152`](https://github.com/ourPLCC/plcc-ng/commit/c8a415260e462cfcb5262d4c051e17bddd9d25d6))

- **cmd**: Thread VerboseContext through ParseHandler to TreePipeline
  ([`2c46ba7`](https://github.com/ourPLCC/plcc-ng/commit/2c46ba7b0958797e14a5171fad338492fc3aaacc))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cmd**: Thread VerboseContext through RepHandler to TreePipeline
  ([`9c07bd6`](https://github.com/ourPLCC/plcc-ng/commit/9c07bd69b31c44e8ff6196de221ba4342372a971))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **design**: Spec for fixing verbose child events uncaptured in plcc-parse and plcc-rep
  ([`9666756`](https://github.com/ourPLCC/plcc-ng/commit/9666756218d68680b4d7fd9c23147c9224140e00))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move completed issues 017, 023, 029 to done [skip ci]
  ([`909e904`](https://github.com/ourPLCC/plcc-ng/commit/909e90402582fbafad8eff5c283eeb1383b42b07))

All three were resolved in PR #120 (docs/issues-029-023-017).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move issue 011 to done [skip ci]
  ([`96e55ad`](https://github.com/ourPLCC/plcc-ng/commit/96e55ad15f34cdd8fda9292acf2ce8a112d4bc95))

- **plan**: Implementation plan for issue 011 verbose child events [skip ci]
  ([`62f7255`](https://github.com/ourPLCC/plcc-ng/commit/62f7255cab128a8ddf26f8cf4c938a64a3ff6bb0))

### Testing

- **cmd**: Extend _proc() helper with stderr support
  ([`0c108a7`](https://github.com/ourPLCC/plcc-ng/commit/0c108a7a1acb859a8b02d8a89ff5e23eb97490b0))

- **cmd**: Pin eof-probe suppression and no-verbose default in TreePipeline
  ([`25c137e`](https://github.com/ourPLCC/plcc-ng/commit/25c137eee73afa55c0c625fa11a35d41b2a5a7ef))


## v0.15.1 (2026-05-20)

### Bug Fixes

- **lang**: Exit 130 cleanly on ^C in plcc-lang-run, plcc-java-run, plcc-python-run
  ([`3b57b16`](https://github.com/ourPLCC/plcc-ng/commit/3b57b168e7cb366a2e1e05aedc45247ce3f83e2d))

### Chores

- **test**: Remove unused Path import in java run_test.py
  ([`cbdd1d7`](https://github.com/ourPLCC/plcc-ng/commit/cbdd1d77b73290e40af3614826e12decbf64f76a))


## v0.15.0 (2026-05-20)

### Bug Fixes

- **bats**: Use escaped single quotes to avoid bash string termination in e2e test
  ([`dd44191`](https://github.com/ourPLCC/plcc-ng/commit/dd4419172855602ef425130afa55ef9e2ae267a7))

- **parse**: Always include stage in error output, even when location is known
  ([`66dbf48`](https://github.com/ourPLCC/plcc-ng/commit/66dbf48c97c9e15f206ee903096c325be5504a30))

- **rep**: Exit 130 cleanly on ^C instead of printing unexpected-exit error
  ([#029](https://github.com/ourPLCC/plcc-ng/pull/29),
  [`4994316`](https://github.com/ourPLCC/plcc-ng/commit/4994316aefa16ef545cd72535be9cd00cf8a0720))

When a user presses ^C in plcc-rep, the interpreter is killed by SIGINT (returncode -2 on Unix) or
  exits with code 130. Instead of printing "interpreter exited unexpectedly" and exiting with code
  1, now exits silently with code 130 to properly propagate the signal exit code.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tokens**: Include character and position in unrecognized-character error
  ([#017](https://github.com/ourPLCC/plcc-ng/pull/17),
  [`650bfe6`](https://github.com/ourPLCC/plcc-ng/commit/650bfe6687187e3a9ad177a2a440ca140cb985f4))

- **tokens**: Update remaining pos consumers to use source
  ([#017](https://github.com/ourPLCC/plcc-ng/pull/17),
  [`94e240f`](https://github.com/ourPLCC/plcc-ng/commit/94e240f1d2a86f3daadd6be2900e3a6f51b0b578))

### Documentation

- **design**: Add design spec for issues 017, 023, and 029
  ([`e19309b`](https://github.com/ourPLCC/plcc-ng/commit/e19309b7f940ad8249111f5e80827db9b6a9c006))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add --trace/-t flag to plcc-parse (#030) [skip ci]
  ([`28497bf`](https://github.com/ourPLCC/plcc-ng/commit/28497bf264b8acd238e3db7eb5be4f27e9714b57))

- **issues**: Plcc-rep ^C shows error instead of exiting silently (#029) [skip ci]
  ([`0345577`](https://github.com/ourPLCC/plcc-ng/commit/034557760856816c09ac54032555f1c021700665))

- **plan**: Add implementation plan for issues 017, 023, and 029
  ([`9598126`](https://github.com/ourPLCC/plcc-ng/commit/95981266fdcfb8011f699ba5c5d91f155a72eb47))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **parse**: Annotate empty productions with '(empty)' in tree output
  ([#023](https://github.com/ourPLCC/plcc-ng/pull/23),
  [`bc11c5f`](https://github.com/ourPLCC/plcc-ng/commit/bc11c5f0b9544937329a42c66a60877408490cdc))

When plcc-parse prints a parse tree, productions with no children (empty productions) are now
  annotated with '(empty)' to make them visually distinct in the output.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.14.4 (2026-05-19)

### Bug Fixes

- **rep**: Align with plcc-parse — EOF errors, submit mode, child_flags, location format
  ([`24c62b6`](https://github.com/ourPLCC/plcc-ng/commit/24c62b666d8206b120d53c446fd487b27483ca00))

- Add EOF-error detection (only_eof_errors gate): incomplete expressions now show '...' continuation
  instead of an immediate error message - Switch SubmitOn.EOL → SubmitOn.EOF, matching plcc-parse's
  proven pattern - Forward child_flags to plcc-tokens and plcc-trees subprocesses - Adopt
  _location_str and stage-name fallback for error formatting - Rebuild rep.py from parse.py baseline
  so alignment is structural, not patched

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **rep**: Use SubmitOn.EOL for REPL-style multi-line evaluation
  ([`a087d72`](https://github.com/ourPLCC/plcc-ng/commit/a087d7275688482ac04e223cf253ffe006a6662f))

SubmitOn.EOF only trials the first line; subsequent lines accumulate without re-evaluation until ^D.
  SubmitOn.EOL calls _accumulate_and_evaluate on every line, which is the correct REPL behavior: the
  user types 1+<enter> (sees ...), then 2<enter> and gets a result automatically.

The EOF-error detection added to TreePipeline makes EOL mode safe: incomplete input (EOF errors with
  eof=False) suppresses the error and shows ... instead of an immediate parse error.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **specs**: Rep-pipeline alignment and TreePipeline extraction design [skip ci]
  ([`b83aa74`](https://github.com/ourPLCC/plcc-ng/commit/b83aa745652587f957c0ca99184b0a1f5eb64cd6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- **cmd**: Apply code-review fixes — rename location_str, extract test helpers
  ([`c451e76`](https://github.com/ourPLCC/plcc-ng/commit/c451e76e797ee4f94113bac59f3ff80dc4db8a7e))

- Rename _location_str → location_str (was exported but underscore-named) - Rename raw_lines → raws
  in TreePipeline.run() to match bytes framing in docstring - Add comment on stderr=None in Popen
  calls to clarify intent - Extract _proc, _tree_record, _error_record, _error_record_with_source,
  _eof_error_record into _test_helpers.py; remove duplicates from three test files

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cmd**: Extract TreePipeline shared pipeline logic from parse and rep
  ([`2cbd8c7`](https://github.com/ourPLCC/plcc-ng/commit/2cbd8c7d4a28d6eec72b7de1e9c6e2e9fb61259a))

Move the plcc-tokens | plcc-trees subprocess pipeline, record collection, and EOF-error gate into a
  single TreePipeline class in pipeline.py. Move _location_str and print_parse_error alongside it.

ParseHandler.feed() and RepHandler.feed() now delegate to TreePipeline.run(), which returns None
  (need more input) or a list of (record, raw_bytes) pairs. Each handler only contains what is
  genuinely specific to it: tree rendering for parse, interpreter dispatch for rep.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.14.3 (2026-05-19)

### Bug Fixes

- **rep**: Handle non-dict JSON values from interpreter
  ([`e08eed9`](https://github.com/ourPLCC/plcc-ng/commit/e08eed94c2e9bb9fe014a8f44231afba3728c82e))

Bare JSON numbers (and other non-dict values) caused a TypeError because 'in' requires an iterable.
  Guard with isinstance(record, dict) before checking for the 'kind' key.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.14.2 (2026-05-19)

### Bug Fixes

- **ci**: Trigger
  ([`7d65f73`](https://github.com/ourPLCC/plcc-ng/commit/7d65f738845008c808ed05dafd8b754059e6039d))

- **java-emit**: Inject body fragments into abstract baseclass files
  ([`573faf6`](https://github.com/ourPLCC/plcc-ng/commit/573faf6547832c6dc404b498c5618da97d6ca595))

### Documentation

- **design**: Add spec for issue 028 baseclass body injection [skip ci]
  ([`366cb19`](https://github.com/ourPLCC/plcc-ng/commit/366cb1966a965a374bb7f911848d619e2c699dbb))

- **issues**: Add 028 - plcc-rep baseclass semantics block injection [skip ci]
  ([`7725fdf`](https://github.com/ourPLCC/plcc-ng/commit/7725fdf7a4ef169ffc43a0891cf1f7cd7d1b26a0))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 028 to done [skip ci]
  ([`c6a18c8`](https://github.com/ourPLCC/plcc-ng/commit/c6a18c8a97ad8232fe089550b60b470ccb9ec01a))

- **plan**: Add implementation plan for issue 028 baseclass body injection [skip ci]
  ([`b004900`](https://github.com/ourPLCC/plcc-ng/commit/b0049006807878dd0778c5b65b25315abda9f640))

### Testing

- **java-emit**: Add failing tests for fragment injection into abstract classes
  ([`2b5eb29`](https://github.com/ourPLCC/plcc-ng/commit/2b5eb29e0b4961e4b46e12cdd91bd71223283605))


## v0.14.1 (2026-05-18)

### Bug Fixes

- **ci**: Trigger
  ([`9bdfa63`](https://github.com/ourPLCC/plcc-ng/commit/9bdfa634cdeec5084a9d632a330d949002813d2d))

- **parse**: Pass eof=True for non-interactive reads in SourceRunner
  ([`a878616`](https://github.com/ourPLCC/plcc-ng/commit/a87861643b4fb77e4d6a515a88ad55a28f3295ed))

Non-interactive stdin and file reads have reached actual EOF. Without eof=True, ParseHandler.feed's
  only_eof_errors guard silently discards eof parse errors instead of printing them, causing
  plcc-parse to exit nonzero with no diagnostic.

Also update issue 026 notes to describe the actual fix (removal, not guarding).

- **parser**: Break on found=eof to prevent cascade errors (fixes #027)
  ([`638039f`](https://github.com/ourPLCC/plcc-ng/commit/638039fdf6043e5e287edf6569a651bb650148e6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Remove verbose.emit_error for parse result errors (fixes #026)
  ([`f37734f`](https://github.com/ourPLCC/plcc-ng/commit/f37734febc43cfa4a7fb83719c5d68d36de91862))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for issues 026 and 027
  ([`fbf7457`](https://github.com/ourPLCC/plcc-ng/commit/fbf7457d3652181eac022f60ec8bfd5c0ecf036d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for issues 026 and 027
  ([`624548d`](https://github.com/ourPLCC/plcc-ng/commit/624548da9c99546d94e91c68a79b838001332446))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 026 - parse error JSONL suppressed without verbose [skip ci]
  ([`e8cb9f6`](https://github.com/ourPLCC/plcc-ng/commit/e8cb9f60df578ce2848b60a90e6d378467dbc5c7))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 027 - incomplete input errors instead of continuation prompt [skip ci]
  ([`ed4dfc9`](https://github.com/ourPLCC/plcc-ng/commit/ed4dfc95231a1780d80c64dd20417fb2f31b20e9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Move 026 and 027 to done [skip ci]
  ([`45412bf`](https://github.com/ourPLCC/plcc-ng/commit/45412bfa6b37782c0e68071f3f74c2a0eb046aad))


## v0.14.0 (2026-05-18)

### Bug Fixes

- **ci**: Trigger
  ([`1b79d81`](https://github.com/ourPLCC/plcc-ng/commit/1b79d81e96b927e5e8e156694081e7f2c267d28c))

- **ll1**: Rename EOF sentinel from '$' to 'eof' in parse table and follow sets
  ([`8ac86cd`](https://github.com/ourPLCC/plcc-ng/commit/8ac86cd123c78dbef9bd1df115582be2749bdb1b))

Update ll1_result_builder.py to emit 'eof' instead of '$' as the parse table and follow-set key for
  the EOF terminal, matching the renamed scanner sentinel. Update unit tests and bats test
  accordingly.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parse,scan**: Feed() gains eof flag; ParseHandler returns False for eof-only errors on trial
  [skip ci]
  ([`b9adf33`](https://github.com/ourPLCC/plcc-ng/commit/b9adf334f4960720e47cf8119013949e844d7467))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add found field to parse error records in table_cli [skip ci]
  ([`45dd071`](https://github.com/ourPLCC/plcc-ng/commit/45dd071bd927666af3be0723e45c396bef2f798f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add found field to ParseError; remove \$ special cases [skip ci]
  ([`5c030f0`](https://github.com/ourPLCC/plcc-ng/commit/5c030f07676918810f92c74652991e1c3e8ebc12))

- **parser**: Update docstring sentinel reference from '$' to 'eof' [skip ci]
  ([`793a7bf`](https://github.com/ourPLCC/plcc-ng/commit/793a7bf60877981fe975e9657239da8112696e67))

- **parser,scan**: Update sentinel guard and filter from '$' to 'eof'
  ([`10f59c1`](https://github.com/ourPLCC/plcc-ng/commit/10f59c14136d22c01c63fc37117b418916186932))

Updates the loop guard in table_cli.py and the sentinel filter in scan.py to recognize the new 'eof'
  token name instead of the old '$' sentinel.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **rep**: Add eof=False to RepHandler.feed to match ScanHandler and ParseHandler
  ([`369623f`](https://github.com/ourPLCC/plcc-ng/commit/369623fd031517a1558d352c1018d9d168fbd07d))

- **source-runner**: Whitespace-only lines are not blank; _accumulate_only always accumulates (016)
  [skip ci]
  ([`23bacca`](https://github.com/ourPLCC/plcc-ng/commit/23baccafd104ed2169ba4a855ce69bb17543ec61))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tests**: Update e2e bats sentinel filter from '$' to 'eof' [skip ci]
  ([`b2fd4d0`](https://github.com/ourPLCC/plcc-ng/commit/b2fd4d081063b6ed81dceeb2229f970f34a0496d))

- **tokens**: Update tokens_cli_test sentinel filter from '$' to 'eof' [skip ci]
  ([`8d00116`](https://github.com/ourPLCC/plcc-ng/commit/8d001165c86ef3ee5f824bd893c28df39acc4551))

### Documentation

- **contributing**: Note [skip ci] for documentation-only commits [skip ci]
  ([`0cf6226`](https://github.com/ourPLCC/plcc-ng/commit/0cf6226d5401e62e7cc8a9e66cd6c22113b755a1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add 025 - interactive first-line attempt before continuation [skip ci]
  ([`cfb56c3`](https://github.com/ourPLCC/plcc-ng/commit/cfb56c30b933f37d65762ba6511487b1379256b0))

- **issues**: Move 008, 012, 019, 022 to done after PR #112 [skip ci]
  ([`d2588e8`](https://github.com/ourPLCC/plcc-ng/commit/d2588e8daa89849eb6957ddfb857d11ad8d33169))

- **issues**: Move 016, 024, 025 to done after implementation [skip ci]
  ([`9282f1c`](https://github.com/ourPLCC/plcc-ng/commit/9282f1c6c973512d993c099e744826ff70676523))

- **plans**: Add implementation plan for issues 016, 024, 025 [skip ci]
  ([`4ea29bd`](https://github.com/ourPLCC/plcc-ng/commit/4ea29bde73219b5e8a5dc76066c8ba03cccbbfd2))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **spec**: Design for issues 016, 024, 025 - interactive session improvements
  ([`f9307d1`](https://github.com/ourPLCC/plcc-ng/commit/f9307d1f5a012fdc517eb9bca8984d268bd1e759))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **source-runner**: Trial first line before entering continuation mode (025) [skip ci]
  ([`899ce2d`](https://github.com/ourPLCC/plcc-ng/commit/899ce2d177968251779c9affe5582cad3f92d295))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tokens**: Emit 'eof' sentinel instead of '$' [skip ci]
  ([`fd4fb15`](https://github.com/ourPLCC/plcc-ng/commit/fd4fb15abed0479e1068c88b1cac2d36fa4ed02f))


## v0.13.0 (2026-05-16)

### Bug Fixes

- **cmd**: Pass submit_on to SourceRunner in scan, parse, rep
  ([`35f59ba`](https://github.com/ourPLCC/plcc-ng/commit/35f59ba1c6e2987ccc97215c7fd7d4b02bef8659))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parse**: Show stage name in error when no source location
  ([`c3ab33f`](https://github.com/ourPLCC/plcc-ng/commit/c3ab33ff12039ab4e71a5292e557135e9b25c617))

- **parse**: Update stale plcc-tree comment to plcc-trees
  ([`0590c0f`](https://github.com/ourPLCC/plcc-ng/commit/0590c0ffc2ce219388ee6b96f267714c2e0d1add))

- **parser-table**: Guard against zero-consumed infinite loop on epsilon productions
  ([`f5a6531`](https://github.com/ourPLCC/plcc-ng/commit/f5a6531c8b922f55285546e1d6c31eacafb80101))

- **parser-table,tests**: Handle empty input epsilon parse; skip $ sentinel in bats loops
  ([`9e61961`](https://github.com/ourPLCC/plcc-ng/commit/9e61961752dc165e915a1d7d3ad889ad75cd4608))

- **scan**: Skip $ sentinel from plcc-tokens in human-readable output
  ([`a08ad4b`](https://github.com/ourPLCC/plcc-ng/commit/a08ad4b1552320fb93296dcd2a885ba295125977))

- **tokens**: Update bats tests for $ sentinel in JSONL output
  ([`8d6f12d`](https://github.com/ourPLCC/plcc-ng/commit/8d6f12d72831ca8d4c654c62039489e7656b8bca))

- **tokens,parser-table**: Sentinel gets file:line:col for empty input; zero-consumed emits error
  record
  ([`eba82ff`](https://github.com/ourPLCC/plcc-ng/commit/eba82ff5725aee8ac6cb78f0a69225b5133f9eaa))

- **tree**: Complete plcc-tree → plcc-trees rename in rep, verbose_test, e2e tests
  ([`133e7fb`](https://github.com/ourPLCC/plcc-ng/commit/133e7fb00d824d0537f27bc43d401920f810d863))

Update remaining references to 'plcc-tree' command name that were missed in the rename to
  'plcc-trees', including: - subprocess call in rep.py - stage names in verbose_test.py fixtures -
  invocations in e2e test files

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tree,rep**: Complete plcc-trees rename in packaging test; update rep for JSONL stream
  ([`77cfec5`](https://github.com/ourPLCC/plcc-ng/commit/77cfec521795e6ebac367cdf10a82bbae0aa6339))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **contributing**: Update plcc-tree example to plcc-trees
  ([`adf6a4f`](https://github.com/ourPLCC/plcc-ng/commit/adf6a4f66c519abe710679807048b24980da3e27))

- **design**: Plcc-trees error handling and streaming design
  ([`7f81947`](https://github.com/ourPLCC/plcc-ng/commit/7f8194772690f8bb31e3004bdf71f02a35a6e129))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issue 024 — parser-table silent on premature EOF
  ([`ade8f3c`](https://github.com/ourPLCC/plcc-ng/commit/ade8f3c18d34be7375cfecf6b9d61d8c3b668965))

- **plan**: Implementation plan for plcc-trees error handling
  ([`ba0f586`](https://github.com/ourPLCC/plcc-ng/commit/ba0f58665ef4e11ae124af2adf633d2f78165ac9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **parse**: Uniform record iteration, file:line:col error format
  ([`8f5b6e5`](https://github.com/ourPLCC/plcc-ng/commit/8f5b6e52eab1c66304ec44b79642f0596190546f))

Rewrote ParseHandler.feed() to iterate all JSONL records from the plcc-tree pipeline output,
  handling both tree and error records. Updated _location_str to emit file:line:col (or -:line:col
  for stdin). Added tests for the new error rendering and mixed tree+error output.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser-table**: Skip-and-retry loop, JSONL stream output, exit 0 always
  ([`a537d2d`](https://github.com/ourPLCC/plcc-ng/commit/a537d2d17a9d8afec1b6ff0b57c06b354afaf236))

Replace single-parse-or-die with a skip-and-retry loop: on ParseError emit an error record and
  advance one token; on success emit the tree. Stop at the '$' sentinel. Always exit 0. Update tests
  to reflect new behavior.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **source-runner**: Add SubmitOn enum, required submit_on param, EOF accumulation mode
  ([`d1d7995`](https://github.com/ourPLCC/plcc-ng/commit/d1d799532c73ec5759676d5a6e0875bc7c9aca5f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tokens**: Emit $ sentinel token at EOF
  ([`a36babc`](https://github.com/ourPLCC/plcc-ng/commit/a36babc5278ff0c0752d9559a104ad51a769e801))

Adds a {"kind": "token", "name": "$", "lexeme": "", "source": ...} record as the final JSONL line so
  downstream tools can detect end-of-tokens without relying on Python EOF detection.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tree**: Rename plcc-tree → plcc-trees
  ([`7b76450`](https://github.com/ourPLCC/plcc-ng/commit/7b76450f511a878e1ca7ac54f4b64f9d68eed810))

### Refactoring

- **parser**: Parseerror carries source, parse() returns (tree, consumed), remove
  IncompleteInputError
  ([`352ec57`](https://github.com/ourPLCC/plcc-ng/commit/352ec57d70ac266d37d99f4aa4ecea8c028043d1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tokens**: Extract last_source from domain object, avoid JSON round-trip
  ([`f7f378c`](https://github.com/ourPLCC/plcc-ng/commit/f7f378cdfe50040e8a9f9c572bbfa1ab4fb04ccf))

Replace json.loads(format_record(...)) round-trips with direct attribute access on Token/Skip
  objects (obj.line.file, obj.line.number, obj.column), and eliminate the double format_record call
  in the Skip branch.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.12.3 (2026-05-15)

### Bug Fixes

- **source-runner**: ^d after partial text force-submits buffer (020)
  ([`0d756fd`](https://github.com/ourPLCC/plcc-ng/commit/0d756fd9dedd9f04eeef14242b6e6497d561a685))

- **source-runner**: ^d exit prints newline before returning to shell (018)
  ([`486bd9a`](https://github.com/ourPLCC/plcc-ng/commit/486bd9aea775dc68e16d24ea01193e149a35254d))

- **source-runner**: ^d in continuation submits buffer instead of exiting (020a)
  ([`6b136fe`](https://github.com/ourPLCC/plcc-ng/commit/6b136fe09d2cbb348f2b89c5d480641910dc92fb))

When user presses ^D in continuation mode (buffer has content), the loop now resets state and
  continues instead of breaking. This allows further input to be processed after the buffered
  content is submitted.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **source-runner**: Exit with error when force-submit is rejected by handler (021)
  ([`daac3da`](https://github.com/ourPLCC/plcc-ng/commit/daac3da1e2ec9dd5daefb1f6d43c6580d186e788))

- **source-runner**: Wrap prompt print in KeyboardInterrupt try block
  ([`7a19511`](https://github.com/ourPLCC/plcc-ng/commit/7a19511d98eedba92ab5807f2d71201cf5d4fda9))

### Code Style

- **source-runner**: Remove docstring and redundant comment
  ([`892628e`](https://github.com/ourPLCC/plcc-ng/commit/892628ecd7b963f28919b1f0193fcd5830e380d4))

### Documentation

- **design**: Spec for interactive ^D and blank-line fixes (018, 020, 021)
  ([`2caf17d`](https://github.com/ourPLCC/plcc-ng/commit/2caf17d40eecb17ed3d45733193229a288852b4c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design,plan**: Fix line-type count (four→five) and remove 'pure' from _process_line
  ([`f350539`](https://github.com/ourPLCC/plcc-ng/commit/f350539b68976422b95a535acbb19400bb6390fa))

- **design,plan**: Update 021 description to reflect eof=True error-and-exit fix
  ([`7c2da27`](https://github.com/ourPLCC/plcc-ng/commit/7c2da27fe6a77316df46a5a97f0d7caf8b276826))

- **issues**: Add issues 016-023 from interactive plcc-parse testing
  ([`63b6c06`](https://github.com/ourPLCC/plcc-ng/commit/63b6c06799bd6e3e62c8bf7cd71d74d55e18133a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Close 018, 020, 021 — interactive ^D and blank-line fixes
  ([`d07dcd5`](https://github.com/ourPLCC/plcc-ng/commit/d07dcd59dbddbaea17c020f43c3c0425d1f79abd))

- **plan**: Implementation plan for interactive ^D and blank-line fixes (018, 020, 021)
  ([`f5c0bdd`](https://github.com/ourPLCC/plcc-ng/commit/f5c0bdda6096e86fb92782547c6307806defc304))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **source-runner**: Restore run() return contract docstring
  ([`82be1c8`](https://github.com/ourPLCC/plcc-ng/commit/82be1c822894fe71c0af0f80579aa58346d08632))

### Refactoring

- **source-runner**: Add _InteractiveState and predicate methods
  ([`f4aa1bc`](https://github.com/ourPLCC/plcc-ng/commit/f4aa1bc375cd97cb1f4797bbe6d5803717386aa9))

- **source-runner**: Extract _process_line and handler methods; make 021 force-submit explicit
  ([`bb70ccc`](https://github.com/ourPLCC/plcc-ng/commit/bb70ccc7d7e63949eba1bb1552dd51003cb54a1c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.12.2 (2026-05-14)

### Bug Fixes

- **source-runner**: ^c exits or clears buffer; blank line submits continuation
  ([`d7345ad`](https://github.com/ourPLCC/plcc-ng/commit/d7345ade7f060b81153090ef79fdefe507fd358d))

### Documentation

- **design**: Add interactive shell UX spec for issues 013 and 014
  ([`8a02bb2`](https://github.com/ourPLCC/plcc-ng/commit/8a02bb2798e57739c90df6fba81b6802e5a78225))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Blank line appends EOF to buffer before feeding
  ([`ca9e347`](https://github.com/ourPLCC/plcc-ng/commit/ca9e347e6c5673bd24ad86e9aeaa3061a883e5a4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Blank-line feed resets unconditionally — EOF always produces output
  ([`68bd5ff`](https://github.com/ourPLCC/plcc-ng/commit/68bd5ffbb60670a0af86da1abb96adb8da7972b6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Replace evaluating flag with split try/except and _evaluate helper
  ([`9e1d2c9`](https://github.com/ourPLCC/plcc-ng/commit/9e1d2c94edf108d0c13dd5556d545a74b973c74c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issues 013, 014, 015 for interactive shell and default codegen
  ([`75d4d09`](https://github.com/ourPLCC/plcc-ng/commit/75d4d094eb0f6c749a6502aad9f979ba5ef0dee1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Close 013 and 014 interactive shell ^C and blank-line fixes
  ([`06c08c5`](https://github.com/ourPLCC/plcc-ng/commit/06c08c531fa40e70702f753abf22b0e34c65372f))

- **plan**: Add implementation plan for issues 013 and 014
  ([`b816373`](https://github.com/ourPLCC/plcc-ng/commit/b8163733f1a8096c34c2b5c68e99891e130e977c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **source-runner**: Add failing tests for issues 013 and 014
  ([`1a3b43c`](https://github.com/ourPLCC/plcc-ng/commit/1a3b43cf77e91951992ef939e2256edafd481366))


## v0.12.1 (2026-05-14)

### Bug Fixes

- **parse-syntactic-spec**: Align token name regex with lexical grammar
  ([`dda3cc3`](https://github.com/ourPLCC/plcc-ng/commit/dda3cc3b22a3a7bd02ce4a949891289d8181408c))

Regex was [A-Z][A-Z_]* — excluded digits and leading underscores. Lexical parser uses
  [A-Z_][A-Z0-9_]*, so names like NUM1 were misclassified as non-terminals. Fix aligns the syntactic
  regex with the authoritative lexical name grammar and adds a regression test.

- **parse-syntactic-spec**: Single-char token names now classified as terminals
  ([`b7a4315`](https://github.com/ourPLCC/plcc-ng/commit/b7a4315b465c73c690e789ba15442e3852e3e5b4))

### Documentation

- **issues**: Close 009 model generator token type wrong
  ([`1e42742`](https://github.com/ourPLCC/plcc-ng/commit/1e42742b5b80ae14c872f07e4aee0802828ad0f6))

- **plans**: Add implementation plan for fix 009 token type wrong
  ([`be7abd6`](https://github.com/ourPLCC/plcc-ng/commit/be7abd6e6c4d7750d2f01e626193023e1e131684))

- **specs**: Add design for fix 009 token type wrong
  ([`5cae813`](https://github.com/ourPLCC/plcc-ng/commit/5cae813e40f18bf411cfd886f8896626f35dde78))

### Testing

- Add regression tests for single-char capturing terminals
  ([`86e988f`](https://github.com/ourPLCC/plcc-ng/commit/86e988f63cf164110713bf4717eaf9e1438f1f1c))

Add two new tests to verify that single-character token names like <A> and <A>:b are properly
  recognized as CapturingTerminal instead of falling back to RhsNonTerminal. These tests currently
  fail due to bug in parse_syntactic_spec.py line 92, where the regex requires 2+ chars.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.12.0 (2026-05-13)

### Bug Fixes

- **parse**: Exit non-zero and include stage name when error record received
  ([`1de38a0`](https://github.com/ourPLCC/plcc-ng/commit/1de38a0d2b204f0f7bd18d450491bb14f8168510))

- **review**: Apply copilot review items 1-4
  ([`2baceb8`](https://github.com/ourPLCC/plcc-ng/commit/2baceb87f7f17e672ea1ed9718b3074198200526))

- runner.run() return value now checked in parse.py and rep.py main(); non-interactive incomplete
  input exits nonzero - table_cli.py: remove spurious verbose.emit_error on IncompleteInputError -
  table_cli.py: add "stage":"plcc-parser-table" to parse error record - table_cli_test.py: remove
  duplicate incomplete-input test - source_runner_test.py: add four return-value tests

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Remove redundant proc.wait() after communicate()
  ([`73d5b0b`](https://github.com/ourPLCC/plcc-ng/commit/73d5b0b9c6b0c61862d28e973112abb9c489a840))

- **source-runner**: Return completed boolean from run()
  ([`7eda6dd`](https://github.com/ourPLCC/plcc-ng/commit/7eda6dd848d5842e052d2ab477d39353d22a0db9))

Non-interactive feeds that signal incomplete input (handler returns False) now cause run() to return
  False; interactive mode always returns True.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for shared SourceRunner (scan/parse/rep IO unification)
  ([`082887a`](https://github.com/ourPLCC/plcc-ng/commit/082887a303b322adc7d4c5414c91708fe0ecad16))

- Add implementation plan for SourceRunner
  ([`03c9121`](https://github.com/ourPLCC/plcc-ng/commit/03c91211114405623933d296eb7d712f667633d9))

- Clarify RepHandler interpreter-state guarantee in source-runner spec
  ([`24b20b0`](https://github.com/ourPLCC/plcc-ng/commit/24b20b008cc2b89ffeb3cc991e1477c1a0ea8bfd))

- **issues**: Add issue 010 for intermittent bats flakiness in full commands suite
  ([`78e31cf`](https://github.com/ourPLCC/plcc-ng/commit/78e31cfc2373cd174bb225b1265efef82a426175))

- **issues**: Track missing source position in parser-table error record (012)
  ([`bc25fd3`](https://github.com/ourPLCC/plcc-ng/commit/bc25fd3597603676b2118a9a434ae7cb26b5e0b9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Track verbose child event capture bug in plcc-parse/plcc-rep (011)
  ([`abd18de`](https://github.com/ourPLCC/plcc-ng/commit/abd18de9fad48f0145dfb9f83771d3bbcf3c08ff))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **cmd**: Add SourceRunner with source routing and interactive loop
  ([`8e319e4`](https://github.com/ourPLCC/plcc-ng/commit/8e319e453e4c876fc8cc268d231f212ed503fad1))

SourceRunner orchestrates reading content from files or stdin, routing it to a handler for
  processing. Interactive stdin mode supports multi-line input with continuation prompts and Ctrl+C
  handling.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parse**: Add ParseHandler; route IO through SourceRunner
  ([`9f63b45`](https://github.com/ourPLCC/plcc-ng/commit/9f63b457971f3f901477b55833eeabca266b1a69))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add IncompleteInputError for EOF-mid-parse detection
  ([`afad167`](https://github.com/ourPLCC/plcc-ng/commit/afad167a33052ebbf9ea955f5b21bb062d55447e))

IncompleteInputError is a ParseError subclass that distinguishes "ran out of tokens mid-parse" from
  "wrong token present". It's raised when lookahead is $ (end-of-stream sentinel) in parsing
  contexts where a production was expected.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser-table**: Emit error record to stdout on parse error; silent on incomplete
  ([`4cfdc32`](https://github.com/ourPLCC/plcc-ng/commit/4cfdc3280cf18f24511dafcd4173f1c5c6f267bf))

Implement Task 3 from the source-runner plan: - Real parse errors (wrong token): emit {"kind":
  "error", "message": "..."} to stdout AND to stderr (via verbose); exit 1 - Incomplete input
  (IncompleteInputError): emit nothing to stdout; exit 1

This distinguishes between parse failure (caller should see the error) and incomplete input (caller
  can detect "need more input" by checking for empty stdout).

Updates test_nothing_written_to_stdout_on_error to use incomplete input and adds two new tests: -
  test_parse_error_emits_error_record_to_stdout: verifies real errors emit -
  test_incomplete_input_produces_no_stdout: verifies incomplete input is silent

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **rep**: Add RepHandler; route IO through SourceRunner
  ([`4258147`](https://github.com/ourPLCC/plcc-ng/commit/4258147fc02b7b02dbc26a6e02411fc22050f6e6))

- **scan**: Add ScanHandler; route IO through SourceRunner
  ([`f8763b5`](https://github.com/ourPLCC/plcc-ng/commit/f8763b53f74a29561751d590c3e1f598e255ab11))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tokens**: Add --source-name flag to override stdin label
  ([`45c20da`](https://github.com/ourPLCC/plcc-ng/commit/45c20da395577f655a3b13e1c08bd1e3ae17f4f9))


## v0.11.0 (2026-05-12)

### Bug Fixes

- **scan**: Close proc.stdout after read loop; update test mock and docs
  ([`aa492a1`](https://github.com/ourPLCC/plcc-ng/commit/aa492a1b1b5bd67809df7b68086808d51e66265a))

- Add proc.stdout.close() before proc.wait() to release the file descriptor promptly when scanning
  multiple sources - Update scan_test.py mock to use io.BytesIO (supports close()) instead of
  iter([]) - Correct spec: the TTY-hint-absent bats test also requires --separate-stderr - Correct
  plan Task 1 snippet to show the full updated test block with --separate-stderr and $stderr check

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for plcc-scan TTY hint (issue 005)
  ([`6ca4d19`](https://github.com/ourPLCC/plcc-ng/commit/6ca4d19c093ff9805acb1506628e120d7a1b8084))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for plcc-scan TTY hint (issue 005)
  ([`a9c05a5`](https://github.com/ourPLCC/plcc-ng/commit/a9c05a56b8d44290017f0aacf680638844e9f7a2))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Mark 005-007 as done
  ([`0de5fb5`](https://github.com/ourPLCC/plcc-ng/commit/0de5fb54f89dad51501adb9d6d2d12ff20253d63))

### Features

- **scan**: Print TTY hint each time interactive stdin read begins
  ([`56ef53a`](https://github.com/ourPLCC/plcc-ng/commit/56ef53ace15d3fc31c4722a69cbd5511dd6ec2a8))

### Testing

- **scan**: Add failing unit tests for TTY hint
  ([`41554be`](https://github.com/ourPLCC/plcc-ng/commit/41554bebfa7a5f19e977621c6e0ea783855d2502))

- **scan**: Check stderr (not combined output) for TTY hint absence
  ([`64f04cc`](https://github.com/ourPLCC/plcc-ng/commit/64f04ccc7400d9beb6800d0d538b8d3b74517bd6))

- **scan**: Update bats hint checks to match new message casing
  ([`d355619`](https://github.com/ourPLCC/plcc-ng/commit/d3556199de26db55e62a7e26c2505c29b31016a1))


## v0.10.0 (2026-05-12)

### Bug Fixes

- **scan**: Improve --trace output format
  ([`17e054e`](https://github.com/ourPLCC/plcc-ng/commit/17e054e8946c627e86f89930f2efaea4de27ae4a))

- Add Candidates: heading before match attempts - Mark winning candidate with -> instead of * -
  Exclude zero-match candidates from Candidates list - Use location: disposition: details format for
  token and skip lines - Remove regex from token/skip lines (still present in Candidates) - Add
  blank line after each match block

- **scan**: Remove --show-skips, --show-line, --show-regex, --show-attempts flags
  ([`9828cc8`](https://github.com/ourPLCC/plcc-ng/commit/9828cc853307e7f00528d1d5cb36b6af3f4a4d2f))

BREAKING CHANGE: the four --show-* flags are removed. Use --trace, which already implied all four,
  to enable detailed output.

### Documentation

- Add design spec for plcc-scan trace cleanup (issues 006, 007)
  ([`8924cb5`](https://github.com/ourPLCC/plcc-ng/commit/8924cb555db5a2e6b8dd9c8f285be97808294edb))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for plcc-scan trace cleanup
  ([`0b3d9c4`](https://github.com/ourPLCC/plcc-ng/commit/0b3d9c4234a8c1a22eb0825d3448984e85b9fd68))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Fix stale _render_record signature in spec and plan
  ([`d963496`](https://github.com/ourPLCC/plcc-ng/commit/d96349651a3218e2c0aa48507b9258b640b23c63))

show_regex was removed from the signature during implementation. Update both documents to reflect
  the final three-parameter API and correct the file-map note about new files.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Add issues 005-009 from review session, retire 002-004
  ([`cb2533d`](https://github.com/ourPLCC/plcc-ng/commit/cb2533d325bc8ce8f1234fea67dab7061eed42d3))

- 005: plcc-scan missing ^D hint for interactive sessions - 006: plcc-scan --trace output format
  improvements - 007: remove --show-* flags from plcc-scan - 008: plcc-parse multi-program input,
  streaming output, error recovery - 009: model generator emits token name as field type instead of
  Token - move resolved issues 002, 003, 004 to docs/issues/done/

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.9.1 (2026-05-11)

### Bug Fixes

- Release smoke test uses --grammar-file flag explicitly
  ([`f60221b`](https://github.com/ourPLCC/plcc-ng/commit/f60221b36c797872fa638e2a85900f2bb4d2ffd3))

- Update release smoke test to use --grammar-file interface
  ([`6ee4c75`](https://github.com/ourPLCC/plcc-ng/commit/6ee4c7568d1fd5e062586b41e5c2a4591c7b3679))


## v0.9.0 (2026-05-11)

### Bug Fixes

- Atomic temp file in build/, validate --through value in plcc-make
  ([`4164663`](https://github.com/ourPLCC/plcc-ng/commit/416466383d8465c91b98488f65fd3f5953157ea9))

- Remove shutil.rmtree from slow path; build/ is managed incrementally
  ([`a86fa5a`](https://github.com/ourPLCC/plcc-ng/commit/a86fa5a759d0a1d350c3d3913cb3686a2c2dbf7a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update packaging smoke test to use --grammar-file interface
  ([`f5e9ab5`](https://github.com/ourPLCC/plcc-ng/commit/f5e9ab59e85c30da60ef3e1ee7f26ec0ce43dbcc))

### Documentation

- Add unified-build design spec
  ([`99b0367`](https://github.com/ourPLCC/plcc-ng/commit/99b0367c32a4f6c5018516a91265138b644a890e))

Captures the design for making build/ the single source of truth across all Level 2 commands, with
  hash-based staleness detection, --through=scan|parse|all for incremental builds, and defaulting
  the grammar file to ./grammar.plcc.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add unified-build implementation plan
  ([`de53f05`](https://github.com/ourPLCC/plcc-ng/commit/de53f05dad7738572cd21d23f31a494b1b204c9d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Add staleness algorithm, --grammar-file, --through to plcc-make
  ([`e12c97f`](https://github.com/ourPLCC/plcc-ng/commit/e12c97f59d18688d681abf95071912be6c0d666b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add staleness module for build sentinel management
  ([`2090313`](https://github.com/ourPLCC/plcc-ng/commit/209031322e687022cdc05fdc08667b5276182545))

- Plcc-parse uses build/ via plcc-make, drops positional GRAMMAR arg
  ([`932b525`](https://github.com/ourPLCC/plcc-ng/commit/932b525a2d4b3eca92b650c3e1808491b9afa9c2))

Replace positional GRAMMAR argument with --grammar-file=<path> option (default: grammar.plcc).
  Delegate build steps to plcc-make --through=parse and read spec.json/ll1.json from build/ instead
  of temp files.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Plcc-rep uses build/ via plcc-make, drops positional GRAMMAR arg
  ([`a875996`](https://github.com/ourPLCC/plcc-ng/commit/a875996917681c290f942f14e572c69cd7a09ce6))

Remove the silent-ignore bug where the positional GRAMMAR arg was accepted but never used. Now uses
  --grammar-file=<path> (default: grammar.plcc) and calls plcc-make as its first step to guarantee
  artifact presence.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Plcc-scan uses build/ via plcc-make, drops positional GRAMMAR arg
  ([`1d6ad01`](https://github.com/ourPLCC/plcc-ng/commit/1d6ad012500d08ab696b2f561b6a4652c67bdd4e))

Replace plcc-spec temp-file block with plcc-make --through=scan call; add --grammar-file=<path>
  option (default: grammar.plcc); use build/spec.json instead of a temp file; add rebuild/no-rebuild
  and lexical-only tests.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- Add type hint and document unknown-level behavior in staleness
  ([`98f0dda`](https://github.com/ourPLCC/plcc-ng/commit/98f0dda53d3fe4de488e6d3424b08952995acb5d))

- Clean up make.py — remove unused verbose param, redundant sentinel delete
  ([`c62e44f`](https://github.com/ourPLCC/plcc-ng/commit/c62e44f8112d1a19cdb7e06947b6b04bf8404589))

- Remove unused verbose parameter from _report_ll1_failure function signature and all call sites -
  Remove redundant delete_sentinel(build_dir) in LL(1) failure branch (already called in slow path)
  - Drop or 'grammar.plcc' and or 'all' fallbacks since docopt provides defaults

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- Add lexical-only fixture for partial-grammar tests
  ([`ae7a6db`](https://github.com/ourPLCC/plcc-ng/commit/ae7a6db6e391e67d5e8c0a28e3cd4b180836250a))

- Rewrite plcc-make bats for staleness, --through, --grammar-file
  ([`7e319c0`](https://github.com/ourPLCC/plcc-ng/commit/7e319c0380299e95dd6a4e45e7c3cd59f581b37d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update e2e and integration tests for new --grammar-file interface
  ([`2d5d054`](https://github.com/ourPLCC/plcc-ng/commit/2d5d05421b348cdd3d25f8c87a170602e98ed652))

- fix e2e/happy-path.bats: replace positional grammar arg with --grammar-file= in plcc-make calls;
  update "cleans build/ on rebuild" test to use a modified grammar copy to trigger staleness - fix
  e2e/plcc-rep.bats: replace positional grammar arg with --grammar-file= in all plcc-rep calls;
  replace "exits non-zero without build/" test (now invalid since plcc-make auto-builds) with "exits
  non-zero when grammar file does not exist" - fix integration/plcc-parse-errors.bats: replace
  positional grammar arg with --grammar-file= in plcc-parse call - feat(make): clean build/
  directory on rebuild (shutil.rmtree) so stale artifacts from previous builds are removed when
  grammar hash changes

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.8.1 (2026-05-11)

### Bug Fixes

- Remove dead TokenOrSkipProperties definition; isolate plcc-scan verbose lines in regression tests
  ([`991da44`](https://github.com/ourPLCC/plcc-ng/commit/991da4427ce28597ddde8e47e8d84922f16f783e))

TokenOrSkipProperties was defined but never referenced in the schema.

The -vv/-vvv regression tests now grep for ^plcc-scan: before counting lines, isolating scan-emitted
  events from child-process stderr so the tests remain correct if plcc-spec or plcc-tokens add
  output at higher verbosity levels in future.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Remove trailing comma from definitions in token.schema.json
  ([`091c654`](https://github.com/ourPLCC/plcc-ng/commit/091c65490dacb9f6b1df6a8abd9625fff3f5234c))

Trailing comma after AttemptEntry's closing brace caused JSONDecodeError in check-jsonschema (Python
  3.14's strict JSON parser).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.8.0 (2026-05-11)

### Bug Fixes

- **scan**: Add flush=True to contextual prints; guard unlink with existence check
  ([`81489d0`](https://github.com/ourPLCC/plcc-ng/commit/81489d0502ce25d7d5b1028789bff69a61712a1c))

### Documentation

- Add design spec for scan verbosity redesign and output richness flags
  ([`d073875`](https://github.com/ourPLCC/plcc-ng/commit/d073875a2966b3ae5aa5ec629de45cb89d1eb139))

Splits --verbose (stderr diagnostics) from new --show-skips/--show-attempts flags (stdout richness).
  Per-token detail travels in the JSONL stream; plcc-scan stops capturing/reformatting child stderr.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for scan verbosity redesign
  ([`a059224`](https://github.com/ourPLCC/plcc-ng/commit/a059224918fd043ea2dcccd306b2f9382b890b4a))

- Correct Split the knob table — enrichment controlled by --show-*, not -v
  ([`659bbe0`](https://github.com/ourPLCC/plcc-ng/commit/659bbe00e6f84a3d92444e65426b8e68f4645906))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Fix -v counting flag syntax in scan verbosity design spec
  ([`125c4f5`](https://github.com/ourPLCC/plcc-ng/commit/125c4f57b0d107b97ebc3b235a24d4376abf6e01))

Replace -v=N notation with docopt-ng counting style: -v (level 1), -vv (level 2), -vvv (level 3).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Move TTY ^D hint to plcc-scan stdout, independent of -v
  ([`b129473`](https://github.com/ourPLCC/plcc-ng/commit/b129473ca8ed32c9d29c15ba6215bfd3719543cf))

Hint is always printed to stdout as the first line when stdin is a TTY. Removes it from -v stderr
  diagnostics and from plcc-tokens responsibility.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Rename --show-all to --trace/-t in design and plan
  ([`c626038`](https://github.com/ourPLCC/plcc-ng/commit/c626038a8161dc2b9173d0e0a2daa611d2db4df6))

Stakeholders identified --show-all as trace output, aligning with the original PLCC --trace flag for
  parse. Both plcc-scan and plcc-tokens use --trace consistently; the note explaining the "identical
  name, different meanings" tension is removed since the flags now share the same clear intent.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Resolve findings 2 and 3 from spec quality review
  ([`f7f2b8f`](https://github.com/ourPLCC/plcc-ng/commit/f7f2b8f91585f246a9e01dae77659f517579ef01))

Finding 2: source_line comes from obj.line.string — no new dataclass field. Finding 3: attempts
  contains all matching rules (tokens and skips) in definition order, regardless of which type wins;
  winner is whatever match() returns.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Resolve remaining spec quality review findings
  ([`36daee8`](https://github.com/ourPLCC/plcc-ng/commit/36daee8c4371b554598869191934ead10b5a560e))

- Finding 1: note pattern field emitted as "regex" JSON key - Finding 4: fix column numbers in
  --show-skips and --show-all examples - Finding 5: clarify --show-attempts ordering relative to
  cursor line - Finding 6: note --show-regex applies to skip lines too - Finding 7: char_count ==
  len(lexeme), included as renderer convenience - Finding 8: is_skip carried for downstream
  consumers, not used by renderer - Finding 9: explicitly call out oneOf third branch and attempts
  item schema - Finding 11: grammar file does not emit per-file event (not a source file) - Finding
  12: add TTY hint text string - Finding 13: TTY hint test is bats only (remove "or bats" pytest
  hedge) - Finding 14: add attempts item field list with types - Finding 15: acknowledge --show-all
  name is intentional on both commands

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update scan verbosity design spec with revised output flags
  ([`3986f51`](https://github.com/ourPLCC/plcc-ng/commit/3986f5137f3f42e6b081f86a9e2e20c8bc31c56e))

Simplifies default output (no regex), replaces individual tokens flags with --show-all on
  plcc-tokens, adds --show-line/--show-regex/--show-all on plcc-scan, and updates -v references to
  match merged main branch.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **scan**: Add pattern and attempts fields to Token and Skip
  ([`7a802b6`](https://github.com/ourPLCC/plcc-ng/commit/7a802b6e13bfb9f07eeb2e673e09dc4a9f537907))

Add two new fields to Token and Skip data carriers with compare=False to enable downstream
  formatting and diagnostics while keeping existing equality assertions backward-compatible.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Populate pattern always; build attempts list when record_attempts=True
  ([`b756caa`](https://github.com/ourPLCC/plcc-ng/commit/b756caaa359f2e87ed7f192e50af4d6e07c6e6c9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Replace stderr capture with pass-through; add --show-* enrichment flags and TTY hint
  ([`1f3e266`](https://github.com/ourPLCC/plcc-ng/commit/1f3e266741fe3d2095afb99562562f22974ac4a4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **schema**: Add SkipRecord branch and optional enrichment fields
  ([`5aae9a5`](https://github.com/ourPLCC/plcc-ng/commit/5aae9a532357ebdb47490a55368fff96c3ed6f60))

- **tokens**: Add --trace flag, SCANNING_FILE event, emit skips and enriched records
  ([`aaa3fe4`](https://github.com/ourPLCC/plcc-ng/commit/aaa3fe45b91f612c561a824ebe9b17476cf98f60))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tokens**: Formatter handles Skip and emits enriched fields when show_all=True
  ([`b40bbd2`](https://github.com/ourPLCC/plcc-ng/commit/b40bbd2481a511b0031fa2a9d7833883fd5dcf2b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **scan**: Add --show-* flags, --trace, verbose levels, and TTY hint bats tests
  ([`ea4f98b`](https://github.com/ourPLCC/plcc-ng/commit/ea4f98b354479c1a9acab11c81645b23a55a406b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Fix test_record_attempts_skip_win_includes_token_candidates to cover skip-beats-token
  scenario
  ([`1597b13`](https://github.com/ourPLCC/plcc-ng/commit/1597b1382eb7643bd64b14a8c0dd3ffbb36e3d3e))

- **tokens**: Add --trace enrichment and -v per-file event bats tests
  ([`eb0008a`](https://github.com/ourPLCC/plcc-ng/commit/eb0008a33af35ee4595b288dc4ca7cb9ec18360d))

- **tokens**: Add skip enrichment test and use constructor kwargs in fixtures
  ([`02c18c0`](https://github.com/ourPLCC/plcc-ng/commit/02c18c0918da776ade4ed78e42a819ec99b85793))


## v0.7.0 (2026-05-08)

### Bug Fixes

- Update module docstring to reference -v flag
  ([`d47cf35`](https://github.com/ourPLCC/plcc-ng/commit/d47cf35ce98f2a2081c8c35f7b2eef2dfdc7afd7))

### Documentation

- Add design spec for -v counting flag replacement
  ([`83af049`](https://github.com/ourPLCC/plcc-ng/commit/83af049a2f789ed1d9c8f66f86950e89ecbfc119))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for -v counting flag
  ([`e1296cd`](https://github.com/ourPLCC/plcc-ng/commit/e1296cdf926071563c6e67fb68e67d3d5a8d1418))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- Add [-v ...] to all CLI usage lines for docopt-ng counting
  ([`19b04db`](https://github.com/ourPLCC/plcc-ng/commit/19b04db883543a8fa8fb57e8c8f2a8babe6c2563))

Also fix ll1_cli_test.py to use -v/-vv instead of the removed --verbose=LEVEL flag.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Replace --verbose=LEVEL with -v counting flag in verbose.py
  ([`9a035e2`](https://github.com/ourPLCC/plcc-ng/commit/9a035e21bb601f0a8e208d742d6a87bd77b1e9bc))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- Add -vv bundled-flag acceptance test for plcc-scan
  ([`efc13d0`](https://github.com/ourPLCC/plcc-ng/commit/efc13d0b75ce723c11cb1d61211a39b11ab2ab49))

- Update bats command tests to use -v flag
  ([`7d80a2a`](https://github.com/ourPLCC/plcc-ng/commit/7d80a2a6424c4c0f4698084edd01686b497bc80e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Update java emit test to use -v flag
  ([`368f8ad`](https://github.com/ourPLCC/plcc-ng/commit/368f8ad3b955d4b304b9993fd2357eb087a0f323))


## v0.6.0 (2026-05-07)

### Bug Fixes

- **scan**: Exit nonzero when plcc-tokens fails
  ([`9a9ee36`](https://github.com/ourPLCC/plcc-ng/commit/9a9ee36f75da7598dfbe89e6fe2160e99200f953))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for scan token file provenance
  ([`653cf22`](https://github.com/ourPLCC/plcc-ng/commit/653cf22fa7a0929b20e4df9fb79885e951a34717))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for scan token file provenance
  ([`65130f1`](https://github.com/ourPLCC/plcc-ng/commit/65130f12f36611801b98c4801c249e8dc14bfffb))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Correct design spec — custom helpers, not Source, for line reading
  ([`bdfe469`](https://github.com/ourPLCC/plcc-ng/commit/bdfe46953abfb4e300b08b8a44e0d5021e4e73f7))

Source.strip() corrupts column numbers; document the actual approach.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Completed 001
  ([`3f3b90c`](https://github.com/ourPLCC/plcc-ng/commit/3f3b90c59a97ca545e0b0ac8fedfc27032ee915f))

### Features

- **scan**: Pass SOURCE args to plcc-tokens; always include file in location
  ([`9cdb107`](https://github.com/ourPLCC/plcc-ng/commit/9cdb107438ea787083e88547e36990490bda87dc))

- **tokens**: Accept SOURCE file args; label stdin lines with file='-'
  ([`78eab7d`](https://github.com/ourPLCC/plcc-ng/commit/78eab7d4eb8e68190ed6043ef4dbcbd1bc2ccb2c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- **parse**: Update location format in token leaf assertion
  ([`9585add`](https://github.com/ourPLCC/plcc-ng/commit/9585add40ff8487355feb409f8836d0c480a3ac1))

- **scan,tokens**: Update and add file-provenance bats tests
  ([`8667753`](https://github.com/ourPLCC/plcc-ng/commit/866775327830ce3e6238c36a2b8da369adc4b206))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.5.0 (2026-05-07)

### Bug Fixes

- **parse**: Detect upstream error records and report to stderr, exit nonzero
  ([`070d16b`](https://github.com/ourPLCC/plcc-ng/commit/070d16bc0c2e1a1242425b460e80e837a3088ec0))

- **scan**: Handle error records inline, drop --continue-on-error from plcc-tokens call
  ([`4e1807a`](https://github.com/ourPLCC/plcc-ng/commit/4e1807a8a645bba90d016870d7486d7920e25c43))

- **tokens,scan**: Update schema for error records; use message from record in scan output
  ([`111acb5`](https://github.com/ourPLCC/plcc-ng/commit/111acb5f74039c140d6d3c46a071a01861b50183))

- token.schema.json extended to oneOf[TokenRecord, ErrorRecord] to cover the full plcc-tokens stdout
  stream - plcc-scan now reads message from the error record instead of hard-coding the wording

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- **issues**: Add plcc-scan review issues 001-004
  ([`79bad29`](https://github.com/ourPLCC/plcc-ng/commit/79bad2949d13d7e4f8be16679f49db260d94e20b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **issues**: Delete done issues
  ([`7f1e9f1`](https://github.com/ourPLCC/plcc-ng/commit/7f1e9f14a06ff1e84c9bf561e6ff6d1fde19cc61))

- **plans**: Add implementation plan for scan errors inline (issue 001)
  ([`5220538`](https://github.com/ourPLCC/plcc-ng/commit/5220538905d45be3d03bfb680fbf6a9ffb8be0b1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add design for scan errors inline (issue 001)
  ([`9a3fd0d`](https://github.com/ourPLCC/plcc-ng/commit/9a3fd0d1b77ca1a46bdcc7c2263deff4c0d93f55))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Features

- **tokens**: Add format_error_record to jsonl_formatter
  ([`9fdaf9e`](https://github.com/ourPLCC/plcc-ng/commit/9fdaf9ee93fd1829ee095071c3016beb7387d49f))

- **tokens**: Emit lex errors as stdout records, exit 0, drop --continue-on-error
  ([`c2b5cb6`](https://github.com/ourPLCC/plcc-ng/commit/c2b5cb6188ee17af25938a776031523ad77e65f4))

### Refactoring

- **tokens**: Add type guard to format_error_record
  ([`b2ea457`](https://github.com/ourPLCC/plcc-ng/commit/b2ea4579cb4a08919e21b93a8adbc21c9321c48c))

### Testing

- **bats**: Update lex error tests for new stdout-record protocol
  ([`6ed919a`](https://github.com/ourPLCC/plcc-ng/commit/6ed919aeb7bfff77474f1d8a98f77c901080cddd))

- **bats**: Update plcc-parser-table lex error test for stdout-record protocol
  ([`d9a305c`](https://github.com/ourPLCC/plcc-ng/commit/d9a305c97caddab313d226f47a042661e60eecd4))

- **tokens**: Assert exit 0 explicitly in lex error test
  ([`0c56226`](https://github.com/ourPLCC/plcc-ng/commit/0c562263d7d199022513d760761295c62045ae3d))


## v0.4.0 (2026-05-07)

### Bug Fixes

- **scan**: Handle BrokenPipeError in feeder, flush token output, drop feed join
  ([`5469144`](https://github.com/ourPLCC/plcc-ng/commit/546914412946bbada258beecd8479e15c1ecf73f))

### Features

- **scan**: Stream tokens line by line using Popen
  ([`39ed0bf`](https://github.com/ourPLCC/plcc-ng/commit/39ed0bff9b77e010321798cf93e3bd76c109c5a3))

Replace subprocess.run with Popen + two background threads so input is fed and output is consumed
  concurrently, enabling line-by-line streaming instead of buffering all input before starting.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.3.0 (2026-05-07)

### Bug Fixes

- **scan**: Print tokens before and after lex errors
  ([`3699e8f`](https://github.com/ourPLCC/plcc-ng/commit/3699e8f53dc266099bea1d5bb5a8a010581d86ed))

Pass --continue-on-error to plcc-tokens and always process stdout regardless of exit code, so tokens
  emitted before a lex error are not silently discarded.

### Features

- **tokens**: Add --continue-on-error flag
  ([`d4d402d`](https://github.com/ourPLCC/plcc-ng/commit/d4d402d37d392a9351c581ebb353a28279ae7b7b))

### Refactoring

- **scan**: Remove unreachable error branch from token loop
  ([`3fe33d6`](https://github.com/ourPLCC/plcc-ng/commit/3fe33d6cac71648dd0228cbd62e6247b69a07cf3))


## v0.2.0 (2026-05-06)

### Features

- **parse**: Accept '-' as stdin
  ([`5ee2b73`](https://github.com/ourPLCC/plcc-ng/commit/5ee2b73cbddc536c1841d7a5f742c5a5bb04a414))

- **scan**: Accept '-' as stdin
  ([`a0f314b`](https://github.com/ourPLCC/plcc-ng/commit/a0f314b1768c8ff7cbc343abbf2196fe2c90d6cc))

### Performance Improvements

- **parse**: Avoid quadratic copy when building input
  ([`ae7c4cb`](https://github.com/ourPLCC/plcc-ng/commit/ae7c4cb019aada5a7c40cb0473c594c649691cc6))


## v0.1.3 (2026-05-06)

### Bug Fixes

- **make**: Brief usage mentions --help
  ([`d8138b8`](https://github.com/ourPLCC/plcc-ng/commit/d8138b8d31aa2fb711402012d565a3f98109e1d5))

- **parse**: Brief usage mentions --help
  ([`fbb383a`](https://github.com/ourPLCC/plcc-ng/commit/fbb383ab723a545f5f8a9c60b8b6cfaef906e06a))

- **rep**: Brief usage mentions --help
  ([`950f7cc`](https://github.com/ourPLCC/plcc-ng/commit/950f7ccc018d0bd0f2afce09f0d0d678c36b9e32))

- **scan**: Brief usage mentions --help
  ([`e93ea70`](https://github.com/ourPLCC/plcc-ng/commit/e93ea70f09ebd107defa706dcc0f524b740a0cb1))

### Chores

- Pin devcontainer feature versions in lock file
  ([`e361107`](https://github.com/ourPLCC/plcc-ng/commit/e3611074694f67179deaa84e778995233ed6e055))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add design spec for plcc-scan issues 001–004
  ([`4cd258e`](https://github.com/ourPLCC/plcc-ng/commit/4cd258e31f746e5e0b7ed481a4e29345fa48abca))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add file-based issue tracker design
  ([`25f440b`](https://github.com/ourPLCC/plcc-ng/commit/25f440b5518288c22a7fec9338d0e33a462ef00b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add implementation plan for plcc-scan issues 001–004
  ([`4c52065`](https://github.com/ourPLCC/plcc-ng/commit/4c52065bfaaeff756ba5b6f8b67de6941440e52b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add issue tracker implementation plan
  ([`4111885`](https://github.com/ourPLCC/plcc-ng/commit/4111885fa9e8e7d6df42270f10460e3f7327a8e1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add plcc-scan issues 001-004
  ([`bc5f121`](https://github.com/ourPLCC/plcc-ng/commit/bc5f121ba7fad8ccf49caba80887c9911b3b2a3f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Scaffold file-based issue tracker
  ([`64d1701`](https://github.com/ourPLCC/plcc-ng/commit/64d17018cc4484f57b8ab993683e79c8dee61e7b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Refactoring

- Add line before help hint
  ([`29aa064`](https://github.com/ourPLCC/plcc-ng/commit/29aa064f7ae4b7d087f121ee4c1029aebc22d96f))

- Print newline using a separate print statement
  ([`5604310`](https://github.com/ourPLCC/plcc-ng/commit/5604310dd33c97042193b302aeb0f3e67d8cf3d9))

Co-authored-by: Copilot Autofix powered by AI <175728472+Copilot@users.noreply.github.com>

- Print newline using a separate print statement
  ([`511fccc`](https://github.com/ourPLCC/plcc-ng/commit/511fcccb3f060494dfb4372da9488f9ae544664d))

Co-authored-by: Copilot Autofix powered by AI <175728472+Copilot@users.noreply.github.com>

- Print newline using a separate print statement
  ([`4b90167`](https://github.com/ourPLCC/plcc-ng/commit/4b90167018d20c9dbb5ad12af514eb493cc06913))

Co-authored-by: Copilot Autofix powered by AI <175728472+Copilot@users.noreply.github.com>

- Print newline using a separate print statement
  ([`15f7a51`](https://github.com/ourPLCC/plcc-ng/commit/15f7a5193e5ba823502322d111bdcbca9727ec75))

Co-authored-by: Copilot Autofix powered by AI <175728472+Copilot@users.noreply.github.com>


## v0.1.2 (2026-05-05)

### Bug Fixes

- **ci**: Skip attestations on TestPyPI to avoid duplicate-attestation error on PyPI
  ([`935058a`](https://github.com/ourPLCC/plcc-ng/commit/935058a4356e39ff808677ace6e0c7eddee2d293))

The pypa/gh-action-pypi-publish action generates `.publish.attestation` files alongside the wheel
  during publish. When the same dist/ is published to two indexes (TestPyPI then PyPI) within one
  workflow run, the second call sees the leftover attestation files from the first and errors out.
  Disabling attestations on the TestPyPI step lets the PyPI step generate them fresh — TestPyPI
  doesn't need attestations anyway.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.1.1 (2026-05-05)

### Bug Fixes

- **ci**: Skip existing files on TestPyPI to allow workflow retries
  ([`5849700`](https://github.com/ourPLCC/plcc-ng/commit/5849700de973dec2048666cf754f700aea18b08d))

TestPyPI rejects re-uploading any filename that has been deleted (filename-reuse policy), which
  makes failed workflow runs unrecoverable without bumping the version. skip-existing: true makes
  TestPyPI publish tolerant of both already-uploaded and tombstoned filenames.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>


## v0.1.0 (2026-05-05)

### Bug Fixes

- --version in docker
  ([`de41205`](https://github.com/ourPLCC/plcc-ng/commit/de41205655df0355c8e3edfd8a5d0830f2cca32e))

- Automate release ([#45](https://github.com/ourPLCC/plcc-ng/pull/45),
  [`324c210`](https://github.com/ourPLCC/plcc-ng/commit/324c210c6a1f7c5555201779df013928217eb9f3))

## fix: update CI/CD pipeline

* On pushes to PR: * Run automated tests. * Build multi-arch images tagged with PR for manual
  testing. * On merge to main, release by: * Use Conventional Commits to determine next release
  number. * Tag commit with next release number. * Build multi-arch images tagged with new release
  number (3.2.1, 3.2, 3, and latest) * Create release entry in GitHub with release notes (commit
  messages).

## refactor: determine `--version` from git tag, then VERSION file, otherwise "Unknown"

- Improve installer 89 ([#90](https://github.com/ourPLCC/plcc-ng/pull/90),
  [`24a7d3a`](https://github.com/ourPLCC/plcc-ng/commit/24a7d3a07ad80591e12fcd55a0526e1458c3fa4c))

We now ask users to place a callback into .bashrc or .zshrc. That way upgrades that need a change in
  the environment do not need to ask the user to update their .bashrc or .zshrc.

- Print error messages to stderr in ProcessFiles.java
  ([`ea099d2`](https://github.com/ourPLCC/plcc-ng/commit/ea099d255cde6ce48db5ed0f4f7645725dd6447f))

Co-authored-by: Timothy Fossum <fossum@halsum.org>

Fixes #22

- Print messages to stdout instead of stderr
  ([`05c0908`](https://github.com/ourPLCC/plcc-ng/commit/05c0908dcf49bffb5ddcb41ff37ef98a539a8e34))

Co-authored-by: Timothy Fossum <fossum@halsum.org>

Tim wrote the code and the above comments. I'm just the committer.

- Remove BASH_SOURCE, not POSIX ([#85](https://github.com/ourPLCC/plcc-ng/pull/85),
  [`5f05e44`](https://github.com/ourPLCC/plcc-ng/commit/5f05e448de997467edc5d7680e575c7c364131ff))

- Remove use of new Java switch statements/expressions
  ([#62](https://github.com/ourPLCC/plcc-ng/pull/62),
  [`7de5505`](https://github.com/ourPLCC/plcc-ng/commit/7de55056d6c2ded764c9ef8d9d33b769b7028c80))

Fixes #61, allowing PLCC to work with Java 11 or higher.

---

Co-authored-by: Timothy Fossum <fossum@halsum.org>

- Renormalize line endings in bat files
  ([`c37f559`](https://github.com/ourPLCC/plcc-ng/commit/c37f5598fc77e38f768e78c6236e45a29d787015))

- Restore missing plcc bash script ([#17](https://github.com/ourPLCC/plcc-ng/pull/17),
  [`1c0e35c`](https://github.com/ourPLCC/plcc-ng/commit/1c0e35c61dad32e1535b791680c493f03d59305c))

- Restore VERSION file
  ([`7747836`](https://github.com/ourPLCC/plcc-ng/commit/7747836b8ca4f5dd66692b19c8106c70efe2823e))

- Small fix regarding handling of EOF on input
  ([`7edba11`](https://github.com/ourPLCC/plcc-ng/commit/7edba1123d8e8567fdcf24ee7c54ee7acc5c79b5))

PL/PLCC/Std/Scan.java taken from
  https://drive.google.com/drive/folders/1x8aM6Xi6RMRuJZHVnzdSJZlS-8U_buaa?usp=sharing at
  20200711T235651Z-001.

---

Related to https://github.com/ourPLCC/course/issues/8

- Token propagation when using a custom scanner ([#51](https://github.com/ourPLCC/plcc-ng/pull/51),
  [`fa28f15`](https://github.com/ourPLCC/plcc-ng/commit/fa28f157ac456421e23804283be117ce731ddc2a))

Hi.

I just noticed that the Token.template file in the Std directory uses an old representation of how
  token names get propagated into a Token.java file when using plcc.py with the '!pattern=' flag in
  the input file.

The '!pattern=' flag is typically used when writing a compiler and not a PLCC-generated interpreter.
  In this case, the user must supply a stand-alone scanner (Scan.java) instead of using the
  Scan.java found in the Std library directory. Such a Scan.java file must still implement the IScan
  interface, so its 'cur' method must still return a Token object.

Token.template (instead of Token.pattern) in the Std library is used to generate Token.java when
  PLCC is flagged to use a hand-crafted scanner other than the Scan.java in the Std directory. Note
  that this only applies in the case where PLCC is used to create a compiler instead of an
  interpreter.

I have uploaded Token.template into the plcc.pithon.net directory. This will *not* have any effect
  on any of the examples in the Code directory, since none of these examples use the '!pattern='
  flag.

Tim

Co-authored-by: Timothy Fossum <fossum@halsum.org>

- Use raw strings for regex ([#82](https://github.com/ourPLCC/plcc-ng/pull/82),
  [`33577a4`](https://github.com/ourPLCC/plcc-ng/commit/33577a44c6406770dfef2fd72bc91dcd75d450aa))

Closes #66

- Use REUSE Software for licensing ([#93](https://github.com/ourPLCC/plcc-ng/pull/93),
  [`1c44a19`](https://github.com/ourPLCC/plcc-ng/commit/1c44a193f820d8f4bd428e044e9f27e4d6138343))

Closes #69

- Version bump
  ([`89bfc62`](https://github.com/ourPLCC/plcc-ng/commit/89bfc62245cd6074a774724fb5e8d37ea7945403))

- Version bump
  ([`b4ae438`](https://github.com/ourPLCC/plcc-ng/commit/b4ae438b105a288903a2c6f99072b3dc6addd383))

- **bats/commands**: Fix test isolation, JSONL handling, and fragile interpolation
  ([`01d493c`](https://github.com/ourPLCC/plcc-ng/commit/01d493c988cab9912b76246a5159f278d8f2c58d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **bin**: Improve shell script safety and clarity
  ([`8dec94e`](https://github.com/ourPLCC/plcc-ng/commit/8dec94efb95ec191dd851576c8ec576fc83fcbca))

- **bin/build**: Self-install pdm in package.bash if not present
  ([`a3178e3`](https://github.com/ourPLCC/plcc-ng/commit/a3178e31c7803d75996f3af613b4024d67e91950))

- **bin/test**: Add venv to PATH before running bats
  ([`16e88b2`](https://github.com/ourPLCC/plcc-ng/commit/16e88b218f5a127c0eb7c02676dddc8b729ad2f7))

- **bin/test**: Put installed venv on PATH before running plcc-make
  ([`f96dac6`](https://github.com/ourPLCC/plcc-ng/commit/f96dac6c8cc42dad219aabf9d72745e0b47de942))

- **bin/test**: Use plantuml_only fixture in packaging test (trivial has Java section)
  ([`a6e0011`](https://github.com/ourPLCC/plcc-ng/commit/a6e001119acdce07ed1368c030f1545618ffb31e))

- **build_model**: Strip trailing whitespace from %%% block delimiters
  ([`3c9a531`](https://github.com/ourPLCC/plcc-ng/commit/3c9a531a9ee402f72832496483b1455d38205dc0))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cd**: Remove username from test image
  ([`46548c0`](https://github.com/ourPLCC/plcc-ng/commit/46548c04cd403c3bfede7986897a541881e54dc5))

- **cd**: Use working parts of ci.yaml
  ([`c1c5a03`](https://github.com/ourPLCC/plcc-ng/commit/c1c5a030e0f136f060c5782e6fdbbc589fdf9f48))

- **ci**: Define version component variables
  ([`371a597`](https://github.com/ourPLCC/plcc-ng/commit/371a59749a796d68b31c0654b919b3728cf7b662))

- **ci**: Only create full version tags
  ([`f03b0ba`](https://github.com/ourPLCC/plcc-ng/commit/f03b0ba31b649491e35bb0a4a5eb35af8f19dfeb))

- **ci**: Smoke test uses real plcc-make CLI (no --output, build/ relative to CWD)
  ([`f2b22b5`](https://github.com/ourPLCC/plcc-ng/commit/f2b22b5553536123d34986c238052c39f339f6de))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **ci**: Trigger
  ([`1809c7b`](https://github.com/ourPLCC/plcc-ng/commit/1809c7ba8811e7f9fac049317c9912ebb718ccde))

- **ci**: Try again
  ([`e809fc9`](https://github.com/ourPLCC/plcc-ng/commit/e809fc9de714dc228b14204e1a07bbe7e4cdc4e6))

- **ci**: Try again
  ([`5d523c6`](https://github.com/ourPLCC/plcc-ng/commit/5d523c67ee3d669c55f572b70515510f9be9265f))

- **e2e**: Prevent languages-java.bats from running twice in e2e.bash
  ([`1960721`](https://github.com/ourPLCC/plcc-ng/commit/19607218f0823bef00165995c0df4b26475cc92d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **Grammar**: Any set-compatible object is a valid nonterminal
  ([`7e4d798`](https://github.com/ourPLCC/plcc-ng/commit/7e4d798845c6acfb06df1ff71c5be921368802d0))

- **Grammar**: When terminal found to be nonterminal remove it from terminals)
  ([`8268841`](https://github.com/ourPLCC/plcc-ng/commit/8268841256af776068cadb51031655aab681ae45))

- **java-emit**: Remove bare imports and add runtime.Token import in generated Java
  ([`00101d2`](https://github.com/ourPLCC/plcc-ng/commit/00101d20ff23d5df810eec908e0de7f707605322))

- **java-emit**: Remove stub runtime/Main.java that conflicts with generated Main.java
  ([`b813dd0`](https://github.com/ourPLCC/plcc-ng/commit/b813dd05ae1396274d915766675e5a089643216e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **lang**: Add Python plugin unit tests, fix quoting style and BATS assertion
  ([`fa4400b`](https://github.com/ourPLCC/plcc-ng/commit/fa4400b17e12f76036244d64e5bfc1220c8f0ad9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **lang**: Fix Java stub JSON parsing, add unit tests, fix quoting and BATS coverage
  ([`624704e`](https://github.com/ourPLCC/plcc-ng/commit/624704ec7aa31c30b0a7a686495f33bd73e762b0))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **lang**: Remove unused shutil import and add main() test coverage for list
  ([`19897ce`](https://github.com/ourPLCC/plcc-ng/commit/19897ce0212a54a00c76120a029abe1127eaf6ee))

- **lexical**: Use re.error instead of re.PatternError (added in 3.13, not 3.12)
  ([`6a6d8f7`](https://github.com/ourPLCC/plcc-ng/commit/6a6d8f7b4129665867b44a522c3e8b54222a900f))

- **ll1**: Remove speculative --format option and wire input loading in stub
  ([`864150d`](https://github.com/ourPLCC/plcc-ng/commit/864150d5797ae979fdd608486205c32909fc7494))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **make**: Fix left-recursion cycle reporting in _report_ll1_failure
  ([`6b12d9a`](https://github.com/ourPLCC/plcc-ng/commit/6b12d9afb854d84cbcc36de22566bb2d38e61bc2))

- **model**: Strip trailing newline before %%% delimiter comparison
  ([`ab7e752`](https://github.com/ourPLCC/plcc-ng/commit/ab7e752b8e229ffe469510e08410d869de315321))

- **packaging**: Use project venv Python to satisfy >=3.12 requirement
  ([`2ec9d62`](https://github.com/ourPLCC/plcc-ng/commit/2ec9d62773d46d1fc8d60c9d337567e9f2a8a845))

System python (3.11.2) fails to install the wheel because pyproject.toml requires Python >=3.12. Use
  the PDM-managed .venv/bin/python (3.14.2) instead.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parse-blocks**: Treat %%% with trailing whitespace as block delimiter
  ([`bd6a16b`](https://github.com/ourPLCC/plcc-ng/commit/bd6a16bf3c7424263fc166ab41e799780038843c))

The regex for block markers required %%% to be followed by either nothing or a # comment, rejecting
  %%% with trailing spaces. Some legacy grammar include files (e.g. RANDSCONT/cont) end blocks with
  '%%% ' (trailing space), causing each subsequent Java code line to be parsed as a separate
  fragment with the line content as its class_name. Widening the regex to allow optional trailing
  whitespace (before any optional # comment) fixes the misparse without changing behavior for valid
  inputs.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Pass error records through in plcc-parser-table
  ([`dc76921`](https://github.com/ourPLCC/plcc-ng/commit/dc76921749195e62d3e1a19cf80d2e81b2fc3e40))

- **parser**: Simplify dead branch and add --verbose-format test
  ([`464b5be`](https://github.com/ourPLCC/plcc-ng/commit/464b5be42c3f7af41ee6f82970bc2f75be0a950a))

- **plcc-python-run**: Add -u flag to prevent buffering deadlock in plcc-rep
  ([`880aba5`](https://github.com/ourPLCC/plcc-ng/commit/880aba56c778ba4d3526419134081185a9286d10))

- **plcc-rep**: Fix GRAMMAR docstring, drain stderr pipes, remove duplicate --verbose-format option
  ([`b037f35`](https://github.com/ourPLCC/plcc-ng/commit/b037f352cf2522c164267d8eb8921ac216232eea))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plcc-rep**: Handle empty semantic sections and BrokenPipeError on interpreter write
  ([`5e3f665`](https://github.com/ourPLCC/plcc-ng/commit/5e3f66549164918e2ecf954eede2f11b16f94a48))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plcc.py**: Enforce uppercase token names
  ([`1be4531`](https://github.com/ourPLCC/plcc-ng/commit/1be4531b2b75e0f31a3912d1817cb262a94ea07c))

Co-authored-by: fosler <fossum@halsum.org>

- **pypi.yaml**: New version
  ([`4f8860c`](https://github.com/ourPLCC/plcc-ng/commit/4f8860cc14c55d4ff91b4cc21a75561ac16d50f4))

- **scan**: Close spec file handle, remove stale skeleton test
  ([`aa55af2`](https://github.com/ourPLCC/plcc-ng/commit/aa55af2137c10b429be997aa48807696a42b55fa))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan.matcher**: Skips ignored if a token matches before any skips
  ([`d8a4630`](https://github.com/ourPLCC/plcc-ng/commit/d8a46304ef3f00102324b54df5f4970461b14c83))

- **shell**: Use bash in shebang
  ([`973da7f`](https://github.com/ourPLCC/plcc-ng/commit/973da7fca0bc5e119a861c37ac6e308830c5245b))

- **test**: Fix temp-file leaks and shell injection in bats integration tests
  ([`64c5214`](https://github.com/ourPLCC/plcc-ng/commit/64c5214d8dcea0654d81b18d63e82defe2178ecc))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **test**: Pass spec JSON (not .plcc path) to plcc-tokens in pipeline integration test
  ([`73c1a53`](https://github.com/ourPLCC/plcc-ng/commit/73c1a5377924973e95b81cfba57fad7263289a65))

- **test**: Update plcc-rep and plcc-lang-run tests for new REPL implementation
  ([`0f7001a`](https://github.com/ourPLCC/plcc-ng/commit/0f7001abda1bc35ad04b6b24b5ddd73a4ad17806))

- plcc-rep tests now set up build/ artifacts in setup() using plcc-spec, plcc-ll1, and
  plcc-python-emit - Output assertion updated from "evaluated" to "42" (actual REPL output) -
  plcc-lang-run dispatch test fixed: use valid tree JSONL with proper children pairs format and
  check for "result" instead of old "evaluated" string

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Build System

- Add release-image.yml file
  ([`3be8ecb`](https://github.com/ourPLCC/plcc-ng/commit/3be8ecb145ebb389d4deb85b53ef53877b91165d))

- Cleanup ([#14](https://github.com/ourPLCC/plcc-ng/pull/14),
  [`e487714`](https://github.com/ourPLCC/plcc-ng/commit/e487714d42502479906574735798bda7da5d7abd))

- delete .trash - delete .gitpod/workflows - delete .github stuff - remove version tags - move
  .vscode/settings.json into .devcontainer/devcontainer.json - simplify PR template. - update
  .devcontainer - remove dockerfile - ignore .pdm-build/ - delete containers/ - delete installers -
  delete unused tests - delete .releaserc - delete .versionrc

- Extensions ([#40](https://github.com/ourPLCC/plcc-ng/pull/40),
  [`6b653e6`](https://github.com/ourPLCC/plcc-ng/commit/6b653e6f5d1a648b748988d21fd3ee854ad1da62))

- Prepare to unit test
  ([`fe08748`](https://github.com/ourPLCC/plcc-ng/commit/fe08748f4e98afe7d419cb29b105cfc4633f1b1e))

Adopt Technologies:

* PDM - "A modern Python package and dependency manager supporting the latest PEP standards." *
  pyproject.toml - Used by PDM to manage project dependencies and metadata. * pytest - A nice modern
  unit testing framework for python.

Reorganized tests, and removed local-min-max test. They were breaking and are VERY slow. They were
  intended to mimic those that run in CI. But those are passing.

Added bin/test/units.bash to run unit tests. Place unit tests in tests/unit/.

No longer supporting python < 3.9.

---

Related to #119 Closes #131

Thanks to Co-authored-by: Akshar Patel <aksharpatel1233@gmail.com> He performed the initial research
  for pyproject.toml

- Raise minimum Python version to 3.12
  ([`23ba4ce`](https://github.com/ourPLCC/plcc-ng/commit/23ba4cef67c795870e33ea1bed0ca008fd98d726))

- Release and publish ([#21](https://github.com/ourPLCC/plcc-ng/pull/21),
  [`7b09fe1`](https://github.com/ourPLCC/plcc-ng/commit/7b09fe1daf4da75bb40882a3f171d762f107ca6f))

- Update license ([#16](https://github.com/ourPLCC/plcc-ng/pull/16),
  [`e765712`](https://github.com/ourPLCC/plcc-ng/commit/e765712f9b9094d5ddad2f6f473feeefd62280fb))

- **bin**: Add developer scripts for build, install, and test
  ([`fe11f00`](https://github.com/ourPLCC/plcc-ng/commit/fe11f009ebf3d40261e47112e93126010f19ff62))

- **bin**: Add package build script and scope build/ gitignore to root
  ([`b628d22`](https://github.com/ourPLCC/plcc-ng/commit/b628d22997148362ac2f879542c0d655cd2ba470))

- **bin**: Self-install pdm in units.bash if not present
  ([`a74f8f8`](https://github.com/ourPLCC/plcc-ng/commit/a74f8f809497e16a60cee76944f2203ee739d710))

- **devcontainer**: Install pdm on start
  ([`507b12c`](https://github.com/ourPLCC/plcc-ng/commit/507b12c25bd4fab5c5ec31217e7235519d3f10b0))

- **mypy**: Remove dependency
  ([`a602e02`](https://github.com/ourPLCC/plcc-ng/commit/a602e021fa60569349170bb06f970cbae6165eae))

We do not use annotated types or check them.

- **shell**: Move COPY later to improve caching
  ([`b1ed014`](https://github.com/ourPLCC/plcc-ng/commit/b1ed01458137629784880329f6ad5c374bc6d1f3))

Currently any change to any file in the repository invalidates the entire cache. By moving the `COPY
  . /plcc` command to later in the Dockerfile, the cache for the commands above can be reused,
  improving build performance.

- **shell**: Remove build args to enable caching
  ([`538ea8d`](https://github.com/ourPLCC/plcc-ng/commit/538ea8d669b16561a0d4ae19f8a09403622b1a47))

ARG lines in Dockerfile invalidates build caches from that point on. The existing ARG lines were
  used as constants so that version numbers could be specified at the top of the file. But their
  adverse effect on build performance does not outweigh their benefit in design. So this commit
  inlines them.

- **shell/run**: Don't cd to project root
  ([`b42c5d2`](https://github.com/ourPLCC/plcc-ng/commit/b42c5d2b079a36273a820725358d02ca1b057eb1))

shell/run no longer changes to the root of the project before running the shell environment. This
  means the current working directory from which you run shell/run will be mounted into the
  environment rather than the root of the project. This makes it more flexible in manual tests.

### Chores

- Add .worktrees/ to .gitignore
  ([`c6b1ca7`](https://github.com/ourPLCC/plcc-ng/commit/c6b1ca7ced86f3cd651dff49213872f1bb18b8bd))

- Add Claude Code to devcontaner
  ([`f656eaa`](https://github.com/ourPLCC/plcc-ng/commit/f656eaa660209fe0fad25fdc922232fd18c8e74b))

- Bump version to 1.0.1 in VERSION file
  ([`233f85e`](https://github.com/ourPLCC/plcc-ng/commit/233f85e9ad93f2e778281306ddf52d11e67161dc))

- Delete empty src/plcc/lang/ext/plantuml stub
  ([`425e87f`](https://github.com/ourPLCC/plcc-ng/commit/425e87f1c858c334252c38b8c8e753e7b9a7e8f7))

- Move .claude config and memory from plcc
  ([`99bee81`](https://github.com/ourPLCC/plcc-ng/commit/99bee819f959ca5d7cacedfe3b229c0fae1e44ac))

Bringing over Claude Code settings and project memory as development moves to plcc-ng. Also ignores
  settings.local.json.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Remove support for GitPod
  ([`a6233ed`](https://github.com/ourPLCC/plcc-ng/commit/a6233ed2ca1bef67933dbfe972288e4f570ec51b))

- Upgrade bats to 1.11
  ([`10bdc0d`](https://github.com/ourPLCC/plcc-ng/commit/10bdc0d264bfc28f8f4269af5e381eef64713bbd))

- Upgrade dependencies
  ([`4f196cf`](https://github.com/ourPLCC/plcc-ng/commit/4f196cf6289aa429f1968312a5cce323e731b7c8))

alpine: 3.12 -> 3.14

python3: 3.8 -> 3.9

bash: 5.0 -> 5.1

bats: 1.2 -> 1.3

- **bump**: 3.1.1-dev.0
  ([`7c70965`](https://github.com/ourPLCC/plcc-ng/commit/7c70965131ae9467d1622d6956ae4b0eb01dd5a3))

- **ci**: Add languages-pin.txt for reproducible corpus tests
  ([`c8be85a`](https://github.com/ourPLCC/plcc-ng/commit/c8be85aa4c3b1d2f3778341d15a828d73a86f874))

- **ci**: Bump python to 3.14
  ([`4f1fd7a`](https://github.com/ourPLCC/plcc-ng/commit/4f1fd7a86dca0a5b40220a86c2a3c800aa5d077e))

- **ci**: Fix release mechanism
  ([`f0984ff`](https://github.com/ourPLCC/plcc-ng/commit/f0984ff57103b6fe1cac31d693a8f2a459e58016))

- **ci**: Remove `commit: "false"`
  ([`a913b06`](https://github.com/ourPLCC/plcc-ng/commit/a913b064512e7b0eb297f09cc59ba95554669a93))

- **ci**: Use 'pypi' environment for trusted publishing
  ([`d895a78`](https://github.com/ourPLCC/plcc-ng/commit/d895a789e5a0fc7bb09bc0b71593e7952e0207e1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **cicd**: Upgrade semantic-release action
  ([`9cf29d9`](https://github.com/ourPLCC/plcc-ng/commit/9cf29d986fa750fe5a714504e642895ba7aee8c3))

Hoping this fixes the release issue.

- **claude**: Add bash permission allowlist to settings.json
  ([`f8d887d`](https://github.com/ourPLCC/plcc-ng/commit/f8d887d36a5226f004c89d9b0a9971031d49c890))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **claude**: Update permissions allowlist for Phase 1 tooling
  ([`a792f96`](https://github.com/ourPLCC/plcc-ng/commit/a792f96d0d1da8262ff074523356f20261adddc4))

- **install**: Add java install script and auto-install in e2e.bash
  ([`6ba8124`](https://github.com/ourPLCC/plcc-ng/commit/6ba81244440a29ddfd14708a602c17c676211888))

bin/install/java.bash installs default-jdk via apt if javac is not already present, following the
  same idempotent pattern as bats.bash and pdm.bash. e2e.bash calls it when LANGUAGES_REPO_PATH is
  set so the Java corpus tests run in any environment without manual JDK setup.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **packaging**: Rename to plcc-ng, fix license, add PyPI metadata and semantic-release config
  ([`c10aa07`](https://github.com/ourPLCC/plcc-ng/commit/c10aa07e83cce7dfb43cd11a98b6180a7299e37e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **release**: 1.0.0
  ([`d4862c9`](https://github.com/ourPLCC/plcc-ng/commit/d4862c98f61b733c59a105a711219ff241a68cac))

- **release**: 1.0.1
  ([`b7150a3`](https://github.com/ourPLCC/plcc-ng/commit/b7150a3357cfc26270cc3f2327da6e8ea11c313b))

- **release**: 2.0.0
  ([`ec3ab50`](https://github.com/ourPLCC/plcc-ng/commit/ec3ab50813f50b3712cc33f9a631ced52c343349))

- **release**: 2.0.1
  ([`0bea38f`](https://github.com/ourPLCC/plcc-ng/commit/0bea38febcc313d7764d280b45bb9ab595e059ee))

- **release**: 2.0.1-dev.0
  ([`4bfa244`](https://github.com/ourPLCC/plcc-ng/commit/4bfa24438528caee815e5b8721d7c80171d754d4))

- **release**: 2.0.2-dev.0
  ([`116679d`](https://github.com/ourPLCC/plcc-ng/commit/116679d7a85eabeb970390c2b34a69552225916b))

- **release**: 2.1.0
  ([`044b23a`](https://github.com/ourPLCC/plcc-ng/commit/044b23a38839c361178e05c37c457f2f71e2a993))

- **release**: 2.1.1-dev.0
  ([`1172db3`](https://github.com/ourPLCC/plcc-ng/commit/1172db3c246a5213fc543c5da0d93506c438461d))

- **release**: 3.0.0
  ([`df6f981`](https://github.com/ourPLCC/plcc-ng/commit/df6f981c254531eb9caea821cbace7488b45a893))

- **release**: 3.0.1-dev.0
  ([`c58f800`](https://github.com/ourPLCC/plcc-ng/commit/c58f800da0f5bf426dfc5ced72323f69633e4292))

- **release**: 3.1.0
  ([`8967507`](https://github.com/ourPLCC/plcc-ng/commit/89675074a68b322a107001e121675d25730c6f64))

- **shell**: Pin Alpine packages to approximate version numbers
  ([`f8d2bae`](https://github.com/ourPLCC/plcc-ng/commit/f8d2baed26526b26fecb9b0bb9ae94622435ad73))

This commit only applies to the shell that is used to manually test PLCC (in ./shell).

Alpine does not keep old package versions. So if you pin to a specific package version, your build
  will break if Alpine updates to a new version of the package.

To allow package versions to varry, but maintain some level of consistency in builds, we're pinning
  to approximate versions instead. For example, instead of

openjdk=11.0.7-rc0

We now pin to

openjdk~=11.0

This allows the rest of the version number to spin as needed. In theory, allowing patch updates
  should not break our build.

- **spec**: Confirm LL(1) separation with comment
  ([`2c3a894`](https://github.com/ourPLCC/plcc-ng/commit/2c3a894a311988843a32cda29b7363d367eafdfa))

- **test**: Display versions of test dependencies
  ([`98e0454`](https://github.com/ourPLCC/plcc-ng/commit/98e04541d9b79edfa6b5ca34159be374760a1257))

- **versions**: Allow for non-existant commands
  ([`b67b394`](https://github.com/ourPLCC/plcc-ng/commit/b67b3949eb7c63fc4951d3cf8f1106eac111a672))

### Code Style

- Remove trailing whitespace
  ([`0bc5d90`](https://github.com/ourPLCC/plcc-ng/commit/0bc5d905d4741b59d4b2d6e15ed1fc9d0433bff6))

- **bats**: Use python3 consistently and add bats version guards
  ([`bee549e`](https://github.com/ourPLCC/plcc-ng/commit/bee549e0ea8fb3de2499c0d75448c4090b92f3c1))

- **pyproject**: Normalize entry point spacing in [project.scripts]
  ([`c42e766`](https://github.com/ourPLCC/plcc-ng/commit/c42e766612365bb2172ea65a20014d73da455697))

- **Std**: Clean up whitespace
  ([`b03798a`](https://github.com/ourPLCC/plcc-ng/commit/b03798abe5557b7298ef9d59c5f3884e3b9ea527))

- **verbose**: Consolidate imports in verbose_test.py
  ([`eef2cbf`](https://github.com/ourPLCC/plcc-ng/commit/eef2cbfbb795d10dc3aecffd0ddb35ed93d7f9e7))

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>

### Continuous Integration

- Add GitHub Actions workflow for multi-lang branch
  ([`39162ff`](https://github.com/ourPLCC/plcc-ng/commit/39162ffb3978eb06baa6bd01d2cd0ddc728298c3))

- Add release.yml with semantic-release and Trusted Publishing
  ([`5354817`](https://github.com/ourPLCC/plcc-ng/commit/5354817105ff9b0b73ae1c239d54e87494a6426b))

- Avoid duplicate runs by limiting push trigger to main
  ([`3274bd8`](https://github.com/ourPLCC/plcc-ng/commit/3274bd83ac4f5ec219e9e02632b5c2a73ff76c70))

- Checkout tags too
  ([`7dcdab9`](https://github.com/ourPLCC/plcc-ng/commit/7dcdab9df892f76c0ee8eff06e9ee850dccc8205))

- Combine pypi and release
  ([`2ab18e6`](https://github.com/ourPLCC/plcc-ng/commit/2ab18e64287fa812fdf12e32dd7487c2cc97f526))

- Debug pdm
  ([`7a94be3`](https://github.com/ourPLCC/plcc-ng/commit/7a94be392dc810cfd169f5a475a74ecb9dce5b57))

- Exclamation triggers major version bump ([#83](https://github.com/ourPLCC/plcc-ng/pull/83),
  [`7557a96`](https://github.com/ourPLCC/plcc-ng/commit/7557a96f6e9ae897af5ed7761c56f42044d38d79))

Closes #60

- Fetch everything
  ([`dd1752f`](https://github.com/ourPLCC/plcc-ng/commit/dd1752f4f8aebc24b08fcd79956b2f09437104fc))

- Fix release.yaml
  ([`cc40a9c`](https://github.com/ourPLCC/plcc-ng/commit/cc40a9c38ddce697f237f7947a1e57d6672b941c))

- Include languages in functionality test ([#113](https://github.com/ourPLCC/plcc-ng/pull/113),
  [`7976dfc`](https://github.com/ourPLCC/plcc-ng/commit/7976dfca4f43c743fe65707e68f771b4f02206e7))

- Real attempt
  ([`254840f`](https://github.com/ourPLCC/plcc-ng/commit/254840f07d152afbc90e14a8804e3029dd683cb6))

- Remove release/ ([#74](https://github.com/ourPLCC/plcc-ng/pull/74),
  [`3bba3d5`](https://github.com/ourPLCC/plcc-ng/commit/3bba3d5987af43b999ee83159354756a8a009297))

Release is now performed by a GitHub action. The manual release mechanism should no longer be
  necessary.

---

Closes #71

- Replace ci.yml with three-job workflow (unit-integration, corpus, packaging)
  ([`4537397`](https://github.com/ourPLCC/plcc-ng/commit/4537397fa4a7858f4e93bd19570d2d74936b64b1))

- Run CI on all branches and pull requests
  ([`7310f78`](https://github.com/ourPLCC/plcc-ng/commit/7310f78d0b4001e29c1f21eeaf8439d86d44535a))

- Run on pull_request to test merged version
  ([`758b3d7`](https://github.com/ourPLCC/plcc-ng/commit/758b3d7841baead584ee61b249fa8acf312189e3))

According to https://github.com/actions/checkout/issues/15#issuecomment-524093065 if we run on
  pull_requests instead of on push, we'll get the merged version of the repo rather than the pull
  request branch.

- Upgrade to Node.js 24 compatible action versions
  ([`dedac2e`](https://github.com/ourPLCC/plcc-ng/commit/dedac2e7572efd9342ae06148ce98915d010b1f1))

Bump actions/checkout v4→v5 and actions/setup-python v5→v6. Both new versions target Node.js 24,
  eliminating the deprecation warning ahead of the June 2026 forced cutover.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Documentation

- Add CONTRIBUTING.md and CLAUDE.md for developer workflow
  ([`e098105`](https://github.com/ourPLCC/plcc-ng/commit/e0981058af817753bbb0dbf967c15783c340c4ca))

Address Phase 1 retro finding that agents repeatedly wrote ad-hoc scripts instead of using pre-built
  commands in bin/. CONTRIBUTING.md describes bin/ scripts, test tiers, the TDD inner loop, and
  workflow conventions. CLAUDE.md is a short pointer auto-loaded by Claude Code at session start,
  directing readers to CONTRIBUTING.md and forbidding ad-hoc scripts.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- Add initial CONTRIBUTING.md
  ([`f415422`](https://github.com/ourPLCC/plcc-ng/commit/f415422d7d76ab9da27a92ac2a35b98c8184152d))

- Add intro on which contribution process to use
  ([`d239629`](https://github.com/ourPLCC/plcc-ng/commit/d2396294d46e4dfd200ca3fb268139e54d34c8f0))

- Add link to new Discord server
  ([`4a14c22`](https://github.com/ourPLCC/plcc-ng/commit/4a14c22298ca81f15ab3a526841bf7629ab0fda9))

- Add location of install and test install
  ([`f8c710e`](https://github.com/ourPLCC/plcc-ng/commit/f8c710eee53beca36137bba261c19c169d9eec69))

- Add more links to Discord
  ([`aece35c`](https://github.com/ourPLCC/plcc-ng/commit/aece35c0c8629e6d83fc5ec032d8592b5b1e3399))

- Add multi-language architecture and implementation roadmap
  ([`5cf2d3e`](https://github.com/ourPLCC/plcc-ng/commit/5cf2d3e4068a55428adf55ceffa4b0d507c9d9b7))

Moving design documents from plcc to plcc-ng to develop and demonstrate the implementation here
  first before merging upstream.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add pointers to issue tracker and CONTRIBUTING.md
  ([`a6dde8e`](https://github.com/ourPLCC/plcc-ng/commit/a6dde8ece4dbc9c1e3e6df51981c2d414ad9cfdd))

- Add uid:gid to docker run ([#88](https://github.com/ourPLCC/plcc-ng/pull/88),
  [`17d596e`](https://github.com/ourPLCC/plcc-ng/commit/17d596e29af702933d513561acef405d4ee01df7))

Closes #87

- Add updating a pull-request and generalize
  ([`e6db9bb`](https://github.com/ourPLCC/plcc-ng/commit/e6db9bbe7b7fe1875e0a2a0bc7000e26d59dca97))

- Adjust project name
  ([`01d5371`](https://github.com/ourPLCC/plcc-ng/commit/01d53710df6a1d77c39dbe30d19248f96c4334e8))

- Credit co-authors for 41b8e97 [skip-ci]
  ([`b8e2341`](https://github.com/ourPLCC/plcc-ng/commit/b8e2341657c5ff6dfa050104f90ef7f5ddd1677a))

Co-authored-by: James Heliotis <jeh@cs.rit.edu>

Co-authored-by: Timothy Fossum <fossum@halsum.org>

- Fix based on Jim's feedback [skip-ci]
  ([`db394cf`](https://github.com/ourPLCC/plcc-ng/commit/db394cf271b27babbaf4e14ac2c5936ccf68bdd6))

---

Co-authored-by: James Heliotis <jeh@cs.rit.edu>

- Fix link to point to plcc's issue tracker
  ([`c6f32c1`](https://github.com/ourPLCC/plcc-ng/commit/c6f32c1da0eb1ca9b6d7d39a6fe202591b20cd8a))

- Fix typo
  ([`da1da1d`](https://github.com/ourPLCC/plcc-ng/commit/da1da1d9f11ca575bfd6807ab910629fdd828c9b))

- Fix typo
  ([`29d59db`](https://github.com/ourPLCC/plcc-ng/commit/29d59db9b8d0b40d43220ee1bc4161cc2189e88e))

- Fix typo in README.md
  ([`4253b26`](https://github.com/ourPLCC/plcc-ng/commit/4253b260e007ce05468a5912086996968e52d90e))

---

* Closes #127

- Improve pseudo-code of scan algorithm [skip-ci]
  ([`41b8e97`](https://github.com/ourPLCC/plcc-ng/commit/41b8e97fd4632b8b9b4f02dcd7adef7e1ca83895))

- Move CHANGELOG.md to docs
  ([`814d379`](https://github.com/ourPLCC/plcc-ng/commit/814d3797fe90be323c4190b9292f36cabac2cf7f))

- Move common contributing documentation to wiki
  ([`73cdc78`](https://github.com/ourPLCC/plcc-ng/commit/73cdc78ba70c74a481e1e009ff9cdc603d1bdefa))

- Move wiki into repo ([#77](https://github.com/ourPLCC/plcc-ng/pull/77),
  [`dd6883a`](https://github.com/ourPLCC/plcc-ng/commit/dd6883a6fc3b034d613a72ed08a338daeb292b9c))

Closes #73

- Overhaul ([#79](https://github.com/ourPLCC/plcc-ng/pull/79),
  [`3940c1a`](https://github.com/ourPLCC/plcc-ng/commit/3940c1a743043ac4d2f38906779da0f363f8fd21))

The goal is to consolidate and minimize the end-user documentation to make it easier to navigate,
  and faster to get started.

- Reduce the number of Discord links
  ([`a0810b6`](https://github.com/ourPLCC/plcc-ng/commit/a0810b65be3c5d3b90e2e6d391213079d825a135))

- Reorganize designs and plans
  ([`3d54d87`](https://github.com/ourPLCC/plcc-ng/commit/3d54d87f347991e374fdf7643512ef2eae62c95c))

- Simplify
  ([`75cc1c0`](https://github.com/ourPLCC/plcc-ng/commit/75cc1c0a84af37ba462ea1671a4359cd3fc9067d))

- Update add Use.md
  ([`c512a12`](https://github.com/ourPLCC/plcc-ng/commit/c512a12435fe57500f329696661147bb3ff0dce1))

- Update docs ([#18](https://github.com/ourPLCC/plcc-ng/pull/18),
  [`e63517b`](https://github.com/ourPLCC/plcc-ng/commit/e63517b6ccf20dded02fdecd98f3e0d947c8c2da))

- **design**: Add Phase 2 Part 2 model and diagram system design
  ([`e731cb8`](https://github.com/ourPLCC/plcc-ng/commit/e731cb8849a31429d5dc845e2b2808e7910fec48))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Add Phase 2 Part 3 design — Python emitter and interactive REPL
  ([`ce49eed`](https://github.com/ourPLCC/plcc-ng/commit/ce49eedce2d4720a8512a200007aa365be3e95fb))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Add §17.8 pipeline-wide --verbose diagnostics
  ([`29f5a7b`](https://github.com/ourPLCC/plcc-ng/commit/29f5a7b8a73e6bb698405122c2c95e0f929b425c))

Every stage accepts --verbose/-v as a level dial (0–3) and writes human-readable narrative to
  stderr. Walking-skeleton discipline: accept-and-forward is mandatory from day one in every stage;
  content fills in as stages mature. Output standards include stage-name prefix, GNU-style source
  positions, present-tense active voice, and line-atomic writes.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- **design**: Address review findings in phase 2 part 1 ll1 parser design
  ([`f104bcf`](https://github.com/ourPLCC/plcc-ng/commit/f104bcfdca2c9cc8408c23859a88b1e6b0230968))

- Specify algorithm end-of-input handling (synthetic $ sentinel), success condition, and
  stack-empty-with-remaining-tokens error case - Clarify lookahead key is token name field (or "$")
  - Fix span computation: add explicit formula for endColumn (1-indexed inclusive) - Fix
  "conflicting cells omitted or arbitrary" -> cells are omitted - Fix level-0 verbose wording:
  silent regardless of is_ll1 value, not "on success" - Add JSONL payload shapes for all verbose
  events in both plcc-ll1 and plcc-parser-table - Add Python enum note for hyphenated event names
  (predict-lookup, first-set, etc.) - State tree is assembled in memory and written atomically only
  on exit 0 - Make plcc-spec deliverable concrete (code comment confirming separation) - Make
  plcc-parser-list verbose flag acceptance an explicit deliverable - Note tree.schema.json and
  ll1.schema.json as schema file deliverables - Justify plcc-ll1 stdin-only decision explicitly -
  Note arch spec field name discrepancy (first vs first_sets)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Address review findings on skeleton update design
  ([`40b18a3`](https://github.com/ourPLCC/plcc-ng/commit/40b18a3f34a3a34d8302b402ee1474cae41b0b8b))

Fixes from independent review: - F1: Mark --ll1 as required on plcc-parser-table - F2: Document
  dispatcher asymmetry (parser vs lang no-op semantics) - F3/F4: Clarify intermediate artifact
  plumbing for Level 2 commands - F6: Confirm spec.json carries tool→language mapping - F7: Confirm
  plcc-make does not invoke plcc-lang-run - F8: Resolve docopt -v vs count-style -vv ambiguity (use
  --verbose=N) - F9: Draft §17.9 amendment text for plcc-<lang>-run - F10: Note --parser on Level 2
  commands is deferred - F11: Document _cli suffix naming convention - F12: Add ll1.schema.json to
  scope - O7: Note JDK requirement for Java plugin tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- **design**: Amend multi-lang pipeline spec with §17.3–§17.7
  ([`e3a7159`](https://github.com/ourPLCC/plcc-ng/commit/e3a715976f2362b1555786ee42f2a5067f660117))

Phase 2 Part 1 brainstorm amendments to the architectural spec:

- §17.3 plcc-tree is one-shot, not long-running - §17.4 introduce plcc-ll1 primitive; plcc-spec
  stops doing LL(1) - §17.5 generated components are pipeline stages - §17.6 parsers are pluggable
  via PATH-based plcc-parser-<kind> - §17.7 interpreters long-lived; plcc-tokens/plcc-tree per chunk

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- **design**: Append Phase 1 retro to walking skeleton design doc
  ([`95979ef`](https://github.com/ourPLCC/plcc-ng/commit/95979efc91ab65082e3c32d7dbb25935f02b7420))

Captures surprises, architectural review (no amendments needed), what worked, cross-phase gaps
  (developer docs, aggregated coverage), and feed-forward items for the Phase 2 brainstorm. Per
  roadmap §9.4.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- **design**: Apply language plugin command contract to existing specs
  ([`da2eaa8`](https://github.com/ourPLCC/plcc-ng/commit/da2eaa8af5fadb039f6e9997680ec6a134281651))

Updates pipeline spec and implementation plan to reflect the decisions captured in the
  language-plugin-command-contract design doc: retire plcc-emit, introduce plcc-lang-emit/build/list
  dispatchers, rename plugin commands to plcc-<lang>-emit/build, drop the plcc.emitters entry-point
  group, and switch to PATH-based discovery throughout.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Draft Phase 2 Part 1 LL(1) parser design
  ([`2b2c818`](https://github.com/ourPLCC/plcc-ng/commit/2b2c8187814e60c86e66e98884731aba7db87ccc))

DRAFT status — captures brainstorm decisions (A' parse tree schema, unified token/tree schemas,
  error node shape, verbose protocol) but implementation scope needs revisiting after the walking
  skeleton is updated to reflect §17.3–§17.8 amendments.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- **design**: Extend §17.9 to supersede §17.6.2 parser-plugin error bullets
  ([`d9c8c92`](https://github.com/ourPLCC/plcc-ng/commit/d9c8c92aebec80fc3aa0aac48c70ede8b4e0647f))

- **design**: Finalize phase 2 part 1 ll1 parser design
  ([`e086d26`](https://github.com/ourPLCC/plcc-ng/commit/e086d26102691bbb2c9ba887a6d59cc049df5241))

Promotes the draft to APPROVED status, incorporating decisions from the brainstorm session: labeled
  children, source-field positions with endLine/ endColumn on internal nodes, stdin-only plcc-ll1,
  parse table with field-annotated symbols for AST elision, predict_sets as ordered list of predict
  sets per alternative, conflicts array as self-contained diagnostic, start_symbol in ll1.json, and
  expand/shift/complete verbose events at -vv.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Fix spec self-review issues in Phase 2 Part 3 design
  ([`b37c0b2`](https://github.com/ourPLCC/plcc-ng/commit/b37c0b2f2ed3dfa29b20d879940b3d5639563162))

- Add Expr.eval() fragment to arith.plcc fixture (Program._run needed it) - Add auto-generated
  parent class import to class_file.py.jinja template

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Fix §17.3 framing — plcc-tree emits single JSON document
  ([`714e340`](https://github.com/ourPLCC/plcc-ng/commit/714e340708c56bb8d0736eea0b4d742f247e488f))

Under the one-shot posture, the multi-program-per-invocation JSONL framing was dead justification
  carried over from the long-running design. plcc-tree now parses one program per invocation and
  emits a single newline-terminated JSON document, which is also a valid one-line JSONL stream so it
  composes with the §17.7 interpreter without an adapter.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- **design**: Language plugin command contract spec
  ([`dcf11ee`](https://github.com/ourPLCC/plcc-ng/commit/dcf11ee407fc06815432d539b6fc599419bf86cb))

Captures the decision to replace Python callable-based emitter plugins with CLI command-based
  plugins (plcc-<lang>-emit, plcc-<lang>-build), PATH-based discovery, and the plcc-lang-*
  dispatcher commands.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Merge amendments into multi-lang pipeline architecture doc
  ([`dc4dcfa`](https://github.com/ourPLCC/plcc-ng/commit/dc4dcfa7a30bf392a5acd508e0d0bb37f5c224e9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Phase 1 walking skeleton design doc
  ([`f704467`](https://github.com/ourPLCC/plcc-ng/commit/f704467430c4c4961f3e256e47b1f60b479f58ae))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **design**: Retire §8 in-band errors; add §17.9 stderr+exit-code model; simplify Part 1 parse-tree
  schema
  ([`42a075f`](https://github.com/ourPLCC/plcc-ng/commit/42a075fffeafff7d8b6f3990a7b90b7ef3ac2476))

- **design**: Rewrite §17.8 as dual-form verbose diagnostics
  ([`892e1ff`](https://github.com/ourPLCC/plcc-ng/commit/892e1fff2375b566d57438eeb7fcc684671046dd))

--verbose/-v level dial (0-3) controls how much; --verbose-format= text|json controls how. Default
  is text (human-readable narrative). Level 2 orchestrators override children to
  --verbose-format=json and may request higher verbosity than the user asked for (asymmetric
  propagation). Addresses independent review findings: interpreter lifecycle (flags immutable for
  session), Level 2 nesting (out of scope), timestamp scope (intra-stage only), PIPE_BUF caveat, -vv
  flag-counting clarification, and §17.6.3 cross-reference.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- **design**: Skeleton update design for architectural amendments §17.3–§17.8
  ([`59da9a6`](https://github.com/ourPLCC/plcc-ng/commit/59da9a6fad9474126ec10c774c467d4ca07e59ba))

Captures the design for updating the Phase 1 walking skeleton to reflect the architectural
  amendments from the Phase 2 brainstorm. Covers new commands (plcc-ll1, plcc-parser-table,
  plcc-parser-list, plcc-lang-run), Python and Java language plugin stubs, verbose infrastructure
  (plcc.verbose), Level 2 command promotion, and test/fixture updates.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- **plans**: Add phase 2 part 1 implementation plans for ll1 analysis and parser table
  ([`c50b174`](https://github.com/ourPLCC/plcc-ng/commit/c50b174badf6f5479b0f2056d63fcb94388155a7))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Add Phase 2 Part 2 implementation plan
  ([`edf2e67`](https://github.com/ourPLCC/plcc-ng/commit/edf2e675e0641a41a5f82b457d328257187df818))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Add Phase 2 Part 3 implementation plan (python-emit + plcc-rep)
  ([`2694dda`](https://github.com/ourPLCC/plcc-ng/commit/2694ddab962c822ff27ab81fd9dd500a7e70dc4a))

- **plans**: Add Phase 2 Part 4 arbno implementation plan
  ([`f7553f7`](https://github.com/ourPLCC/plcc-ng/commit/f7553f7a5566f67299e013e84cf81b3a99e0e3d9))

- **plans**: Add Phase 3 Java emitter implementation plan
  ([`fcf173d`](https://github.com/ourPLCC/plcc-ng/commit/fcf173d45f59af03344c20297229328a7aa63dc0))

- **plans**: Add Phase 4 packaging and release implementation plan
  ([`c0b0118`](https://github.com/ourPLCC/plcc-ng/commit/c0b011856880f46aab3d33e7433440f390a15b19))

- **plans**: Error handling redesign in three model-tiered parts
  ([`b949c31`](https://github.com/ourPLCC/plcc-ng/commit/b949c316c0c2b15a95b0be27353750fdff7db55c))

Part 1 (Opus) retires §8 in-band errors, adds §17.9 stderr+exit-code model, and simplifies the Phase
  2 Part 1 parse-tree schema. Part 2 (Sonnet) applies the mechanical code changes across Level 0
  stages. Part 3 (Opus) wires pipefail attribution and cascade suppression into the Level 2
  orchestrators.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>

- **plans**: Phase 1 walking skeleton implementation plan
  ([`77d40ca`](https://github.com/ourPLCC/plcc-ng/commit/77d40ca72e397c8bfaf45d5c40386ac7bcfed7d7))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Resolve all review findings before phase 1 execution
  ([`e5f8191`](https://github.com/ourPLCC/plcc-ng/commit/e5f819177cfa56de7bb5bbe92a3e58fa94258b90))

Addresses all 6 blockers and 10 concerns from the independent review
  (docs/reviews/2026-04-13-phase-1-plan-review.md).

B1: fix _extract_fields to use isCapturing/isTerminal flags (not kind); add discovery step to
  confirm actual plcc-spec JSON shape first B2: fix tree_cli_test --spec to pass spec JSON, not a
  grammar file

B3: remove dead `with open(model_json) as model_f:` block in plcc-make

B4: add sed step to update --cov=plccng → --cov=plcc in pyproject.toml

B5: new Task 7a — retire scan_cli.py, json_formatter.py, text_formatter.py

B6: new Task 7b — delete plcc_cli.py and spec_cli.py (decision: remove)

C1: fix trivial grammar in design doc §3 (plantuml → diagram)

C2: fix capitalize() → [:1].upper()+[1:] to preserve camelCase names

C3: add discovery step for spec_loader LexicalRule duplication decision

C4: add Phase 1 comment to tree_cli.py explaining --spec is unused

C5: document one-file-per-class design choice in plantuml emit.py

C6: add try/except ValueError around validate_tool_name in plcc-make

C7: resolved by B6 decision (plcc_cli.py removed in Task 7b)

C8: add explicit test inventory step to Task 4

C9: add --semantics deferral comment in lang-emit and plcc-make

C10: simplify packaging.bash entry-point check to test -x

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plans**: Skeleton update implementation plan (19 tasks, 7 parts)
  ([`6a85c9a`](https://github.com/ourPLCC/plcc-ng/commit/6a85c9a893506e0bad66441da4567672b095a5c3))

- **plans**: Update smoke test to use trivial-plantuml.plcc fixture
  ([`1eabee9`](https://github.com/ourPLCC/plcc-ng/commit/1eabee9d84149603b32a9edfc589d71cc5886189))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **readme**: Fix typo, add install section and 'what this is' note
  ([`e0e1eaf`](https://github.com/ourPLCC/plcc-ng/commit/e0e1eaf1f785a057d2ed12944da2af88a7c60184))

- **reviews**: Phase 1 plan independent review
  ([`a24ac49`](https://github.com/ourPLCC/plcc-ng/commit/a24ac4902d2313f4f07b173dafb9d1a09c80f6bf))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **shell**: Fix bats version number
  ([`894aa32`](https://github.com/ourPLCC/plcc-ng/commit/894aa32ea41e7498b0c5bcf37af8788e1e01561b))

- **specs**: Add Phase 2 Part 4 arbno support design
  ([`dee5c5b`](https://github.com/ourPLCC/plcc-ng/commit/dee5c5b9c005d4e7e083618ebac8d97c2a06dfb7))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add Phase 3 Java emitter design
  ([`d43f286`](https://github.com/ourPLCC/plcc-ng/commit/d43f286c4c9de1b694c3431c15e396d554335787))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **specs**: Add phase 4 packaging and release design
  ([`809401f`](https://github.com/ourPLCC/plcc-ng/commit/809401ffb1afcdcbf383c8d801ef65c870f6e5d8))

Phase 4 design: visualizer polish (location-aware, human-first errors), package rename to plcc-ng,
  license fix to AGPL-3.0-or-later, PR-triggered CI with full test suite (incl. languages corpus
  pinned via tests/fixtures/languages-pin.txt and twine check), and a release workflow built around
  python-semantic-release in tag-only mode plus Trusted Publishing to TestPyPI then PyPI.

Versioning starts at 0.0.0 — plcc-ng is a separate, experimental identity from the original plcc;
  the 9.0.0a* prerelease scheme is abandoned. Release decisions about whether plcc-ng becomes the
  successor to PLCC are deferred to Phase 5 and beyond.

- **specs**: Append Phase 3 retro to phase-3-java-emitter-design
  ([`1fff1f1`](https://github.com/ourPLCC/plcc-ng/commit/1fff1f17b15946082bf8f88ab7606faea7150135))

- **testing**: Add testing documentation
  ([`ca08e75`](https://github.com/ourPLCC/plcc-ng/commit/ca08e75c2b5635d4ce5593aa56ab913e3b27998b))

### Features

- Add %include
  ([`1c74d39`](https://github.com/ourPLCC/plcc-ng/commit/1c74d397cb3033350c125682fe600bd69859e99f))

* Add %include, which is a synonym for #include. * Deprecate #include, use %include instead. *
  Deprecate include, use %include instead.

In a PLCC grammar file, `#`` starts a comment. So `#include` looks like a comment, but it's not. To
  avoid this confusion, we are adding `%include` and plan to remove `#include` in the next release.

---

Related to #99 Related to #115

- Add --version option ([#15](https://github.com/ourPLCC/plcc-ng/pull/15),
  [`3a73a85`](https://github.com/ourPLCC/plcc-ng/commit/3a73a852ccf40b6241c640d55669402a043b5d1b))

Print version number and exit without error.

Related issue: https://github.com/ourPLCC/plcc/issues/10

- Add `plccng spec` command ([#66](https://github.com/ourPLCC/plcc-ng/pull/66),
  [`19afd35`](https://github.com/ourPLCC/plcc-ng/commit/19afd3500a9d462fdb0dfa1b98dc026bdcd5386f))

- Add build_parsing_table
  ([`f4cdc4d`](https://github.com/ourPLCC/plcc-ng/commit/f4cdc4db1ff8ae5d013f3f976e1b8b8197b4cfde))

- Add lexical validator
  ([`7a5ff02`](https://github.com/ourPLCC/plcc-ng/commit/7a5ff021ebda44aa09282ec5e92f0d714a3ba81a))

Validates a given LexicalSpec object and returns an errorList

---

* Closes #13

Co-authored-by: Kyle Almeida <almeidakyle03@gmail.com>

Co-authored-by: Akshar Patel <aksharpatel1233@gmail.com>

- Add LL1Validator
  ([`6f08516`](https://github.com/ourPLCC/plcc-ng/commit/6f08516295f81e53f4417cee2050e539ea35e467))

Add check_ll1 method to verify ll1ness, and add helper Grammar and Wrapper classes.

---

* Closes #18 * Closes #48

- Add parse_semantic_spec
  ([`cad5c53`](https://github.com/ourPLCC/plcc-ng/commit/cad5c534ec0a19ccc9082d9585e8554c748414ca))

Parses a given semantic spec into a SemanticSpec object. Updated a Divider object to include tool
  and language.

---

* Closes #7

Co-authored-by: Michael Banerjee <michaelbanerjee10@gmail.com>

Co-authored-by: Akshar Patel <aksharpatel1233@gmail.com>

Co-authored-by: Kyle Almeida <almeidakyle03@gmail.com>

- Add parseSpec ([#58](https://github.com/ourPLCC/plcc-ng/pull/58),
  [`e862b6a`](https://github.com/ourPLCC/plcc-ng/commit/e862b6a2801a2a5aa1944e30c605eeb655317cf5))

* Add plccng.spec.parseSpec, that returns (spec, errors). * Remove access to
  plccng.spec.parse_from_string; use plccng.spec.parseSpec * Remove access to
  plccng.spec.parse_lexical_from_string; use plccng.spec.parseSpec * Move plccng.spec.lines to
  plccng.lines

- Add parsing table checker
  ([`bc35f9a`](https://github.com/ourPLCC/plcc-ng/commit/bc35f9acf489572f83144823d75aa489bcf4876c))

---

* Closes #36

- Build plccng/scanner/source ([#32](https://github.com/ourPLCC/plcc-ng/pull/32),
  [`8cbea2b`](https://github.com/ourPLCC/plcc-ng/commit/8cbea2bf4880a823bb6481d7b918bbd4a478104a))

- Build src/plcc/scanner/sink.py ([#61](https://github.com/ourPLCC/plcc-ng/pull/61),
  [`b01024c`](https://github.com/ourPLCC/plcc-ng/commit/b01024ccab348597987cc326bdca9f74f6dfe9ed))

Co-authored-by: Stoney Jackson <dr.stoney@gmail.com>

- Initial cli
  ([`46282a7`](https://github.com/ourPLCC/plcc-ng/commit/46282a760c40c8a6aad66f340684cdf409dd7de1))

Co-authored-by: Stoney Jackson <dr.stoney@gmail.com>

- Last merge merged a feature
  ([`b815e10`](https://github.com/ourPLCC/plcc-ng/commit/b815e1084f306cc54c9d6e4fd9db9da468001231))

- Optional colon in RHS of rule to pass name
  ([`0a4cf1c`](https://github.com/ourPLCC/plcc-ng/commit/0a4cf1cb3f92a16edccb229b65f941b67064f7bb))

This version allows for optional ":" in annotated class and field names. I know this may be
  controversial, but I honestly don't think it's a big deal: I always wondered why I made the
  "decision" to use ":' in LHS and not in the RHS -- to do so was NOT a rational decision on my
  part, and I am perfectly happy with making them optional in both situations. This does not break
  class notes or even the languages in the Code directory, so it's not a big deal. I suppose the
  plcc documentation should say something about this...

fix: conflicting dummy constructor generation

ONE '1' % <one> ::= ONE

With the current version of plcc.py, the dummy constructor conflicts with the
  automatically-generated constructor for the One.java class. Removing the dummy constructor fixes
  this.

refactor: consolidate to one defang procedure

While taking care of the dummy constructor, I also re-factored the 'defang[g]' procedures, so there
  is only one general 'defang' procedure. [The term 'defang' refers to removing the angle brackets
  (fangs) in <...> grammar rules. I invented the term, so blame me for the usage.] The 'defangLHS'
  procedure handles LHS items in BNF rules, and the 'defangRHS' procedure handles RHS items: the LHS
  and RHS versions are slightly different. This refactoring makes the python Java class generation
  code a bit tighter, but the Java code that gets generated is exactly the same as before.

---

Co-authored-by: Timothy Fossum <fossum@halsum.org>

Tim wrote the code and the above comments. I'm just the committer.

- Parse lexical spec
  ([`7bfa6b8`](https://github.com/ourPLCC/plcc-ng/commit/7bfa6b81ddecafed33d8bb99a7a278ab62c285ec))

- Parse syntactic spec
  ([`b7b17fd`](https://github.com/ourPLCC/plcc-ng/commit/b7b17fd725eafd49a322bcf2300d94b5464880fe))

Parses a given syntactic spec and tokenizes the input into SyntacticRule objects that contain
  Symbols on the left and right hand sides.

---

* Closes #6

Co-authored-by: Akshar Patel <aksharpatel1233@gmail.com>

- Pp, modal scanner, #include ([#59](https://github.com/ourPLCC/plcc-ng/pull/59),
  [`1c4b82f`](https://github.com/ourPLCC/plcc-ng/commit/1c4b82f68867f3ff2f53f7b204db20b5b44cca19))

In "The PLCC Tool Set" section of the plcc.pithon.net repository, I have uploaded the latest
  versions of plcc.py (in the src directory) and Scan.java and Token.pattern (in the src/Std
  directory). These incorporate the changes we discussed:

1. Dropping the PP preprocessor option in plcc.py 2. Implementing scanner "line mode" toggling using
  '^^...' tokens 3. Implementing #include directives anywhere in the specification text

Tim

---------------------- "line mode" in scanner ----------------------

On a related issue, do you want me to implement the "lineMode" feature as I proposed earlier? That
  is, if a token definition looks like this:

token PCT3$$ '^%%%'

then the scanner will enter line mode whenever it sees the PCT3$$ token on input, and will exit line
  mode when it sees another matching PCT3$$ token. The "$$" at the end of the token name is what I
  used to toggle line mode. There are other ways we could use token names to trigger line mode -- my
  choice of "$$" is only a suggestion.

In line mode, the appearance of <> on the RHS matches an entire LINE of input, and it returns a
  token with the special token name of $LINE (which cannot conflict with user-defined token names)
  whose lexeme contains the entire line of input. This only works when the scanner is in line mode.

Here's an example of a PLCC language specification file whose implementation can process a PLCC
  specification file (but with no semantics)

skip WHITESPACE '\s*' token PCT3$$ '^%%%' # toggles line mode token ANYTHING_ELSE '\S*' % <start>
  ::= <stuff> <stuff>:NoLineMode ::= <ANYTHING_ELSE> <stuff>:LineMode ::= PCT3$$ <lines> PCT3$$
  <lines> **= <> % # no semantics

The RHS element <> behaves as if it were <$LINE>, where $LINE is the special reserved token name for
  a line (which cannot be a user-defined token name). The scanner cannot return a $LINE "token"
  unless it's in line mode, which is toggled as described above.

In the above, once the scanner encounters the line mode toggle token (PCT3$$ in the above), it
  consumes the rest of the line containing the token and starts line mode processing beginning with
  the next input line. It then continues reading the input, line-by-line, until it encounters
  another instance of the same line mode toggle token, whereupon it returns to normal token
  processing.

<IMPORTANT> Making these changes to the PLCC tool set requires modifications to plcc.py,
  Std/Scan.java, and Std/Token.java. These changes do not alter the *behavior* of the Java
  implementation produced by the PLCC tool set using the language examples in the Code repository,
  but of course the resulting Java files Scan.java and Token.java will not look quite the same. All
  of the other generated Java files -- namely, those generated from the BNF grammar specification --
  are unchanged. </IMPORTANT>

Incidentally, the Scan, Parse, and Rep programs don't know anything about 'include' in the files
  they are reading. So if you wanted to run Scan on, say, the V6 language source files using the
  above language definition, you would need to do something like this:

(cd ~/PL/Code/V6 ; cat grammar code envVal prim val) |\ java -cp Java Scan

where the Java directory has the PLCC code generated by the above language. The 'cat ...' command
  will grab all of the code pieces (codpieces?) and present them to the scanner as a single file.
  Just running Scan on the 'grammar' file will not process the named include files, because the
  language described above doesn't know how.

---------- `#include` ----------

Bowing to unrelenting pressure, I have succeeded in implementing an 'include' feature for input
  files to plcc.py. First, so as not to break any existing code, the use of 'include ...' at the end
  (normally) of the semantics section stays exactly the same: file names are simply added to the
  argv array and processed as if they were parameters given on the command line.

My proposed 'include' feature allows for lines of the form

#include filename

just like C/C++. When such a line appears anywhere in the input file (after any command-line
  switches), input lines switch to the file with the given filename, and returns to the previous
  file once the new file contents have been read. These #include directives can be nested -- that
  is, an #include file can itself have an #include part, and everything gets stacked up.

But BEWARE: if a file has an include like this:

#include fff

and if the file 'fff' itself has the same include line

the include mechanism could blow up with a stack overflow. I have made it so that you can't have
  nested includes more than 4 levels deep, which avoids this problem. I can't imagine nesting even
  this much, but I'm open to suggestions.

The tricky part about this is that there might possibly be a situation where code in the semantics
  section between the %%% ... %%% markers has `#include` lines. This could happen, for example, if
  the target language were C/C++ -- an unlikely situation, but oddly possible given the insatiable
  desire of both of you to target any implementation language that is Turing complete. In order to
  side-step this possibility, I have TURNED OFF the processing of #include directives for code
  between %%% ... %%% markers. I think this makes sense, and basically treats this code as being
  entirely language independent (except for lines themselves starting with %%% -- ouch!).

----------------------------- Remove PP option from plcc.py -----------------------------

This option allowed a specified preprocessor command to be ran on the generated code. The
  implementation relied on Python's now deprecated `pipes` library. Unaware of any uses of the PP
  options, we have chosen to simplify plcc.py by removing the PP option and also the deprecated
  dependency.

BREAKING CHANGE:

Removal of the PP option will break code that relies on this option. There are no alternatives to
  this option.

---

Co-authored-by: Timothy Fossum <fossum@halsum.org>

Closes #49 Closes #55 Closes #58

- Print AST in JSON format ([#68](https://github.com/ourPLCC/plcc-ng/pull/68),
  [`559ff22`](https://github.com/ourPLCC/plcc-ng/commit/559ff22bfc91306006f24ec7a48eb10f08ff9e86))

To print an AST for a program in JSON format, do the following.

plccmk --json_ast GRAMMAR_FILE parse --json_ast < PROGRAM_FILE

Adds a new dependency: the Jackson JSON library for java. We distribute jars (in src/lib) from the
  following projects under the Apache 2.0 license:

* https://github.com/FasterXML/jackson-core * https://github.com/FasterXML/jackson-databind *
  https://github.com/FasterXML/jackson-annotations

If manually compiling and running the generated Java code, you'll need to add these jars to your
  classpath.

If you don't use the new --json_ast option, these jars do not need to be in your classpath.

---

Closes #53 - Add option to print parsejava to print ast in json

Co-authored-by: Madison Mason <madison.nm1213@gmail.com>

Co-authored-by: Rarity Van Lone <rarity.vanlone@gmail.com>

Co-authored-by: Stoney Jackson <dr.stoney@gmail.com>

- Replace repeating with standard rules
  ([`4e2d182`](https://github.com/ourPLCC/plcc-ng/commit/4e2d1824d8ae039b314100524bb72d8379fc9169))

- Top-level spec ([#41](https://github.com/ourPLCC/plcc-ng/pull/41),
  [`c35cc58`](https://github.com/ourPLCC/plcc-ng/commit/c35cc58fbf26a01bf99d8ef13a75efb2598ab548))

- parse_from_lines - parse_lexical_from_string - parse_lines_from_string

- Trigger release
  ([`1ce9cd5`](https://github.com/ourPLCC/plcc-ng/commit/1ce9cd58b99f4224b890655b9a9fb37701be8829))

BREAKING CHANGE: This commit is to coerce semantic-release into releasing a major release.

- Updates for next release
  ([`1d29683`](https://github.com/ourPLCC/plcc-ng/commit/1d29683f0d1bae4e2d490db35e6998a0a4015f7b))

## Breaking changes:

* The standalone parser is now called 'Parse' instead of 'Parser'. If the parse is successful, it
  prints 'OK'.

* Both 'Rep' and 'Parse' process command-line arguments and standard input in exactly the same way,
  using a support program called 'ProcessFiles'. This reduces code duplication and makes for a
  common user interface.

* Printing PLCCExceptions now default to printing a leading "%%% " instead of ">>> ". This makes
  exception output stand out better.

## New and improved features:

* Each PLCC-generated parser class file has a "<Class>:init" hook as the first line of its
  constructor. This can be used to incorporate Java code into the Class constructor that can carry
  out simple semantics that would otherwise not be possible using the parser alone.

For example, the Formals class in Language V4 parses the list of formal parameter variables to get a
  'varList' of Tokens. In the 'grammar' file (actually, in the 'code' file that the 'grammar' file
  includes), the lines

``` Formals:init %%% Env.checkDuplicates(varList, " in proc formals") %%% ```

would include this call to 'checkDuplicates' as the first line of the Formals constructor. This
  method will throw an exception if the 'varList' of Tokens has any duplicate identifiers. Including
  this method in the Formals constructor means that the semantic action of checking for duplicate
  variable names will be done during parsing instead of at runtime. This hook is just a comment
  unless defined otherwise in the 'grammar' file.

* Each PLCC-generated parser class file has a "<Class>:top" hook at the top of the file. This can be
  used to incorporate documentation regarding the file, such as copyright or whatever. This hook is
  just a comment unless defined otherwise in the 'grammar' file. I haven't used this, but someone
  might find it convenient.

## Other changes, including bug fixes:

* Instead of printing the 'toString()' value of the root of the parse tree to "evaluate" it using
  the 'Rep' loop, I have the default behavior call a '$run()' method on the root of the parse tree.
  Whatever this method does is the 'behavior' of the program. It defaults to printing the
  'toString()' value as before. The '$run()' method is void, so whatever visible behavior a program
  should have can be undertaken in this method.

---

Co-authored-by: Timothy Fossum <fossum@halsum.org>

Co-authored-by: Stoney Jackson <dr.stoney@gmail.com>

- Upgrade docker dependencies ([#48](https://github.com/ourPLCC/plcc-ng/pull/48),
  [`3d6bb79`](https://github.com/ourPLCC/plcc-ng/commit/3d6bb79203643d35b1959740eb737d4589fb9880))

## Features

* Upgrade Java to 17 in Docker, allowing language authors to use its features when implementing
  languages.

## Fixes

* Test for `plcc --version` now accepts leading `v` in version numbers.

- Validate each repetition rule separator is a terminal
  ([#64](https://github.com/ourPLCC/plcc-ng/pull/64),
  [`8c0718c`](https://github.com/ourPLCC/plcc-ng/commit/8c0718c3713618baac408027588fa8bda00020cc))

- Validate every RHS non-terminal must appear on the LHS of at least one rule
  ([#84](https://github.com/ourPLCC/plcc-ng/pull/84),
  [`cd4832c`](https://github.com/ourPLCC/plcc-ng/commit/cd4832c639f5f8d7911ec8c68bee7ec52896b93c))

closes #51

---------

Co-authored-by: Stoney Jackson <dr.stoney@gmail.com>

- Validate lhs of syntactic section
  ([`05f17a0`](https://github.com/ourPLCC/plcc-ng/commit/05f17a0685783a2711b638a7c2fddca3b754ba12))

Validates the LHS of a given Syntactic Spec, as well as laying foundation for RHS to be validated.
  ---

* Closes #22

- Validate SemanticSpec CodeFragments have attributes defined
  ([#59](https://github.com/ourPLCC/plcc-ng/pull/59),
  [`43ece85`](https://github.com/ourPLCC/plcc-ng/commit/43ece852f43a213988bfb21cefbb65f37438e2f8))

Co-authored-by: Stoney Jackson <dr.stoney@gmail.com>

- Validate that terminals in syntactic spec are defined in lexical spec
  ([#57](https://github.com/ourPLCC/plcc-ng/pull/57),
  [`fed798d`](https://github.com/ourPLCC/plcc-ng/commit/fed798ddb8d74a8994dff2e0f253b160b754aa9e))

Check that terminals in syntactic spec are defined as tokens in the lexical spec.

---

Co-authored-by: Stoney Jackson <dr.stoney@gmail.com>

Closes #52

- **cmd**: Add plcc-scan, plcc-parse, plcc-rep skeleton entry points
  ([`5d73fbc`](https://github.com/ourPLCC/plcc-ng/commit/5d73fbcda9cda083b8f946b084eee5fe5f5de57a))

- **diagram**: Add plcc-diagram dispatcher
  ([`db45a78`](https://github.com/ourPLCC/plcc-ng/commit/db45a7891c3c003e790b9b1882e492baaf81dd70))

- **diagram**: Add plcc-diagram-list command
  ([`86d8755`](https://github.com/ourPLCC/plcc-ng/commit/86d87551fad47db2cd232760f1131046f8ce8fd5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **diagram**: Add plcc-plantuml-diagram command
  ([`156250a`](https://github.com/ourPLCC/plcc-ng/commit/156250a0cd980788140b50471bf7e84d9f65952e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **fixtures**: Add entry_point and Program/Expr eval fragments to arith.plcc
  ([`24a31a1`](https://github.com/ourPLCC/plcc-ng/commit/24a31a1d767ed41989409bd1d06d93b80e60a612))

- **fixtures**: Update trivial-python.plcc to capture NUM and declare _run
  ([`8406388`](https://github.com/ourPLCC/plcc-ng/commit/84063881737e14ca9457d44530cf0641b3d333cd))

- **java-build**: Add org.json classpath and runtime/*.java compilation
  ([`49b9ac4`](https://github.com/ourPLCC/plcc-ng/commit/49b9ac4c776c5e0e0a469aeea8631caf98fafa3a))

- **java-emit**: Add class_file.java.jinja template
  ([`cc488fc`](https://github.com/ourPLCC/plcc-ng/commit/cc488fc8782ee319f991430b45c22000ff45125c))

- **java-emit**: Add Main.java.jinja template
  ([`7a2c573`](https://github.com/ourPLCC/plcc-ng/commit/7a2c573924b265ec721c3d54ff45a747ff1b55ee))

- **java-emit**: Replace stub with full Jinja2-based emitter
  ([`2f2b059`](https://github.com/ourPLCC/plcc-ng/commit/2f2b059bbe3bd4ded87657815b466e6892385ca3))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **java-run**: Add org.json classpath
  ([`729b231`](https://github.com/ourPLCC/plcc-ng/commit/729b23127375e149f6b3cc76b2d8d0583e4476a4))

- **java-runtime**: Add bundled org.json-20250107.jar
  ([`f9b9087`](https://github.com/ourPLCC/plcc-ng/commit/f9b90875e37f83613ed7c9153a5ce1a99bdd7906))

- **java-runtime**: Add Deserializer class
  ([`bbaaaf1`](https://github.com/ourPLCC/plcc-ng/commit/bbaaaf1ab3d905af91f01fe24d7dcf48c77eacc7))

- **java-runtime**: Add Node and Token base classes
  ([`21144bd`](https://github.com/ourPLCC/plcc-ng/commit/21144bdf4f183bbf8a19330e3e0675a064cbd2f7))

- **java-runtime**: Add Registry class
  ([`9638231`](https://github.com/ourPLCC/plcc-ng/commit/9638231a50e8314923560e161c63cbed31a05ac9))

- **lang**: Add Java language plugin stubs (emit + build + run)
  ([`aba4cc8`](https://github.com/ourPLCC/plcc-ng/commit/aba4cc892a30f59cc433bcafff8383c18ff5bb96))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **lang**: Add plcc-lang-build dispatcher
  ([`5371141`](https://github.com/ourPLCC/plcc-ng/commit/53711416bb1e585d7aba57e593764b7c4057da86))

- **lang**: Add plcc-lang-emit dispatcher
  ([`4fa082a`](https://github.com/ourPLCC/plcc-ng/commit/4fa082aebf8e57fd94d5ffdb003659b67a7aadac))

- **lang**: Add plcc-lang-list PATH scanner
  ([`6a8f76f`](https://github.com/ourPLCC/plcc-ng/commit/6a8f76fcb6dfd18ed13abaa23b2ee6c5ab41992d))

- **lang**: Add plcc-lang-run dispatcher (no-op for missing runners)
  ([`47c1bd1`](https://github.com/ourPLCC/plcc-ng/commit/47c1bd1c06e871b9f31077be5a1462c1abf93b57))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **lang**: Add Python language plugin stubs (emit + run)
  ([`1047b4d`](https://github.com/ourPLCC/plcc-ng/commit/1047b4d6ba096ab929609c7fadec46206021aa25))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **ll1**: Add ll1_result_builder — compute ll1.json dict from Grammar
  ([`c9bc2cf`](https://github.com/ourPLCC/plcc-ng/commit/c9bc2cf20fbba8ff34966a885313277d11baf0e6))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **ll1**: Add plcc-ll1 stub with empty LL(1) analysis output
  ([`d51c9b0`](https://github.com/ourPLCC/plcc-ng/commit/d51c9b0ef1f4759f4d6d74cfe483cc1cadadf3d1))

- **ll1**: Add spec_json_decoder — build Grammar from spec JSON
  ([`2d5a25a`](https://github.com/ourPLCC/plcc-ng/commit/2d5a25a194080f0708d1c08905caeedba2d09f32))

- **ll1**: Add start_symbol to ll1.schema.json and tighten types
  ([`739e03f`](https://github.com/ourPLCC/plcc-ng/commit/739e03f8a931360f53fbe1b9f359906843b79ab0))

- **ll1**: Decode() expands arbno rules, returns 3-tuple with arbno_rules
  ([`fe1a54b`](https://github.com/ourPLCC/plcc-ng/commit/fe1a54bc9673fd2d9672f62311aaf334e4002f9d))

- **ll1**: Emit arbno section in ll1.json, filter internal expansion nts
  ([`3852bef`](https://github.com/ourPLCC/plcc-ng/commit/3852bef318c5182623025da3e1b8c592977ef460))

build_ll1_result gains an arbno_rules parameter that filters arbno nonterminals and their
  continuation nts from first/follow/predict/parse_table/conflicts and emits them under a new
  "arbno" key with computed lookahead sets.

- **ll1**: Emit is_ll1 field; keep exit 0 on non-LL(1) per §17.9 (stub)
  ([`ae71cc1`](https://github.com/ourPLCC/plcc-ng/commit/ae71cc1a7f765dd60859670b2e7a0fb417171d17))

- **ll1**: Implement plcc-ll1 with real LL(1) analysis; stdin only
  ([`9094792`](https://github.com/ourPLCC/plcc-ng/commit/9094792dc611e5f36501e3708f2055fd75588d2b))

Wire spec_json_decoder and ll1_result_builder into the plcc-ll1 CLI, switching from file-path
  argument to stdin-only interface; update all callers (make, parse, rep) and bats test suites
  accordingly.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **make**: Abort on is_ll1:false with human-readable conflict summary per §17.9
  ([`952cc81`](https://github.com/ourPLCC/plcc-ng/commit/952cc8121953fc0add03b9a0f843c7b927049a0b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **make**: Add plcc-ll1 step and Level 2 verbose propagation
  ([`1a80e23`](https://github.com/ourPLCC/plcc-ng/commit/1a80e231f4311068b999a1beb98c9a3e8e1b2d3e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **make**: Add plcc-make orchestrator
  ([`23a013a`](https://github.com/ourPLCC/plcc-ng/commit/23a013a93a043a38f1f34e504c7f2209b4e00638))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **model**: Add plcc-model initial implementation for trivial grammar
  ([`75de9c8`](https://github.com/ourPLCC/plcc-ng/commit/75de9c8c7cf55fc2343ea90e65a34059072d2505))

Implements Task 10: plcc-model CLI that reads spec JSON and outputs a language-neutral code model
  JSON with classes, fields, and semantic sections.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **model**: Detect arbno rules, emit is_list fields with List-suffix names
  ([`e7b2780`](https://github.com/ourPLCC/plcc-ng/commit/e7b2780dd600346eb9e5f95d1783db398b37e6e9))

- **model**: Implement class inheritance derivation in build_model
  ([`56dd709`](https://github.com/ourPLCC/plcc-ng/commit/56dd709721c2966cf624d194b192d178b7f55c4e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **model**: Retire plcc-plantuml-emit language plugin
  ([`6f55a39`](https://github.com/ourPLCC/plcc-ng/commit/6f55a39231eb2e186b428bad2af8ff7e3b2bf8a9))

Remove emit.py, its test, the bats command test, and plantuml fixtures. Update all tests that
  referenced PlantUML targets or plantuml_only.plcc to use Python/trivial-python.plcc equivalents
  instead.

- **parse**: Add location-aware tree output and compiler-style error format
  ([`50b4d48`](https://github.com/ourPLCC/plcc-ng/commit/50b4d48d93d360a521a198f43639ec6237ee85b1))

- **parse**: Promote plcc-parse to connected skeleton with Level 2 verbose
  ([`a70c713`](https://github.com/ourPLCC/plcc-ng/commit/a70c713ce759c91015405d9046600dde3d27dd6c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parse**: Use reap_pipeline for upstream-first attribution + cascade suppression per §17.9
  ([`b263433`](https://github.com/ourPLCC/plcc-ng/commit/b2634331a191eaa04a69ef4822f44646ebe262cf))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add plcc-parser-list (PATH scan for parser plugins)
  ([`ec3f119`](https://github.com/ourPLCC/plcc-ng/commit/ec3f11906c765661d9668d6a7e6778039a0317b2))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add plcc-parser-table stub (relocated pass-through logic)
  ([`bf2255f`](https://github.com/ourPLCC/plcc-ng/commit/bf2255f7504d3a601caa7e93df9dc2cb507c8166))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add predictive_parser — iterative LL(1) table-driven parser
  ([`907d1cd`](https://github.com/ourPLCC/plcc-ng/commit/907d1cd22557adb16a755aa2e872d944bcb727b8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add verbose support to plcc-parser-list
  ([`ee22496`](https://github.com/ourPLCC/plcc-ng/commit/ee22496986eb778a8e5a6f7b5cebc31753b5989f))

- **parser**: Implement plcc-parser-table — real LL(1) predictive parser
  ([`700d825`](https://github.com/ourPLCC/plcc-ng/commit/700d82592d69175c250305511c64e106501491cc))

Wire predictive_parser.parse() into table_cli.main; add unit tests covering valid input, tree
  structure, source spans, capturing fields, non-LL(1) grammar rejection, syntax error exit codes,
  and stdout cleanliness on error.

- **parser**: Rewrite predictive_parser as recursive descent with arbno loop support
  ([`9641871`](https://github.com/ourPLCC/plcc-ng/commit/96418712d756e2fc36460523d4eb2b9818f18a52))

Replaces the stack-based implementation with a recursive descent parser that dispatches to
  _parse_regular or _parse_arbno, enabling iteration over arbno (repeating) grammar rules with
  optional separators.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Update tree.schema.json for [field,node] children and source span
  ([`022ac09`](https://github.com/ourPLCC/plcc-ng/commit/022ac09a6c314873c4325dee5d0f2f910b76b24a))

- **plantuml**: Add plcc-plantuml-emit minimal plugin
  ([`ddb73ed`](https://github.com/ourPLCC/plcc-ng/commit/ddb73edba5050407adadbe5ea68bbe647e9b5a0a))

- **plcc-model**: Add entry_point pass-through and rule_name to class dicts
  ([`b8d61cb`](https://github.com/ourPLCC/plcc-ng/commit/b8d61cbf4baed2d10cc4f129560a73a4d7fa54c8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plcc-python-emit**: Full Jinja2-based code generation, one file per class
  ([`7e1f737`](https://github.com/ourPLCC/plcc-ng/commit/7e1f7376611fb53037e6804621b9ee49dd0437b9))

Replace stub emit with full implementation: reads model JSON, renders class_file.py.jinja per class,
  handles file-kind fragments verbatim, renders main.py.jinja with entry_point, and copies runtime/
  directory. Deletes the old runtime/main.py stub that was incorrectly being used.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plcc-rep**: Rewrite as interactive REPL using pre-built build/ artifacts
  ([`4857e8b`](https://github.com/ourPLCC/plcc-ng/commit/4857e8b6b6cc4a8613738f8a64e8d6505fa6a8a4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **plcc-spec**: Capture optional entry_point in semantic section header
  ([`6cfb106`](https://github.com/ourPLCC/plcc-ng/commit/6cfb106047342d4cc312ec54cf0726a104f1163e))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **rep**: Promote plcc-rep to connected skeleton with --tool and Level 2 verbose
  ([`9155be5`](https://github.com/ourPLCC/plcc-ng/commit/9155be5e5562b6d095dfce554080a80b21e2c80b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **runtime**: Add Node/Token base classes and jinja2 dependency
  ([`2c1a4a3`](https://github.com/ourPLCC/plcc-ng/commit/2c1a4a3cbddbb6d1c4be8ba965500b555cd9d19f))

- **runtime**: Add recursive parse-tree deserializer
  ([`a765617`](https://github.com/ourPLCC/plcc-ng/commit/a76561719399e8cfecca99c5f68105dc8b08f1e8))

Implements deserialize() function that reconstructs the object graph from plcc-tree JSON output.
  Tokens become Token(kind, lexeme) instances, and nonterminals are constructed via Registry lookup
  with recursive deserialization of children.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **runtime**: Add Registry with field-based disambiguation
  ([`fc42fe3`](https://github.com/ourPLCC/plcc-ng/commit/fc42fe3478e0596e3391760dc7c1a6e10b2228ce))

Implement Registry class for field-based class lookup. The Registry indexes classes by rule name and
  frozenset of field names, enabling disambiguation of parse-tree classes that share the same rule
  name but differ by fields.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **runtime**: Deserialize list values for arbno fields
  ([`9b87482`](https://github.com/ourPLCC/plcc-ng/commit/9b87482492a94a3c4b2a88420235c61b68b3e834))

- **scan**: Add --skip option
  ([`3bdb32c`](https://github.com/ourPLCC/plcc-ng/commit/3bdb32c7133464a7991b3121b9457f05e23bba72))

- **scan**: Add default plain text formatter
  ([`cfca135`](https://github.com/ourPLCC/plcc-ng/commit/cfca135d09f017ecfde96fe6b2f6c5c1b4bb57be))

- **scan**: Add location-aware output and compiler-style error format
  ([`fb5bf40`](https://github.com/ourPLCC/plcc-ng/commit/fb5bf40bf7d4ea3314751c848cbd8981909c8a4f))

Tokens now print with {line}:{col} prefix; lex errors in source are treated as non-fatal (exit 0),
  reserving non-zero exit for grammar failures.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **scan**: Promote plcc-scan to connected skeleton with Level 2 verbose
  ([`933d736`](https://github.com/ourPLCC/plcc-ng/commit/933d7364662057740f22653517cb701dbbf930fe))

Rewrote plcc-scan to orchestrate plcc-spec and plcc-tokens, printing tokens in human-readable
  format. Removed the old stub test and added a BATS test suite for plcc-scan. Deleted
  plcc-skeletons.bats.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **Scan.java): fix(plcc.py): refactor(plcc.py**: (#23)
  ([`2013bf2`](https://github.com/ourPLCC/plcc-ng/commit/2013bf2c68aa36602dbe9727453b743eaa299dff))

SJ: This is effectively three commits in one. I placed feat(Scan.java): first in the subject line as
  its change to the version number would mask the others.

fix(plcc.py): prevent capture of user-defined non-terminals

I changed the format of automatically generated nonterminal names for repeating rules for LL(1)
  checking. Originally, for a nonterminal name like 'nt', the automatically generated nonterminal
  name was 'nt_aux_' and, for ones with a separator, the separator nonterminal name was 'nt_sep_'.
  Since it is possible (though remotely so) for a user to have a grammar rule with a nonterminal
  name of these forms, I changed the separator nonterminal name to nt+'#', which cannot possibly be
  mistaken for a user-generated name.

refactor(plcc.py): reduce number of rules generated

I also simplified the generated rules for a repeating rule without a separator with two rules
  instead of three, and for ones with a separator, with four rules instead of five. The generated
  parser code remains exactly the same. The only difference, internal only to plcc.py, is how the
  repeating rules are converted to right-recursive non-repeating rules for the purposes of checking
  for LL(1).

feat(Scan.java): improve error messages

I modified Scan.java so that error tokens -- ones that do not match any token specification -- have
  a string representation of the form "!ERROR(...)' where '...' is the offending character instead
  of just $ERROR.

Except for better error reporting for "bad" tokens, these changes do not affect any of the generated
  code for a language.

Co-authored-by: fosler <fossum@halsum.org>

Co-authored-by: jeh <jeh@cs.rit.edu>

- **schema**: Update model schema for abstract classes and semantic fragments
  ([`244fab9`](https://github.com/ourPLCC/plcc-ng/commit/244fab914111c11b05f927bbbe9e0a2bced1ccb1))

- **schemas**: Add minimum viable JSON schemas for all Level 0 contracts
  ([`51e8113`](https://github.com/ourPLCC/plcc-ng/commit/51e8113c7232611513c19a6f6470bb8be9e6aad1))

- **spec**: Add plcc-spec standalone entry point
  ([`7e0a1cc`](https://github.com/ourPLCC/plcc-ng/commit/7e0a1ccee30b72ef520713ffaf5f6201148fda9d))

Adds the plcc-spec command that parses and outputs a PLCC grammar file as JSON, wires it as an entry
  point in pyproject.toml, and fixes the trivial.plcc fixture to use valid parser format (% dividers
  instead of %% section headers).

- **spec**: Make json output optional
  ([`ed0b753`](https://github.com/ourPLCC/plcc-ng/commit/ed0b753e898f105aa67a935329f3ba84f029ad22))

- **spec.schema**: Add entry_point field to semantics items
  ([`d79c9bb`](https://github.com/ourPLCC/plcc-ng/commit/d79c9bbd35e6bf237a3d889ed5abb2d11ba1dc54))

- **templates**: Add class_file.py.jinja and main.py.jinja
  ([`003d985`](https://github.com/ourPLCC/plcc-ng/commit/003d98562dc7f475963452ece9338ac78bd03f25))

- **tokens**: Add plcc-tokens standalone entry point with JSONL output
  ([`8c642da`](https://github.com/ourPLCC/plcc-ng/commit/8c642da9ae9a6a7bd8fd43b9935057b812fd415a))

Implements plcc-tokens CLI that reads a spec JSON file and tokenizes stdin, emitting token records
  as JSONL with lex errors in-band.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tokens**: Route lex errors to stderr + exit nonzero per §17.9; drop in-band error schema
  ([`1dc681a`](https://github.com/ourPLCC/plcc-ng/commit/1dc681a63c41a0976f460d628660459ac42d21fe))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **tree**: Add plcc-tree minimal pass-through for trivial grammar
  ([`ad0db91`](https://github.com/ourPLCC/plcc-ng/commit/ad0db910b907bac2dabe36b23e1453f9e184d28c))

- **verbose**: Add --verbose/--verbose-format to all existing Level 0 commands
  ([`ef282f1`](https://github.com/ourPLCC/plcc-ng/commit/ef282f11599ec6238c1300137c603ed25b321c6a))

- **verbose**: Add reap_pipeline for upstream-first attribution + cascade suppression per §17.9
  ([`76a23bc`](https://github.com/ourPLCC/plcc-ng/commit/76a23bc666b779f6476bb3e32329b0864f7ea8e5))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **verbose**: Add shared VerboseContext infrastructure
  ([`e5666fc`](https://github.com/ourPLCC/plcc-ng/commit/e5666fcfaa8b6befc1a233f3505af1bcd650e055))

- **verbose**: Add VerboseContext.emit_error for stderr + exit-code error path per §17.9
  ([`241e186`](https://github.com/ourPLCC/plcc-ng/commit/241e1865eca405ce5aa14bdc06890932b3e309e1))

- **verbose**: Render error events with GNU-style position per §17.9
  ([`a7e82d7`](https://github.com/ourPLCC/plcc-ng/commit/a7e82d7719b1b2dc362dd2914b8c502a92258dc8))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Performance Improvements

- **shell**: Reduce shell size
  ([`b31688f`](https://github.com/ourPLCC/plcc-ng/commit/b31688f0af3ecd9c63bc72588cec93a526bba2b3))

We were installing the the openjdk11 Alpine packcage. But this includes stuff like demos. By
  focusing this to openjdk11-jdk, we safe a few hundred MB.

### Refactoring

- Add gitpod support for development ([#54](https://github.com/ourPLCC/plcc-ng/pull/54),
  [`7edbca4`](https://github.com/ourPLCC/plcc-ng/commit/7edbca486c30db26a1b1e3bda2260040a06a23ea))

- Add plumbing for validators
  ([`5434579`](https://github.com/ourPLCC/plcc-ng/commit/54345792f791216899f8c0744fea121347b9be14))

- Add PR template [no ci] ([#46](https://github.com/ourPLCC/plcc-ng/pull/46),
  [`ebd2f70`](https://github.com/ourPLCC/plcc-ng/commit/ebd2f7073e18d99a5a8abbfd967b88906d4885c1))

- Adjust gitpod stuff ([#56](https://github.com/ourPLCC/plcc-ng/pull/56),
  [`35ce7c5`](https://github.com/ourPLCC/plcc-ng/commit/35ce7c586a6049a6c4dc24d5aab09126fb850333))

- Check defined terminals in repeating rules ([#65](https://github.com/ourPLCC/plcc-ng/pull/65),
  [`8b3a3f3`](https://github.com/ourPLCC/plcc-ng/commit/8b3a3f3161f4969f56243466a3a5215159733235))

Closes #66

- Clean addAbstractStub
  ([`efb4d94`](https://github.com/ourPLCC/plcc-ng/commit/efb4d943f93ea59df620892c15293d5598a50013))

- Clean addAbstractStub
  ([`b08263c`](https://github.com/ourPLCC/plcc-ng/commit/b08263c244036bb1a765d7d34fdb9fa93b0a032f))

- Clean addStub
  ([`2b36c51`](https://github.com/ourPLCC/plcc-ng/commit/2b36c518bddda2a3f798ee8fc849d59970fe08cb))

- Clean build_first_sets and build_follow_sets
  ([`bb607e8`](https://github.com/ourPLCC/plcc-ng/commit/bb607e8c50753639a71d3dc8db9f0fc61eb951fd))

- Clean load_rough_spec
  ([`b13394e`](https://github.com/ourPLCC/plcc-ng/commit/b13394e60da174ff212c050a85c0500a9aa0817a))

- Cleanup params to sem()
  ([`dc3715b`](https://github.com/ourPLCC/plcc-ng/commit/dc3715bd71344d48b402a6cbbe68ce7674e41cba))

- Clear out includes in __init__.py ([#35](https://github.com/ourPLCC/plcc-ng/pull/35),
  [`2a0ca4b`](https://github.com/ourPLCC/plcc-ng/commit/2a0ca4bd42e74ae91b4ebfbe839e17ef4bf41bb3))

I could not detect a clear pattern or practice of imports in __init__.py, and they do not look well
  maintained. So I've decided to delete all imports in __init__.py

This may lead to some ugly imports. I suggest these should be a "smell" that indicate that a
  refactor may be warranted.

- Consolidate shared data structures ([#78](https://github.com/ourPLCC/plcc-ng/pull/78),
  [`6acc71c`](https://github.com/ourPLCC/plcc-ng/commit/6acc71c58efba0cfa452374e57f05531ecaaecbc))

We have many functions that operate on common data structures. The definition of these data
  structures are next to the functions that create them. For example, the Line structure is next to
  the function that parses a line and creates an instance of Line.

The challenge is that when you need to reference the implementation of a structure, you have to find
  where it first created in the system. It would be better if there was a single place to look for
  shared structures.

This commit creates a structs.py and errors.y in plcc.load_spec, and moves all data structures and
  errors into them. This changes the imports of MANY files.

There will likely need to be a couple of tuneups after this as we learn more about the design.

- Convert plcc.py to python package plcc
  ([`231d139`](https://github.com/ourPLCC/plcc-ng/commit/231d139277919eb042e6b9115d239a3168233496))

BREAKING CHANGE:

plcc is now a Python package, and plcc.py has been removed. So plcc.py can no longer be called
  directly like this

python3 path/to/plcc.py grammar

Instead, use plcc like this

plcc grammar

---

This commit restructures the PLCC codebase into that of a conventional Python project. This should
  make it easier to redesign the internal structure of PLCC, making it easier to maintain and add
  new functionality. It should also help us prepare to distribute PLCC through PyPI, making it
  easier to install. Here is a summary of changes.

- Convert plcc.py into python package plcc - Remove environment variable LIBPLCC - Move src/Std/
  under src/plcc (the PLCC Python package) - Move lib/jackson under src/plcc (the PLCC Python
  package) - Pull common functionality of scripts into common.bash

Related Issues

- Related to #119 - Closes #121 - Closes #120

- Convert type to isToken in LexRule
  ([`f2725c6`](https://github.com/ourPLCC/plcc-ng/commit/f2725c6ae82cdce4e09f1648f67ff0eba4adf17b))

- Delete src/bin ([#17](https://github.com/ourPLCC/plcc-ng/pull/17),
  [`90b6d58`](https://github.com/ourPLCC/plcc-ng/commit/90b6d58b5109e34ea8066c07cab9b8c58d07fa5a))

- Enable Python when grammar has 4 sections
  ([`be3aa2e`](https://github.com/ourPLCC/plcc-ng/commit/be3aa2e764a8f68a527682736e6c9ef688af34fd))

This is in anticipation of a new hybrid Java/Python mode in which the parser runs in Java and the
  semantics rep-loop runs in Python.

In this commit, when an optional 4th section is detected, plcc.py generates ParseJsonAst.json. Thus
  allowing the parser to to generate JSON ASTs when the `--json_ast` flag is passed. It also
  generates experimental Python files.

---

Closes #95

Co-authored-by: Reed Everis <reednorrish@gmail.com>

Co-authored-by: Akshar Patel <aksharpatel1233@gmail.com>

Co-authored-by: Stoney Jackson <dr.stoney@gmail.com>

- Extract until you drop
  ([`987e9c8`](https://github.com/ourPLCC/plcc-ng/commit/987e9c8ee292c42cbd38df22da6d54ee3cb70955))

- Fix symbol-hierarchy ([#82](https://github.com/ourPLCC/plcc-ng/pull/82),
  [`6e2e1e9`](https://github.com/ourPLCC/plcc-ng/commit/6e2e1e934f1a955c6290c848b51b0dc19f090a2d))

This hierarchy better models reality.

Closes #77

- Generalize visitor pattern
  ([`eb2f574`](https://github.com/ourPLCC/plcc-ng/commit/eb2f574cd544393372af55affc969d901d2ef99d))

- Improve installing and related docs
  ([`c60a82f`](https://github.com/ourPLCC/plcc-ng/commit/c60a82f22f1635bd08c334bff9bce3b7c6605e64))

* Add docs for installing and using PLCC in GitPod * Consolidate docs for installing and using PLCC
  in different environments. * Add `installer/install.bash` that automates installing PLCC in a bash
  environment.

- Improve load_rough_spec coverage
  ([`8170cf5`](https://github.com/ourPLCC/plcc-ng/commit/8170cf5dcb7c8a8dece62b07be1fc8426f679e33))

- Improve parse_lexical_spec coverage
  ([`e131939`](https://github.com/ourPLCC/plcc-ng/commit/e131939d3a9a5079adf88996f5feb4b494aefce7))

- Improve parse_syntactic_spec coverage
  ([`8bb6551`](https://github.com/ourPLCC/plcc-ng/commit/8bb65514184cdfee7f7d0d2aada7ecdd70f7bdbc))

- Install ag and reuse on demand
  ([`3c68616`](https://github.com/ourPLCC/plcc-ng/commit/3c686167555ddc29de2dd9b8ee7b853c5a43cac4))

- Install jdk in same terminal
  ([`33f32a4`](https://github.com/ourPLCC/plcc-ng/commit/33f32a43d27b0e4b7de32a486f240571959f3fa5))

- Makeabstractstub
  ([`0d0238e`](https://github.com/ourPLCC/plcc-ng/commit/0d0238e69eaa1cfc265baaba168fd527b3325cfa))

- Makestub
  ([`2b5f9c9`](https://github.com/ourPLCC/plcc-ng/commit/2b5f9c98c33f48fa71cd11a13fd21985a0b4347b))

- Move build_parsing_table int LL1
  ([`96a9391`](https://github.com/ourPLCC/plcc-ng/commit/96a93910690148ae8b46303a26998802d003fb27))

- Move code gen for sem() into CodeGenerator
  ([`46441a5`](https://github.com/ourPLCC/plcc-ng/commit/46441a5a769798b89886faa7ada31504f5774dea))

- Move Examples to ourPLCC/languages ([#75](https://github.com/ourPLCC/plcc-ng/pull/75),
  [`a53559e`](https://github.com/ourPLCC/plcc-ng/commit/a53559e2016d342d5f553a0dd4878ecda80d7d6d))

- Move into specparse ([#38](https://github.com/ourPLCC/plcc-ng/pull/38),
  [`71a7ce4`](https://github.com/ourPLCC/plcc-ng/commit/71a7ce4f3f859ce022ac528b1846a781032a840f))

- Move lineparse into specparse ([#39](https://github.com/ourPLCC/plcc-ng/pull/39),
  [`a698706`](https://github.com/ourPLCC/plcc-ng/commit/a69870672d374c41af79a9792b54d84abc0fb286))

- Move parse_syntactic_spec under parse_spec
  ([`8ceb3f1`](https://github.com/ourPLCC/plcc-ng/commit/8ceb3f15af95e68c6f9391d703141a69cf914081))

- Remove include and #include
  ([`f586fe2`](https://github.com/ourPLCC/plcc-ng/commit/f586fe27f5f588ebf0840c58f685631d10601d9f))

BREAKING CHANGE: remove include, use %include

BREAKING CHANGE: remove #include, use %include

- Remove plcc_cli.py and spec_cli.py subcommand dispatcher
  ([`517b6be`](https://github.com/ourPLCC/plcc-ng/commit/517b6be56395c0b21617800a9ecfd7673eabf119))

- Remove rep-t and rep-t.bat ([#84](https://github.com/ourPLCC/plcc-ng/pull/84),
  [`cc95bd5`](https://github.com/ourPLCC/plcc-ng/commit/cc95bd5ae53c42fc0553738e280bb6ec1f358bc4))

BREAKING CHANGE: `rep-t` and `rep-t.bat` removed. Instead Use `rep -t` and `rep.bat -t`.

Closes #81

- Remove superfluous EOF handling code ([#19](https://github.com/ourPLCC/plcc-ng/pull/19),
  [`b1817b7`](https://github.com/ourPLCC/plcc-ng/commit/b1817b71cf970000493fb439f2d6a11ccaf3045a))

Remove three lines from the printTokens() method in Std/Scan.java relating to EOF since they would
  never be executed.

- Remove support for Batch file ([#86](https://github.com/ourPLCC/plcc-ng/pull/86),
  [`12c22b4`](https://github.com/ourPLCC/plcc-ng/commit/12c22b4939d976ae29b164688a8fb9bc170294e5))

BREAKING CHANGE: removes .bat files. Windows users will need to get a Bash/Linux environment. We
  suggest installing WSL.

- Remove unused default parameters ([#81](https://github.com/ourPLCC/plcc-ng/pull/81),
  [`7984d78`](https://github.com/ourPLCC/plcc-ng/commit/7984d7833886626ef34776c1bc56e5f3c88f5936))

In the beginning, all functions that used a regex accepted a default parameter as the regex. I
  thought it would be nice to allow these to be passed by the caller in case the syntax ever
  changed. For example...

```python def parseTerminal(pattern=r'[A-Z_]+'): ... ```

This overcomplicates the function, and makes you wonder if there are any call sites that are passing
  a different regex.

These should be rewriting to something like the following:

```python def parseTerminal(): pattern = r'[A-Z_]+' ... ```

Closes #75

- Remove unused import
  ([`5e91439`](https://github.com/ourPLCC/plcc-ng/commit/5e914394a570bad01c47f7553104deae7d77d1f7))

- Remove ValidationError3 ([#80](https://github.com/ourPLCC/plcc-ng/pull/80),
  [`3d41494`](https://github.com/ourPLCC/plcc-ng/commit/3d414944172fa1b04cdfeec8a0e1413724c1b924))

When I moved all errors to plcc/load_spec/errors.py I found 3 implementations of ValidationError. To
  allow the refactoring tool to work and make the move, I first renamed two of the implementations
  to ValidationError2 and ValidationError3. Once the move was made, I compared the implementations
  and found that the original and 2 were the same, so I renamed ValidationError2 (and all its
  references) to just ValidationError. Then I removed it leaving the original.

ValidationError3's implementation is different. It's constructor takes a different parameter. This
  commit removes ValidationError3 and has each of its subclass call the superclass constructor with
  the normal expected parameters. No changes are needed by client code except their import
  statements had to be adjusted to use ValidationError instead of ValidationError3.

Closes #79

- Remove version
  ([`f7f4f6f`](https://github.com/ourPLCC/plcc-ng/commit/f7f4f6f5ceea667b1390d1162ab360a12e534daf))

- Rename LL1 and sub units for consistency
  ([`ce3e762`](https://github.com/ourPLCC/plcc-ng/commit/ce3e76247a73c815b17306f3ecc16d9fa5a3b94a))

- Rename plccng package to plcc
  ([`a282434`](https://github.com/ourPLCC/plcc-ng/commit/a2824340d18feb65465f971c619159e53d2f674f))

Renames src/plccng → src/plcc, updates all internal imports, renames plccng_cli.py → plcc_cli.py and
  PlccngCli → PlccCli, updates pyproject.toml (project name, console scripts entry point, coverage
  module), and confirms 323 tests pass (stale .pyc cache cleared to resolve EOFError on collection).

Test file classification: - Keep as-is (import-only updates, already applied): 37 files
  lines/parse_from_string_test.py scan/json_formatter_test.py scan/matcher_test.py
  scan/scan_cli_test.py scan/scanner_test.py scan/sink_test.py scan/source_test.py
  scan/text_formatter_test.py spec/SpecError_test.py spec/lexical/parse_lexical_test.py
  spec/parseSpec_test.py spec/rough/parseRough_test.py spec/rough/parse_blocks_test.py
  spec/rough/parse_dividers_test.py spec/rough/parse_from_lines_test.py
  spec/rough/parse_includes_test.py spec/rough/resolve_includes_test.py
  spec/semantics/parse_code_fragments_test.py spec/semantics/parse_semantic_spec_test.py
  spec/semantics/parse_target_locator_test.py spec/semantics/validation_test.py
  spec/spec_cli_test.py spec/syntax/parse_syntactic_spec_test.py
  spec/syntax/validations/ll1/Grammar_test.py spec/syntax/validations/ll1/LL1Wrapper_test.py
  spec/syntax/validations/ll1/build_first_sets_test.py
  spec/syntax/validations/ll1/build_follow_sets_test.py
  spec/syntax/validations/ll1/build_parsing_table_test.py
  spec/syntax/validations/ll1/build_spec_grammar_test.py
  spec/syntax/validations/ll1/check_left_recursion_test.py
  spec/syntax/validations/ll1/check_ll1_test.py
  spec/syntax/validations/ll1/check_parsing_table_for_ll1_test.py
  spec/syntax/validations/replace_repeating_with_standard_rules_test.py
  spec/syntax/validations/validate_lhs_test.py spec/syntax/validations/validate_rhs_test.py
  spec/syntax/validations/validate_syntactic_spec_test.py
  spec/syntax/validations/validate_terminals_defined_test.py - Migrated (content changes beyond
  imports): 1 file plcc_cli_test.py (run() call arg updated plccng→plcc, PlccngCli→PlccCli) - Delete
  later (Task 7b): plcc_cli_test.py covers plcc_cli.py which is scheduled for deletion in Task 7b;
  tests still pass for now

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Rename project name plccng ([#15](https://github.com/ourPLCC/plcc-ng/pull/15),
  [`d1d063f`](https://github.com/ourPLCC/plcc-ng/commit/d1d063f82c4b4db51a38d915f786b33771cdc173))

- Rename shell/ containers/ and consolidate containers
  ([#76](https://github.com/ourPLCC/plcc-ng/pull/76),
  [`7d3e69c`](https://github.com/ourPLCC/plcc-ng/commit/7d3e69c08266602eafae38a17b9a4f2efb5232ef))

- Rename stuff
  ([`1e356fb`](https://github.com/ourPLCC/plcc-ng/commit/1e356fb85e9e1938f6c6fa53b92439ec06be1482))

- Rename top-level python package to plccng ([#20](https://github.com/ourPLCC/plcc-ng/pull/20),
  [`d45cb2f`](https://github.com/ourPLCC/plcc-ng/commit/d45cb2f08d43ac2bed0b064d3386a402f21d50ce))

- Rename ValidationError2 to SpecError ([#44](https://github.com/ourPLCC/plcc-ng/pull/44),
  [`7e8c115`](https://github.com/ourPLCC/plcc-ng/commit/7e8c115958d79bfe8121acbb7dad7313edc66f4d))

- Reorganize files
  ([`ad2f51f`](https://github.com/ourPLCC/plcc-ng/commit/ad2f51f64bee866d3c1749005bd3eda701c9a94f))

BREAKING CHANGE: Moves all source files into a subdirectory named src within the PLCC project. The
  path to this src directory is what the LIBPLCC environment variable must point to, and is also the
  path that must be added to the PATH environment variable. When upgrading, these environment
  variables must be manually adjusted to point to the new src directory.

- Separate parsing from codegen for arbno
  ([`90f1a7d`](https://github.com/ourPLCC/plcc-ng/commit/90f1a7db6a9ad3ac863c75216f8ff677775d1913))

- Split and validate rough_spec before parsing
  ([`f0dcb9a`](https://github.com/ourPLCC/plcc-ng/commit/f0dcb9a95bb05257a88cff21205489159420bc8b))

Split the rough_spec into a RoughSpec object that holds attributes for the three distinct sections:
  lexical, syntactic, and semantic. Add a validation method, which returns a list of
  ValidationErrors. This will make it easier to parse each individual part later on.

---

* Closes #4 * Closes #12

Co-authored-by: Akshar Patel <aksharpatel1233@gmail.com>

Co-authored-by: Stoney Jackson <dr.stoney@gmail.com>

- Use "build"
  ([`cf5eb0a`](https://github.com/ourPLCC/plcc-ng/commit/cf5eb0ae35ebe39a02b9ab3a415c300249bb6947))

We had too many names for the same thing:

* build * generate * create

Let's use the shorter: "build".

- Use CLASSPATH
  ([`ad0619b`](https://github.com/ourPLCC/plcc-ng/commit/ad0619b40b3d049cc49464080e23554d38ed97ef))

- Use exception handling
  ([`10b6cef`](https://github.com/ourPLCC/plcc-ng/commit/10b6cef1039043c29dbfc97e43d663495dd080f4))

- Use functions to create strings
  ([`18424f7`](https://github.com/ourPLCC/plcc-ng/commit/18424f7620742dc71580241ed48e772afa55ca66))

- Use one generator throughout
  ([`6f71880`](https://github.com/ourPLCC/plcc-ng/commit/6f718809a3b275e7e48015aac740719fcc630af7))

- Validationerror2 ([#43](https://github.com/ourPLCC/plcc-ng/pull/43),
  [`745900a`](https://github.com/ourPLCC/plcc-ng/commit/745900a0979293a0ae4cedfc241e5138ac8c9b31))

The new ValidationError2 contains a column, and a __str__() method that prints a standard message.
  Now we migrate each existing ValidationError to the new one. Once all errors are migrated, we'll
  collapse the two into a single class.

- Wip buildStubs
  ([`1c4812b`](https://github.com/ourPLCC/plcc-ng/commit/1c4812bace4ab1b67d479b5c62725ca2e60a2b09))

- **build_first_sets**: Remove check for left recursion
  ([`11cdbe2`](https://github.com/ourPLCC/plcc-ng/commit/11cdbe2179dd339e94bd433efc3ef1f2b8f20526))

This clutters the algorithm. We will add this as a separate module.

- **build_first_sets**: Remove memoFirst
  ([`3c135f0`](https://github.com/ourPLCC/plcc-ng/commit/3c135f042fbd7eb5421b8c150363bab2a3b15dc7))

memoFirst is an optimization. We don't know that we need it. So it's premature optimization. And
  Donald Knuth says, "premature optimization is the root of all evil." So it adds obvious complexity
  without a measurable, significant gain.

- **build_follow_sets**: Clean
  ([`3d31ae3`](https://github.com/ourPLCC/plcc-ng/commit/3d31ae331581fd4dbeeef39f139d7bf49fcecec8))

- **build_parsing_table**: Clean
  ([`0b9c8b6`](https://github.com/ourPLCC/plcc-ng/commit/0b9c8b66144eb3b0745f207df62fe6584e08ee8e))

- **check_ll1**: Integrating
  ([`4c10525`](https://github.com/ourPLCC/plcc-ng/commit/4c10525b764e334d7111168b84556b2b8b681b0a))

* Unify types across components. * Remove dependencies and simplify when possible.

- **ci**: Fix build failure ([#98](https://github.com/ourPLCC/plcc-ng/pull/98),
  [`457a505`](https://github.com/ourPLCC/plcc-ng/commit/457a505c07e8c09340b1d6254471d03fa712863d))

Checks were added to prevent folks from breaking their system's Python installation by updating it
  or adding libraries to it.

Our Dockerfile was doing this. So now we don't. We still make sure that Python 3 is installed. But
  we don't try to upgrade it or pip.

In the future, we may want to figure out how to use something like venv to install a particular
  version of Python that PLCC will use, that is independent of the system's Python.

Closes #97

- **docker**: Move PLCC-in-Docker to a separate project
  ([#16](https://github.com/ourPLCC/plcc-ng/pull/16),
  [`c24eb6f`](https://github.com/ourPLCC/plcc-ng/commit/c24eb6fa298c69c9a55b3094dfa4eb8d9d41137b))

- **gitpod**: Dev ready in first terminal ([#100](https://github.com/ourPLCC/plcc-ng/pull/100),
  [`02c37f0`](https://github.com/ourPLCC/plcc-ng/commit/02c37f03e012c9cde2a709f34c35cd617db1ef7e))

- **gitpod**: Testing ([#102](https://github.com/ourPLCC/plcc-ng/pull/102),
  [`112fe81`](https://github.com/ourPLCC/plcc-ng/commit/112fe81efcc5333d1ab0cfb087eba1e22c634b91))

- Setup GitPod to install dependencies necessary to run tests. - Add scripts in bin/test/ to run
  various tests. - bin/test/everything.bash runs all the tests.

---

Closes #101

- **Grammar**: Any iterable is a valid form
  ([`2bdf42f`](https://github.com/ourPLCC/plcc-ng/commit/2bdf42fe23e0710d287c8fc4d1ca27601d968e27))

The second parameter to addRule() must be an iterable. With this change, a str passed as a second
  parameter would result in each character being treated as a symbol. If this was not the intent of
  the programmer, then this is an error. However, this error should be detected by unit tests.

- **Grammar**: Let set detect invalid symbols
  ([`d8e69ca`](https://github.com/ourPLCC/plcc-ng/commit/d8e69ca898f81a3d2f3a268c60fbf914b5a7a611))

If Grammar is passed an invalid symbol, Python's set will detect it and raise a TypeError. We don't
  need an extra layer of code to detect and translate these errors into a different exception.

Note, we would need this extra layer of code if this was a user error that we were trying to detect
  and report to the user. But this is an internal programmer error that should be detected and
  reported by unit tests.

- **Grammar**: Let set detect invalid symbols
  ([`568d20c`](https://github.com/ourPLCC/plcc-ng/commit/568d20c5dc97a5c6444ee4da380a494c5f022e4f))

If Grammar is passed an invalid symbol, Python's set will detect it and raise a TypeError. We don't
  need an extra layer of code to detect and translate these errors into a different exception.

Note, we would need this extra layer of code if this was a user error that we were trying to detect
  and report to the user. But this is an internal programmer error that should be detected and
  reported by unit tests.

- **Grammar**: Remove generate_grammar()
  ([`c530f44`](https://github.com/ourPLCC/plcc-ng/commit/c530f445ca9ea1bcddc1d0ce16cb38beb62d93e5))

Grammer is a data structure (and not a functional unit), and generate_grammar does not provide any
  additional functionality. So delete generate_grammar().

- **Grammar**: Simplify and clarify
  ([`ac60fc4`](https://github.com/ourPLCC/plcc-ng/commit/ac60fc47d79c39b3f61fec8c01135dfdfbcc2260))

* Replace str with object in all public methods. * Remove nonterminals set and use keys from rules
  instead. * isTerminal(s) is true only if s has been seen and is not a nonterminal. * General
  cleanning and reorganizing.

- **load_rough_spec**: Remove types, imports, and params
  ([#24](https://github.com/ourPLCC/plcc-ng/pull/24),
  [`393e99e`](https://github.com/ourPLCC/plcc-ng/commit/393e99e4ad2a7b78de1cf135b624d549480cf40a))

- **make**: Use ExitStack in _run_or_die and document stderr passthrough
  ([`e3c85cd`](https://github.com/ourPLCC/plcc-ng/commit/e3c85cd17e3c0774cf80f32d3470a4a30f881475))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parse_rough**: Removes the concept of a rough **Spec**.
  ([`f5f2311`](https://github.com/ourPLCC/plcc-ng/commit/f5f2311fa9fcb2c4fb4a40726e9712748e631451))

- **parse_spec**: Massive reorganization ([#37](https://github.com/ourPLCC/plcc-ng/pull/37),
  [`7ec7951`](https://github.com/ourPLCC/plcc-ng/commit/7ec795126debd44803caf196d9a7b61266624453))

* Rename many components. * Colocate validators with related components. * Rewrite tests as needed.
  * Extract lineparse as a separate reusable module. * Store structures and errors in separate
  modules and colocate with code that constructs them. * Split validators making them more
  independent. * In lex spec, regex is delimited by any character the user chooses. But there are no
  escape sequences.

- **parser**: Extract _path_dirs and _is_executable helpers to match lang/list.py style
  ([`8f2fa47`](https://github.com/ourPLCC/plcc-ng/commit/8f2fa470b892ab7720e1110a50e4094942feb661))

- **scan**: Retire old scan package and stale tests
  ([`29e18a3`](https://github.com/ourPLCC/plcc-ng/commit/29e18a306554f97c34ed62b174840737a489bf16))

- **spec**: Improve interface ([#74](https://github.com/ourPLCC/plcc-ng/pull/74),
  [`b160a8f`](https://github.com/ourPLCC/plcc-ng/commit/b160a8f53006615d60973949dac51f3355a449ab))

- **spec.lexical**: Clean imports ([#52](https://github.com/ourPLCC/plcc-ng/pull/52),
  [`d6090e6`](https://github.com/ourPLCC/plcc-ng/commit/d6090e69ec6a61ea18b5e71725af742dc71506fd))

- **spec.lexical**: Make single entry parse_lexical
  ([#51](https://github.com/ourPLCC/plcc-ng/pull/51),
  [`2c4a4f3`](https://github.com/ourPLCC/plcc-ng/commit/2c4a4f32a340a2d64fadda32ae4fe3f33d2a3dbb))

- **spec.lexical**: Redesign ([#54](https://github.com/ourPLCC/plcc-ng/pull/54),
  [`9d675d4`](https://github.com/ourPLCC/plcc-ng/commit/9d675d4a7c4f15269a83eff0768f60eda89fdf73))

* parseLexicalSpec now returns a spec and a list of errors. * Parser performs validations. * All
  tests are performed on top-level parseLexicalSpec. * Errors now accept an index or column; if
  index given column=index+1.

- **spec.lexical**: Remove type annotations ([#53](https://github.com/ourPLCC/plcc-ng/pull/53),
  [`4cd0d90`](https://github.com/ourPLCC/plcc-ng/commit/4cd0d90f3cff69891ab272e20283ae47cf9105d4))

- **spec.lines**: Single entry parseLines ([#55](https://github.com/ourPLCC/plcc-ng/pull/55),
  [`43a12b0`](https://github.com/ourPLCC/plcc-ng/commit/43a12b06ef48de6919db887986939f07426a0a01))

- **spec.rough**: Add handler param to parse_blocks
  ([#46](https://github.com/ourPLCC/plcc-ng/pull/46),
  [`6bb8204`](https://github.com/ourPLCC/plcc-ng/commit/6bb820414c334ffe62fb395b99cc79e6554388e1))

The default handler raises an exception (existing behavior).

If a handler is passed, and no closing %%% is found, then parse_blocks produces a Block containing
  all of the lines from the opening to the end of the file, plus an additional line that
  parse_blocks creates to represent the closing of the block.

- **spec.rough**: Add handler param to parse_from_*
  ([#47](https://github.com/ourPLCC/plcc-ng/pull/47),
  [`c08b2bf`](https://github.com/ourPLCC/plcc-ng/commit/c08b2bfced90ffc718140149d76fd9870db6c734))

This completes our refactor to add handler param to spec.rough. Callers can now pass a `handler`
  callback to parse_from_* functions. The handler is called for each error encountered during the
  processing. If the handler raises and exception, then processing is halted and the exception is
  raised. Otherwise the parser does its best to continue.

```python from plccng.spec.rough import parse_from_string results = list(parse_from_string(...,
  handler=lambda e: print(e))) ```

There are currently two possible errors when parsing the rough. CircularIncludeError and
  UnclosedBlockError. When a CircularIncludeError is encountered, the handler is called, the Include
  is skipped, and processing continues. When an UnclosedBlockError is encountered, the handler is
  called, a closing is created to finish the Block, and processing continues.

In the future, when new errors are added, the creator must decide how processing can continue when
  that error is detected.

- **spec.rough**: Add handler param to resolve_includes
  ([#45](https://github.com/ourPLCC/plcc-ng/pull/45),
  [`52d7cca`](https://github.com/ourPLCC/plcc-ng/commit/52d7cca398e31a019200fc0b1797cba7cf359e3a))

Currently rough raises exceptions when errors found. Instead we want to hand back a list of errors
  during processing, and to try to continue processing as much as possible.

But rough is implemented as a composable set of generator returning functions. It doesn't make sense
  for it to return a list of errors along with a generator, because the error list would always be
  initially empty; and the error list would fill as the generator is expanded. This would be
  confusing and would likely lead to complicated error prone code in clients.

Instead, we'll add an optional callback parameter to each parse function. This callback will be
  called and passed an error object each time an error is detected. Assuming the callback doesn't
  raise an exception, processing will continue after the callback returns. This will allow clients
  to choose how to handle errors.

This commit is the first step along this path. It adds a `handler` callback parameter to
  `resolve_includes`. For example, a client can collect errors during processing but allow
  processing to continue as follows.

```python errors = [] generator = resolve_includes(..., handler=lambda e: errors.append(e)) ````

If a handler is not provided, resolve_includes raises the first error it encounters (the current
  behavior).

- **spec.rough**: Migrate CircularIncludeError to SpecError
  ([#48](https://github.com/ourPLCC/plcc-ng/pull/48),
  [`8ae43f5`](https://github.com/ourPLCC/plcc-ng/commit/8ae43f5412f5f87e2d58e3e19c0ddae8c56a2b57))

- **spec.rough**: Migrate UnclosedBlockError to SpecError
  ([#49](https://github.com/ourPLCC/plcc-ng/pull/49),
  [`9230b07`](https://github.com/ourPLCC/plcc-ng/commit/9230b079364c69ac3588a8143408f29f173eca3b))

- **spec.rough**: Rename entry parseRough ([#56](https://github.com/ourPLCC/plcc-ng/pull/56),
  [`b7ed88d`](https://github.com/ourPLCC/plcc-ng/commit/b7ed88d5e9e2be4c7e284bd9a6d7347933f531dd))

- **spec.rough**: Simplify interface ([#50](https://github.com/ourPLCC/plcc-ng/pull/50),
  [`2354224`](https://github.com/ourPLCC/plcc-ng/commit/235422404b28485081f5b3c4c6ff969c508bee8c))

Now there's just parse_rough. parse_rough takes a string or a list of Lines and returns a rough and
  a list of errors.

rough, errors = parse_rough([])

You can also pass a file path (str) and a startingLineNumber (int).

- **tests**: Split tests into multiple files
  ([`3bbdd57`](https://github.com/ourPLCC/plcc-ng/commit/3bbdd5722423dc4f654de9d4111c79a3f6585f8c))

- **tree**: Drop 'error' from children kind enum; errors go to stderr per §17.9
  ([`7e30963`](https://github.com/ourPLCC/plcc-ng/commit/7e3096300a1e63b492f6c1d70622bed78ab31665))

- **tree**: Rewrite plcc-tree as parser dispatcher (--ll1, --parser)
  ([`7fca6ce`](https://github.com/ourPLCC/plcc-ng/commit/7fca6ce0c6064357b1800b57b2cada66f03bb830))

Replaces the old pass-through stub (--spec) with a dispatcher that invokes plcc-parser-{kind}
  plugins, defaulting to plcc-parser-table. Updates all affected BATS tests to use the new --ll1
  interface.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

### Testing

- Add -c option to plccmk
  ([`bc2f715`](https://github.com/ourPLCC/plcc-ng/commit/bc2f71512cc9719569aed4bfadcd7d2ee5e094ea))

- Add -n to parse and update expected output
  ([`b47b390`](https://github.com/ourPLCC/plcc-ng/commit/b47b39079cd8b4635a1e6dffa766326460e84114))

- Add initial tests
  ([`884ea96`](https://github.com/ourPLCC/plcc-ng/commit/884ea96834714966523d3376e697f20d8effbfc0))

tests.sh needs plcc and bats installed to run.

If you have Docker installed you can run theme as follows:

./shell/build ./shell/run ./tests.sh exit

- Add null entry_point and session-continuation acceptance tests
  ([`1aad646`](https://github.com/ourPLCC/plcc-ng/commit/1aad646eceb5e5fe9e380c55df340b8fd55935fd))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- Add script to run ourPLCC/languages' tests
  ([`9329cdf`](https://github.com/ourPLCC/plcc-ng/commit/9329cdf420263120f9909666966a7f3f49715885))

- Allow local run of min-max test ([#67](https://github.com/ourPLCC/plcc-ng/pull/67),
  [`cd8b9fe`](https://github.com/ourPLCC/plcc-ng/commit/cd8b9fe5df3df87cf9d2a6470cb14a1fc15f638d))

We got min-max test working in CI/CD. But developers should not have to push code just to run this
  important test. This commit allows developers run an equivalent test locally.

- Clean up tests ([#114](https://github.com/ourPLCC/plcc-ng/pull/114),
  [`460d1e7`](https://github.com/ourPLCC/plcc-ng/commit/460d1e7eb2d4090b04146e5b9c549f036d90f99a))

- Isolate tests from each other
  ([`8ba4966`](https://github.com/ourPLCC/plcc-ng/commit/8ba4966248836facb5838ff5e9c800d05f33d57d))

---

Closes #103

- Min and max python and java ([#65](https://github.com/ourPLCC/plcc-ng/pull/65),
  [`422c08f`](https://github.com/ourPLCC/plcc-ng/commit/422c08f7df48fc67c7d2c19cdc513a03c1deb034))

Run tests on minimum and maximum versions of Python and Java. Maximum versions are the latest,
  stable releases of each. Minimum versions are currently:

* Python: 3.5.10 (as identified with pyenv) * Java: 11.0.21-tem (as identified with sdkman)

---

Closes #64 Closes #63

- Print headers
  ([`56b9a49`](https://github.com/ourPLCC/plcc-ng/commit/56b9a4977c07ff5012bd05556e0fc3706ae8525c))

- **arbno**: Add trivial-arbno.plcc fixture
  ([`3415618`](https://github.com/ourPLCC/plcc-ng/commit/3415618943b477d1594d6f51c42cd6f5163d7b16))

- **bats/commands**: Add black-box CLI tests for all Level 0 commands
  ([`1f88d90`](https://github.com/ourPLCC/plcc-ng/commit/1f88d90754cb0f42201208061d8a5d63a1e783a2))

Creates 10 BATS test files covering plcc-spec, plcc-tokens, plcc-model, plcc-tree, plcc-lang-list,
  plcc-lang-emit, plcc-lang-build, plcc-plantuml-emit, plcc-make, and plcc-skeletons. Also adds a
  plantuml_only.plcc fixture to enable plcc-make tests without requiring the Java emitter.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **bats/e2e**: Add end-to-end happy path and error propagation tests
  ([`43113b6`](https://github.com/ourPLCC/plcc-ng/commit/43113b6c01aaa303e7cc4606f25149fb35067457))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **bats/integration**: Add adjacent pipeline pair integration tests
  ([`338c15d`](https://github.com/ourPLCC/plcc-ng/commit/338c15db5f5dc599e13943a251bffb522365bd9f))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **build_bollow_sets**: Up coverage, add acceptance tests
  ([`a3e939f`](https://github.com/ourPLCC/plcc-ng/commit/a3e939f25c9f723204438a001777ab1d6f25bd38))

* Add a test to cover case when follows of subsequent symbols all contain epsilon, and so follows
  then includes parent's follows.

* In code, removed a test for symbol being epsilon. This shouldn't be possible because Grammar rules
  do not contian a symbol for epsilon; epsilon is represented by an empty production. However, a
  symbol IS still used for first sets, and Grammar does hold a symbol for use in first sets.

- **corpus**: Add ARRAY grammar to Java corpus
  ([`6b20d1c`](https://github.com/ourPLCC/plcc-ng/commit/6b20d1cb5c59ba5b0c19661b4d46a08103721bb3))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add BF grammar to Java corpus
  ([`435ea0f`](https://github.com/ourPLCC/plcc-ng/commit/435ea0f2e5668ea75b65ffd6eac4b015ae4f0369))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add GINGER grammar to Java corpus
  ([`d39fd31`](https://github.com/ourPLCC/plcc-ng/commit/d39fd31504310517c1e0f2f34631fe7173a3cdb3))

- **corpus**: Add HANDLER grammar to Java corpus
  ([`8e34492`](https://github.com/ourPLCC/plcc-ng/commit/8e34492d2987355cef6d2c2eb4f0bc546b220bef))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add INFIX grammar to Java corpus
  ([`79aca54`](https://github.com/ourPLCC/plcc-ng/commit/79aca54d37714baa64c9ef9e8f15b5701d57b090))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add LAMBDA grammar to Java corpus
  ([`9d50505`](https://github.com/ourPLCC/plcc-ng/commit/9d505055fb6c32e99e4fbdd7c146e6d4cd76a3f4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add LAMBDAQ grammar to Java corpus
  ([`755e80e`](https://github.com/ourPLCC/plcc-ng/commit/755e80e810591ef02489cd782af638261e05ae9a))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add languages-java e2e corpus infrastructure
  ([`6f8c10a`](https://github.com/ourPLCC/plcc-ng/commit/6f8c10a21459dc95a76d5da2bc653a802f235beb))

- **corpus**: Add LIST grammar to Java corpus
  ([`1365f4a`](https://github.com/ourPLCC/plcc-ng/commit/1365f4a7e0f49a196575e4a342aacc3b8c37d609))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add LON grammar to Java corpus
  ([`0ca5b19`](https://github.com/ourPLCC/plcc-ng/commit/0ca5b190a731987faacb405897aa0c8696642346))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add LON2 grammar to Java corpus
  ([`7b7820e`](https://github.com/ourPLCC/plcc-ng/commit/7b7820e67f00b304226600f73dec875c7a446337))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add LONN grammar to Java corpus
  ([`28f3f25`](https://github.com/ourPLCC/plcc-ng/commit/28f3f2523e45caa0ebc65ace9165318409a2cb86))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add NAME grammar to Java corpus
  ([`935a0af`](https://github.com/ourPLCC/plcc-ng/commit/935a0af70d6a5ad51778844bb33a58990d04e8f1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add NEED grammar to Java corpus
  ([`d61f4b7`](https://github.com/ourPLCC/plcc-ng/commit/d61f4b7f0deb32c2a0f1f8426b193edc9ebf281c))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add OBJ grammar to Java corpus
  ([`3171ee5`](https://github.com/ourPLCC/plcc-ng/commit/3171ee5a57ad1e725a0b8b7cea6e53d69996a7f4))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add PROP grammar to Java corpus
  ([`60418fc`](https://github.com/ourPLCC/plcc-ng/commit/60418fc2cd80f4b9409da752de303420b710570d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add RANDSCONT grammar to Java corpus
  ([`8383c59`](https://github.com/ourPLCC/plcc-ng/commit/8383c59a078051741251979376b0c00174441a49))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add REF grammar to Java corpus
  ([`2521b9e`](https://github.com/ourPLCC/plcc-ng/commit/2521b9e77f517b7115912baec641f4a6f4b96cb7))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add REFCONT grammar to Java corpus
  ([`737cbf9`](https://github.com/ourPLCC/plcc-ng/commit/737cbf969a27d51ef45082ce68d200ffa6c36f62))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add SET grammar to Java corpus
  ([`d4af882`](https://github.com/ourPLCC/plcc-ng/commit/d4af88212921142e134a2ca7e04af67303fd724b))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add THREADCONT grammar to Java corpus
  ([`7d425ac`](https://github.com/ourPLCC/plcc-ng/commit/7d425ac756f7a72c2de332c240019c78a3729dab))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add TYPE0 grammar to Java corpus
  ([`e3993b9`](https://github.com/ourPLCC/plcc-ng/commit/e3993b9e7b4c3f895acbffe7363d4c9216a22f76))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add TYPE1 grammar to Java corpus
  ([`6e97e43`](https://github.com/ourPLCC/plcc-ng/commit/6e97e43603d289394f14b9f1807fe215cab4e32d))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add V0 grammar to Java corpus
  ([`a60f034`](https://github.com/ourPLCC/plcc-ng/commit/a60f034396d837b738104083d4604b5eca698651))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **corpus**: Add V1 grammar to Java corpus
  ([`44adbf9`](https://github.com/ourPLCC/plcc-ng/commit/44adbf9f76b9cabb06613769d15be30a27b03579))

- **corpus**: Add V2 grammar to Java corpus
  ([`427f9fb`](https://github.com/ourPLCC/plcc-ng/commit/427f9fb89adea56e6ea6c6048a94374d0e44058e))

- **corpus**: Add V3 grammar to Java corpus
  ([`6ab5a04`](https://github.com/ourPLCC/plcc-ng/commit/6ab5a0404e133d94753a67ccb52997c8d470723d))

- **corpus**: Add V4 grammar to Java corpus
  ([`486fd66`](https://github.com/ourPLCC/plcc-ng/commit/486fd66d8d4c09abae03d31e28a5de396d8f38e1))

- **corpus**: Add V5 grammar to Java corpus
  ([`fb39780`](https://github.com/ourPLCC/plcc-ng/commit/fb397807207b0796c86b68d9a5bf23419f7411db))

- **corpus**: Add V6 grammar to Java corpus
  ([`8b88089`](https://github.com/ourPLCC/plcc-ng/commit/8b880895cf496ae617ccfeda5bdcc59f2b6f0218))

- **e2e**: Add debug statements
  ([`d12e47b`](https://github.com/ourPLCC/plcc-ng/commit/d12e47bb64f857f5a26244f62a74139d9a3d3f0d))

- **e2e**: Add plcc-rep.bats end-to-end REPL acceptance tests
  ([`f265e7e`](https://github.com/ourPLCC/plcc-ng/commit/f265e7e7fbefcc0f0e3116ed29e2fe18c1f2fb64))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **e2e**: Add trivial-arbno.plcc end-to-end tests for plcc-rep
  ([`3026b60`](https://github.com/ourPLCC/plcc-ng/commit/3026b60a3e53ef197b61c009743596cd719b155b))

Also fix two pipeline bugs found while driving the tests: _count_rules in table_cli.py crashed on
  list-valued arbno children, and rep.py skipped evaluation when stdin was empty/whitespace-only,
  preventing arbno grammars from returning [] for zero-item input.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **e2e**: Fix test isolation in trivial-full e2e test
  ([`b3203f3`](https://github.com/ourPLCC/plcc-ng/commit/b3203f322a03fa945720e9b4e08f905d5e780979))

- **e2e**: Improve portability of mktemp
  ([`a86261f`](https://github.com/ourPLCC/plcc-ng/commit/a86261f3615b772e6c0ecaf7f75e1bb5eb53885f))

- **e2e**: Update smoke test for diagram pipeline and plcc-plantuml-emit retirement
  ([`c68e4ea`](https://github.com/ourPLCC/plcc-ng/commit/c68e4eae7a2357271b47b821a8d561e13269ea5c))

- Replace plantuml-emit-based happy-path.bats with diagram-pipeline tests - Fix trivial.plcc: remove
  trailing bare % that caused spurious Java semantics section - Update packaging.bash to verify
  plcc-diagram/plcc-diagram-list entry points instead of retired plcc-plantuml-emit

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **e2e**: Verify plcc-make produces output for all three language plugins
  ([`adca7fd`](https://github.com/ourPLCC/plcc-ng/commit/adca7fda25b5b2e8f36307bd49a09bd886c26628))

- **fixtures**: Add arith.plcc arithmetic evaluator grammar
  ([`f15de11`](https://github.com/ourPLCC/plcc-ng/commit/f15de11d5c848d4df5db5f98d03a32a873b05815))

- **fixtures**: Add input file, Java, Python, and full trivial grammars for skeleton update
  ([`387a541`](https://github.com/ourPLCC/plcc-ng/commit/387a541731d6af729a75fa4e80ee04f310f62d6b))

- **fixtures**: Add trivial grammar and input
  ([`f7502c7`](https://github.com/ourPLCC/plcc-ng/commit/f7502c7f9e9faf09f8ac069b7f7a1a5088e6358f))

- **fixtures**: Add trivial-plantuml.plcc for Phase 1 smoke test
  ([`c8bf7b9`](https://github.com/ourPLCC/plcc-ng/commit/c8bf7b983ad3497411e3b0dcb2226c2199244757))

trivial.plcc has an implicit Java semantics section (bare % defaults to Java) which causes plcc-make
  to fail in Phase 1 where plcc-java-emit is not installed. The new fixture uses only % diagram
  PlantUML so the smoke test exercises the full plcc-make pipeline without requiring Java.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **integration**: Add python-emit.bats integration tests
  ([`bd2d4dc`](https://github.com/ourPLCC/plcc-ng/commit/bd2d4dc715d6de55934c6ed3a4d8e1ff23f1e7d1))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **integration**: Add spec|ll1 and ll1|tree pipeline pair tests
  ([`0b601e9`](https://github.com/ourPLCC/plcc-ng/commit/0b601e94924497b7f50703d45e2ec78a23062a73))

- **java**: Update trivial-java fixture and command tests for real emitter
  ([`444950d`](https://github.com/ourPLCC/plcc-ng/commit/444950d339d0679ffac6b2add263cb3ffbd33439))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **java-emit**: Add integration tests for full emit→build→run pipeline
  ([`c8f7ded`](https://github.com/ourPLCC/plcc-ng/commit/c8f7ded604e3300328540c1de9c4373c35e8dc25))

- **model**: Add failing test for _extract_body trailing newline bug
  ([`851aa11`](https://github.com/ourPLCC/plcc-ng/commit/851aa112b613b105d6717a6ceff068281dc8aa09))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **model**: Add fragment pass-through tests for build_model
  ([`4cc4279`](https://github.com/ourPLCC/plcc-ng/commit/4cc427987717f16ad82b8c47256a29c6450db7eb))

Covers _compute_kind (body/file/modifier kinds), _extract_body (%%% stripping, indentation
  preservation), and _build_fragment integration via build_model.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **OBJ**: Add OBJ compilation test
  ([`1ae4eb4`](https://github.com/ourPLCC/plcc-ng/commit/1ae4eb45be8c8531512d681e912f02486de20c57))

- **packaging**: Add plcc-lang-list and plcc-diagram-list smoke checks
  ([`8c38364`](https://github.com/ourPLCC/plcc-ng/commit/8c38364c08a7c2dc359839a862ed79209c532c11))

- **parse_blocks**: Add regression test for trailing-space %%% delimiter
  ([`17155b9`](https://github.com/ourPLCC/plcc-ng/commit/17155b93b567f34c04419f3aca73520404c163b9))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add tree-shape assertions for plcc-parser-table and ll1-tree integration
  ([`56bb4d3`](https://github.com/ourPLCC/plcc-ng/commit/56bb4d363ba3e6a7b3ca6559efdd339a341f1226))

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

- **parser**: Add unit test for error record passthrough in plcc-parser-table
  ([`5b0f611`](https://github.com/ourPLCC/plcc-ng/commit/5b0f611e9178e7eaa222df8729a0978e86c51cd5))

- **validate_rhs**: Valid alternate name
  ([`a19def3`](https://github.com/ourPLCC/plcc-ng/commit/a19def3e183ffb24082181f29f5bf33a3246b5d0))
