# CSV → Codex → public fork

One fresh local run daily at 07:00 Asia/Calcutta. Software developers only.

## 1. Pick the next row

Run python -B scripts/next_candidate.py next. Only the first pending/in-progress row is returned. Original CSV order is authoritative; approximate stars are user supplied. Completed/skipped/blocked rows are bypassed.

Inspect only this repository to select one actual developer skill. Record its source-relative skill path and immutable commit. A collection gets one selected skill per CSV row. No eligible skill or redistributable license: record a concrete skipped/blocked reason and move to the next row.

Start/resume the selected row:

    python -B scripts/next_candidate.py mark 2 in-progress --skill-path skills/example

Replace row and path with actual values. Only the current row can be marked. No public/installed Codex-equivalence research, broad discovery or star refresh: user curation is accepted and recorded in registry/queue-policy.json.

## 2. Convert locally

Review the applicable license and actual source resources. Reuse skill_migration inventory/staging/evidence/validation tools for this selected skill only. See docs/registry.md and docs/release-gates.md as needed.

Bind the codex_overlap selection decision to the user-curated CSV row/hash; record accepted user screening without claiming independent absence. Check the local ledger for our own already-used source/path.

Adapt instructions, helpers, dependencies and installation for real Codex use. Exercise realistic supported behavior, failure paths and a fresh install. Record actual outputs and reviewer scope; structural checks alone do not establish usability.

Before the final artifact fingerprint, follow docs/skill-readme.md and templates/skill-repository-readme.md. Match the control README's polish with skill-specific benefits, tested installation/invocation, an example, verification and upstream/license attribution. Resolve placeholders and verify links/claims; include README quality in final review evidence.

## 3. Fork and publish

After local release gates pass, create an actual GitHub fork of the CSV repository with the chosen codex-skill-<slug> name. Verify fork=true and parent.html_url equals the source repository. Use the fork API through an available connector or the existing authenticated GitHub REST client; never expose credentials.

If a suitable fork already exists, inspect it and preserve remote work. GitHub may reject a fork creation; record the actual blocker instead of silently substituting an unrelated repository.

Clone the fork into an ignored publication checkout. Commit the reviewed single-skill package over the inherited tree, removing unrelated copied source files only from this checked-out fork. Preserve fork history and source notices; never force-push or change the upstream repository. Confirm committed package bytes match the reviewed files. Push and wait for completed successful skill-specific CI.

Capture observed publication metadata in evidence/publication/<slug>.json: repository_url, commit_sha, ci_url, ci_conclusion=success, artifact_sha256, fork=true and fork_parent_url. These values must come from actual inspected results.

Mark used only then:

    python -B scripts/next_candidate.py mark 2 completed --candidate source-skill-id --publication evidence/publication/example.json

The helper checks current-row identity, source, local release gates, fork metadata, artifact fingerprint and CI evidence before advancing. It validates supplied evidence; it does not independently fetch GitHub.

## 4. Report and stop

Update one short checkpoint and send the enabled compact Telegram report. No secrets, destination IDs or private logs in Git. Stop after one successfully published skill. Incomplete work remains in-progress/blocked with a precise next action; resume it in the next fresh run.

For skip/block:

    python -B scripts/next_candidate.py mark 2 skipped --reason "No developer skill in this repository"

Run operations sequentially; do not launch overlapping writers. The single schedule starts projectless, so every shell command explicitly sets workdir to the migration workspace. No historical context replay. Archive is consulted only for an explicit recovery task.
