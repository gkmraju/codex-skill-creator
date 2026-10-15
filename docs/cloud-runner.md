# Python-only GitHub runner

The active scheduler is [.github/workflows/daily-migration.yml](../.github/workflows/daily-migration.yml).
It requests one run daily at **01:30 UTC / 07:00 IST**, on GitHub-hosted Ubuntu.
Activation requires the repository Actions variable CLOUD_RUNNER_ENABLED=true after secrets and tests pass.
Until then scheduled jobs are gated off; manual dry_run evaluates without side effects.
The PC and Codex desktop app can be off. No OpenAI key, model call, LLM tokens or desktop login is used.
GitHub can delay scheduled jobs; the cron is a requested start, not an exact-time guarantee.

## What is automatic

Python reads the original CSV in order, checks the current repository, selects its reviewed recipe,
verifies the immutable source and original license hashes, reconstructs the reviewed replacement package
in a fresh directory, exercises its declared installation/behavior checks, and enforces existing release gates.
A separate job can create the actual fork, push the exact reviewed bytes, wait for successful skill CI,
mark the row completed, commit the queue/report and send the compact Telegram message.

Unknown recipes, inaccessible sources, changed hashes, failed tests, fork conflicts and unsuccessful CI
produce **manual intervention**, not a completed migration. The current row stays in-progress.
Select Run workflow after repair and enable retry_today to retry an unfinished day.
A completed publication is never repeated by this option. Concurrent runs are serialized.
A rerun of an old workflow commit cannot overwrite newer remote checkpoints.

## Conversion recipes

[registry/conversion-recipes.json](../registry/conversion-recipes.json) contains explicit, reviewed,
source-specific replacement recipes. This is a deterministic replay of an approved conversion, not
a semantic converter for arbitrary Claude instructions. A new source needs one manual adaptation
and review before Python can publish it. Unsupported rows are reported rather than mechanically renamed.

The initial animation-performance recipe reproduces the exact earlier conversion as a real regression
check. Its CSV row remains completed and is never republished by the daily runner.
There are no preapproved recipes for the remaining queue yet.
The earlier animation source fingerprints describe its CRLF Windows checkout. Its recipe explicitly
uses checkout_eol=crlf to reconstruct those same bytes on Linux before checking the recorded hashes;
the immutable Git revision is checked independently. New recipes default to LF. Existing provenance,
reviewed artifact bytes and published licenses remain unchanged.

To onboard the blocked row:

1. Verify the supplied repository URL/access. Preserve the accepted CSV/hash; corrections need explicit curation.
2. Select one developer skill and pin its commit, skill tree and applicable license hashes.
3. Adapt the single-skill package under migrations/ using docs/registry.md and docs/release-gates.md.
   Follow docs/skill-readme.md and the README template.
4. Record actual functional, compatibility, security and final-review evidence. Set release-ready only after all gates pass.
5. Add one recipe linking that candidate, source revision, complete artifact hash and explicit Python/Node checks.
   Include a behavior check; syntax/metadata checks alone are insufficient. Checks are trusted code reviewed in this control repository.
6. Commit/push the reviewed changes, then run the daily workflow with retry_today enabled.

Check a recipe without publishing:

    python -B -m skill_migration.cloud recipe-check --recipe animation-performance-v1

The browser recipe also requires Node, playwright@1.62.1 and its Chromium installation.
No agent invocation/semantic evaluation is claimed by these Python tests.
Historical exact-artifact review remains in the ledger; each cloud run rechecks its source and declared behaviors.

## Secrets and permissions

| Actions secret | Purpose |
| --- | --- |
| SKILL_PUBLISH_TOKEN | gkmraju GitHub credential permitted to fork, push workflow files and run/read skill CI |
| TELEGRAM_BOT_TOKEN | Existing report bot |
| TELEGRAM_CHAT_ID | Existing destination |

Publishing needs an account credential because the repository-scoped GITHUB_TOKEN cannot create and
write independent account forks. It should have only the required account access; a classic credential
requires repo and workflow scopes. Revocation/expiry requires replacing this secret.
The migration setup may transfer the existing authorized Git credential and Telegram values directly
to encrypted GitHub secrets; values are never written into source or printed.

The evaluation job receives neither publication nor Telegram credentials.
The recording job checks out trusted control code at the same commit; it downloads JSON results only,
and does not execute upstream or recipe test code. The standard GITHUB_TOKEN writes control checkpoints.
Fork CI receives no control-project secrets and must itself pass before completion.

## Reports, retries and recovery

Public outcomes, queue state and notification reservations are committed under reports/cloud/date/run-id/.
Raw test logs are short-lived Actions artifacts; credentials and destination receipts stay private.
The first checkpoint is pushed before Telegram delivery. A public reservation plus daily deduplication
prevents blind retries after uncertain delivery. Inspect Telegram and the run before any manual resend.
If delivery fails, Actions fails visibly and preserves the public report. GitHub/Telegram outages can
prevent delivery; GitHub's own failure notifications remain the fallback.
The desktop automation is paused after cloud activation, preserving its old configuration.
Local sources, credentials, installed skills and archived history remain untouched.
