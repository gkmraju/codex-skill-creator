# Release gates

Selection gates apply before staging:

1. License: actual applicable license and notices identified, content hashes recorded, modification and redistribution reviewed, decision allowed, and passing license evidence.
2. Codex overlap selection decision: for the current user-curated CSV, accept the user's explicit Claude-only/non-portable screening and waive fresh equivalence searches. Record curation authority, CSV hash/row, source binding and scope in evidence; do not claim independently verified absence. Sources outside this accepted queue still require comparative evidence.
3. Prior work: compare the current queue state and local candidate source/path identity. Inspect an existing target fork during publication and preserve its remote work. Do not rediscover or scan the entire account; record the precise local/target scope rather than claiming universal absence.

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

Public README quality is part of final review: follow docs/skill-readme.md, resolve template placeholders, verify commands/links and keep badges/results truthful before the final fingerprint.
