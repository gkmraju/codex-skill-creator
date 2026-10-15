# Python-only GitHub runner

The active scheduler is [.github/workflows/daily-migration.yml](../.github/workflows/daily-migration.yml).
It requests one run daily at **01:30 UTC / 07:00 IST**, on GitHub-hosted Ubuntu.
Activation requires the repository Actions variable CLOUD_RUNNER_ENABLED=true after secrets and tests pass.
Until then scheduled jobs are gated off; manual dry_run evaluates without side effects.
The PC and Codex desktop app can be off. No OpenAI key, model call, LLM tokens or desktop login is used.
GitHub can delay scheduled jobs; the cron is a requested start, not an exact-time guarantee.

## What is automatic

Python reads the original CSV in order and checks the current source. Without an existing recipe,
[autoconvert.py](../skill_migration/autoconvert.py) discovers a supported developer skill, pins the
source revision, recognizes complete MIT notices and generates the actual Codex package from upstream
Markdown. It normalizes provider metadata, preserves references and source attribution, and generates
project installation, dependency locks, bounded runtime tests, a polished README and individual CI.
It installs the trusted locked dependency in a fresh isolated environment and exercises the generated
package checks before enforcing artifact-bound release gates. Existing recipes remain optional.
A separate job can create the actual fork, push the exact reviewed bytes, wait for successful skill CI,
mark the row completed, commit the queue/report and send the compact Telegram message.

A repository returning HTTP 404 on two checks is automatically recorded blocked, with its URL and
reason preserved. The runner immediately advances in original CSV order, bypassing up to ten
unavailable rows per run; it defers the next row until tomorrow if that cap is reached.
Telegram summarizes bypassed rows. The original CSV is never changed.
Authentication, rate-limit, network and server errors stop rather than bypassing sources.
Unsupported source adapters/licenses, changed hashes, failed tests, fork conflicts and unsuccessful CI still produce
**manual intervention**, not a completed migration. That current row stays in-progress.
Select Run workflow after repair and enable retry_today to retry an unfinished day.
A completed publication is never repeated by this option. Concurrent runs are serialized.
A rerun of an old workflow commit cannot overwrite newer remote checkpoints.

## Automatic conversion coverage

The initial runtime adapters support **polars**, **networkx** and **simpy**, independent of a specific
repository URL. Source folders must contain bounded Markdown resources only; executable upstream
helpers and provider-specific tool workflows are refused. Skill discovery is restricted to the
selected CSV repository; no equivalence search or star refresh occurs.

The generated tests exercise complete resource/notice installation and refusal paths plus a bounded
library behavior case. They do not execute a model, measure reasoning quality, certify every upstream
example or claim human semantic review. Automated evidence explicitly records this scope.
Runtime locks and generated executable templates are trusted control-project code. New adapters can
be added with meaningful runtime cases; no finished per-repository conversion is required.

Evaluation sends a hashed ZIP of generated package/evidence data to a separate recording job.
The recording job rejects traversal, linked/duplicate members, changed hashes, existing output
collisions and source/row mismatches, then rechecks the release gates. It never executes downloaded
package code while holding publication credentials. Checkpoints commit the generated artifact and
its evidence alongside the queue state.

[conversion-recipes.json](../registry/conversion-recipes.json) is an optional legacy path for exact
previously reviewed conversions. The earlier animation recipe remains a regression check;
its completed row is never republished. Its recorded CRLF source checkout is reconstructed explicitly.

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

Renamed upstream URLs are followed only within HTTPS api.github.com. Fork lineage is verified by the immutable source repository ID and observed parent ID; publication evidence preserves both the CSV URL and resolved parent URL. Source redirects do not change the accepted CSV.
