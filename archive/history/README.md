# Codex Skill Creator

A local control repository for discovering, assessing, adapting, validating, and packaging individual skills for Codex. It records decisions and evidence; it does not automatically translate instructions or publish.

**Current milestone:** working local tooling, tested with synthetic fixtures. No real skills have been migrated or released. See [STATUS.md](STATUS.md).

## Confirmed scope

- Control repository: gkmraju/codex-skill-creator.
- Authorized individual repositories: gkmraju/codex-skill-<slug>, one skill per repository.
- Compare equivalent Codex skills and prior internal work before migration.
- Preserve upstream identity, applicable licenses, notices, and original files.
- Search impactful Claude-origin skills across all audiences and the wider public Codex ecosystem. The first Anthropic sample remains unfinished; keep searching past failed candidates.
- Daily target: at least one fully adapted, behaviorally tested, installable, publicly published single-skill repository. Publication is authorized once the gates pass. The daily 07:00 IST job and compact Telegram reporting are configured.

The implementation choices are Python 3.11+, JSON records, YAML skill metadata, explicit reviewer evidence, separate source snapshots and editable outputs, and deterministic ZIP packages. These are current choices, not invented historical decisions.

## Setup and checks

From the project directory:

    python -m venv .venv
    .venv\Scripts\python -m pip install -r requirements.txt
    .venv\Scripts\python -m unittest discover -s tests -v
    .venv\Scripts\python -m skill_migration validate

Activation is optional. The shorter commands below assume the environment's Python is on PATH. Local checks also work with the confirmed host Python and installed dependencies.

To preserve actual check results and logs, run python scripts/verify.py. Results are saved locally under evidence/local-tooling/ and excluded from Git. A public-safe summary is in docs/verification.md. See docs/review.md for the scope and limitations of the local review.

The GitHub workflow runs the same tests and validation on Windows and Linux. Check the repository's Actions page for current results; local checks alone do not establish GitHub CI success.

## Local workflow

1. Select an approved source collection and obtain a local checkout at a known revision. Inventory its parent collection:

       python -m skill_migration inventory sources/upstream --collection-id upstream --origin https://github.com/owner/repo --attribution "Upstream authors" --revision FULL_COMMIT_SHA

   This reads source files without executing scripts. It adds candidates to registry/candidates.json. Repeating an inventory that creates duplicate identifiers, slugs, or source identities fails without changing the registry. Inspect new candidates before tracking the registry publicly: source.location is local and can contain a machine path. Use a workspace-relative location for checked-in records when feasible.

2. Collect compatibility hints:

       python -m skill_migration assess upstream-skill-name

   The report is written to assessments/<id>.json. Findings are heuristic and never approve compatibility, license, or tool equivalence. Inspect all resources and scripts yourself.

3. Complete license, Codex overlap, and prior-work reviews. Update source.license_files with collection-relative paths and SHA-256 hashes. Record evidence using [docs/registry.md](docs/registry.md). Set check outcomes and license_decision only after the evidence exists.

       python -m skill_migration record-evidence upstream-skill-name license evidence/license.json
       python -m skill_migration record-evidence upstream-skill-name codex_overlap evidence/overlap.json
       python -m skill_migration record-evidence upstream-skill-name prior_work evidence/prior.json

4. Stage the selected candidate:

       python -m skill_migration stage upstream-skill-name

   sources/<id>/<source-hash>/ preserves the original skill, licenses, and provenance. migrations/<slug>/ is the editable individual repository folder. Staging refuses to overwrite either area and records an adaptation blocker. It is an unchanged copy for review, not a completed migration. Assess and resolve instructions, runtime dependencies, and installation assumptions in this folder.

5. Adapt one skill completely. Update docs/migration.md, docs/compatibility.md, and docs/evaluation.md inside its output folder. Update the registry's assessments and blockers. Exercise realistic activation and non-activation prompts, failure behavior, and supporting scripts in isolated permitted resources. Capture actual outputs.

6. Get the current artifact fingerprint and record compatibility, functional, security, and final review evidence against it:

       python -m skill_migration fingerprint upstream-skill-name
       python -m skill_migration record-evidence upstream-skill-name functional evidence/functional.json

   Repeat record-evidence for compatibility, security, and review. Set status to migrated after adaptation, and to release-ready only after all release requirements are complete. Any output change invalidates artifact-bound evidence.

7. Validate and package:

       python -m skill_migration validate
       python -m skill_migration release-check upstream-skill-name
       python -m skill_migration package upstream-skill-name

   The ZIP is written to dist/codex-skill-<slug>-<artifact-hash-prefix>.zip. It contains only the reviewed individual repository folder. Extraction into a fresh directory produces a reviewable skills-only Codex plugin. Packages have stable file order and timestamps and refuse overwrite.

Global --root and --registry options go before the subcommand. Errors return a nonzero exit code. Run python -m skill_migration --help for the command surface.

## Project layout

- skill_migration/: command implementation; filesystem and evidence rules are shared by all commands.
- schemas/registry.schema.json: strict candidate and registry format.
- registry/candidates.json: candidate ledger, initially empty.
- assessments/: heuristic reports, created when requested.
- evidence/: reviewer reports and captured outputs, created during real work.
- sources/: ignored local upstream checkouts and preserved snapshots.
- migrations/: editable, reviewable individual repository outputs.
- dist/: ignored release ZIPs.
- tests/: synthetic fixture tests; fixtures never enter the real registry.
- docs/: architecture, release gates, workflow contract, and publication procedure.

The source and output paths must stay distinct. Do not inventory generated migrations as new sources.

## Limits and next step

The first real daily migration is complete: [Codex Gauge R&R](https://github.com/gkmraju/codex-skill-msa-gage-rr-builder), with native discovery, installed execution, independent evaluation and completed Windows/Linux CI. Discovery and selection remain evidence-driven agent work; the CLI does not automatically translate, rank or publish skills. Plugin marketplace installation is not verified.

Hashes establish file integrity and invalidate stale evidence. They cannot prove that reviewers actually exercised a workflow. Human review is still needed for licenses, semantic overlap, tool equivalence, binary/private contents, and claimed functional outcomes. Content scanning checks common patterns and cannot guarantee that all private information is absent.

See [release gates](docs/release-gates.md), [architecture](docs/architecture.md), and [publication procedure](docs/publication.md).

## Daily runs and Telegram

A daily 07:00 IST Codex app automation is active. See [daily workflow](docs/daily-workflow.md) and [Telegram setup/reporting](docs/telegram.md). [Today's completed run](reports/2026-10-13/completed-run.md) records the first published skill; the earlier journey remains historical. Reports distinguish completed migrations from assessed drafts and estimated impact from measured results.

Current discovery audience: software developers only, per the latest user instruction. The first published measurement skill predates that scope change.

## Curated queue

Daily work now uses the user-supplied [154-source CSV](registry/claude_only_skills_with_stars.csv). Run python -B scripts/next_candidate.py to see only the next row. Fresh Codex-equivalence screening and broad discovery are waived for this accepted list. See [queue workflow](docs/daily-workflow.md); progress is separate in registry/queue-state.json.
