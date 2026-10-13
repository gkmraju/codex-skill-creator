# Local review record

Reviewed 2026-10-13 against the fresh-session request and the additional pasted prior design.

## Standards

Applied Matt Pocock codebase-design: one command interface, shared rules for paths and evidence, isolated filesystem fixtures, no unused service abstractions. Applied writing-for-agents: concise project contract, explicit contextual pointers, and verification completion criteria.

Findings corrected:
- HTTPS URLs were falsely flagged as Windows paths.
- Artifact/source output overlap could cause recursive staging.
- License bytes needed hashes both before staging and in the final artifact.
- Source identity changes must invalidate selection reviews, not just skill-file changes.
- Frontmatter delimiters must be complete lines, so descriptions can contain dashes.
- Obvious key/credential files should be refused before copying.

Remaining design limits: one local writer, no concurrency locking, conservative local reference syntax, human binary/security and semantic overlap review.

## Spec

The local foundation supports documentation, inventory, source identity/attribution/revision, seven assessment dimensions, duplicate denial, guarded staging with preserved snapshots, structural validation, evidence-backed release checks, tests, CI configuration, and deterministic individual packages.

The confirmed layout and selection gates are represented. GitHub Issues and proposed labels are documented for later publication. Source discovery/ranking, the first real migration, functional Codex/installation acceptance, hosted CI, daily scheduling, Telegram, and GitHub publication remain outstanding.

The end-to-end tests use synthetic sources and reviewer reports and are not evidence of a real skill's behavior.

## Review workflow limit

Matt Pocock's full code-review skill requires a resolved fixed commit point and a nonempty diff against HEAD before parallel Standards/Spec reviews. This repository has no commits. That full skill workflow was not run; the review above is a local manual review informed by its two axes, not a claimed independent or fixed-commit review. No subagents were used.

The next review can use the first reviewed local commit as a baseline once commit history exists.
