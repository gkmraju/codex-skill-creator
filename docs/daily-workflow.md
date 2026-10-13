# Daily migration workflow

Automation: Daily Codex skill migration.
Schedule: every day at 07:00 Asia/Calcutta (IST), using the Codex app heartbeat attached to this chat.

## Required daily deliverable

At least one impactful Claude-origin skill, fully adapted and usable in Codex, with real behavior and fresh-install verification, published in its own public gkmraju/codex-skill-<slug> repository. This is a target, not permission to claim unverified or unfinished work is complete.

Target software developers only for now. Select skills whose primary value is coding, debugging, testing, architecture, developer tooling, security/accessibility engineering, documentation or developer productivity. A non-developer workflow does not qualify merely because its implementation uses code. Continue searching public repositories, relevant news, and communities until a qualifying skill is found. There is no three-candidate cap. Record dated queries, stars, maintenance, source identity, and immutable revision.

Check official, installed, and publicly available Codex-compatible skills as well as prior gkmraju migrations. Compare semantics and workflow, not just names. Reject existing equivalents and already-Codex-ready duplicates. Record search scope and uncertainty; absence from a local catalog alone is insufficient.

## Conversion and publication

Review actual per-skill licenses, notices, scripts, runtime, dependencies, and redistribution rights. Create an independent repository containing only the selected skill and necessary supporting resources; a literal fork of a whole collection is not required. Preserve provenance, license, attribution, and modification history.

Adapt instructions, tools, scripts, templates, install steps, and failure handling deliberately. Exercise real activation, negative/failure scenarios, resources, outputs, and fresh installation. Fix observed failures and capture evidence. Complete all release-check gates and skill-specific CI before publication success is claimed.

The user authorizes creating the individual public repository, committing, pushing, and publishing after the gates pass, without a routine extra confirmation. Reuse suitable repositories, preserve remote work, and never force-push or merge unrelated changes. Legal attestations, credential changes, unauthorized external operations, and modifications to installed/upstream skills remain outside scope.

If a candidate fails or has unavailable prerequisites, retain its rejection/blocker and continue searching when possible. A draft, assessment, structural check, queued CI, or partial adaptation does not count as the daily deliverable.

## Reporting and continuation

Update the registry, durable status, source revision, functional/install evidence, repository/commit, completed CI, measured timing scope, and dated report. Telegram gets a compact summary: outcome and skill, benefit/audience, essential verification, checked count and measured duration, and the public repository link. An unfinished run includes a concrete blocker/next step; it is never reported as a successful release.

Keep full scorecards and learning detail in the dated report rather than Telegram. Preserve work for continuation, and stay quiet on unchanged/non-actionable state. Tokens, destination ids, private names, and private outputs remain outside reports and Git.
