# Release gates

Selection gates apply before staging:

1. License: actual applicable license and notices identified, content hashes recorded, modification and redistribution reviewed, decision allowed, and passing license evidence.
2. Codex overlap: compare triggers, workflow, outputs, and dependencies against built-in and installed skills. A materially equivalent skill fails this project's selection rule. Retain comparison evidence; automated name matching cannot resolve equivalence.
3. Prior work: compare registry source identities, capabilities, and gkmraju repositories. Reject duplicates or prepare an update to an existing candidate. Record search scope and time; an empty registry alone does not prove no prior work.

Release gates additionally require:

- Known immutable source revision/version, preserved attribution, hashed license/notice files.
- Complete compatible findings in all seven assessment dimensions and no unresolved blockers.
- Exactly one skill with valid name/description and instructions, all local Markdown/reference-style links and code-form resource references resolvable, portable paths, no linked filesystem paths.
- Required plugin manifest, provenance, README, migration, compatibility, and evaluation documents.
- No unexpected package files or obvious private paths/credential patterns.
- Passing compatibility, functional, security, and final-review reports bound to the complete artifact fingerprint. Functional reports include realistic exercised cases, environment, observed results, and captured output hashes.
- Explicit release-ready state plus a successful release-check immediately before packaging.

Structural validity is a separate result from functional acceptance. Test-suite fixtures exercise tooling and release denial logic; they do not exercise Codex skill selection or real upstream scripts. Evidence hashes verify integrity, not reviewer truthfulness.

Review all necessary scripts and binary assets manually. Link checks cover supported Markdown syntax, not arbitrary natural-language filenames, shell includes, or executable dependency graphs. A passing check cannot guarantee flawless behavior.

The individual package uses the supported Codex compatibility manifest (.codex-plugin/plugin.json) and skills/ directory from the agreed plan. Current official guidance recommends root plugin.json for new portable packages. Portable packaging can be added later after scope review. No marketplace or plugin installation has been exercised here.

Official references checked 2026-10-13:
- https://developers.openai.com/plugins/build/skills
- https://developers.openai.com/plugins/build/plugins
