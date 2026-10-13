# Telegram reporting

Credentials live in the ignored .env.telegram file. Fill TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (numeric destination or public @channel), then set TELEGRAM_ENABLED=true. Do not paste the bot token into chat or commit it. For a channel, add the bot with permission to post; for a private chat, start the bot before delivery.

Preview a real run report:

    python -m skill_migration.telegram reports/2026-10-13/run.json --preview reports/2026-10-13/telegram-preview.html

Send an explicitly authorized report to the configured destination:

    python -m skill_migration.telegram reports/2026-10-13/run.json --send

The default env is .env.telegram. --env .env selects a different ignored file if desired. Process environment values override file values; credentials are never printed by this tool.

## Report content

Use a dated JSON report with:
- run_id, date, measured duration_seconds, measurement_scope, next_step.
- repositories_discovered (repository discovery count, not skill count).
- skills_reviewed and migrations_completed, matching distinct skill outcomes.
- skills entries with name, outcome (rejected/deferred/migrated/release-ready), usefulness, audience, impact, impact_evidence, actual changes, validation, limitations, developer learning, and inspectable HTTPS links.

Expected impact must be identified as an estimate unless measured adoption/time-savings evidence exists. A staged or partly adapted candidate remains deferred and contributes zero completed migrations. State real workflow and installation limits. Keep host paths, private repository names, captured private outputs, credentials, and other sensitive information out of outward reports.

The renderer uses readable Telegram HTML formatting and escapes report text. It checks Telegram's sendMessage length limit before delivery. A local browser preview offers visual formatting, not proof of Telegram rendering.

Delivery needs explicit --send plus enabled valid configuration. Receipts under ignored evidence/telegram/ retain hashes, attempt status, and Telegram's confirmed message id; they do not store raw tokens or destination ids. Duplicate run ids to the same destination are refused. Transport failure can follow actual delivery, so the attempted receipt also prevents blind retries. Inspect the destination and receipt before manually retrying. Do not run concurrent writers against the same report.

Official API reference checked 2026-10-13: https://core.telegram.org/bots/api#sendmessage

## Compact outward format

The default renderer now keeps only the primary outcome/skill, benefit and audience, essential verification, checked count and measured run time, and link. Unfinished work shows a short blocker/next action. Rejected-candidate detail, separate impact scorecards, source popularity, and developer-learning sections stay in the full JSON/report.

A published outcome requires publication.repository_url for the individual gkmraju/codex-skill-<slug>, the actual 40-character commit_sha, successful ci_conclusion, and matching CI run URL. These fields must come from inspected actual results; their presence alone cannot prove the claims.

The daily job targets a complete public skill across all audiences and keeps searching without a fixed candidate cap. Independent single-skill repositories are authorized after verification gates pass.

Current audience filter: software developers only for future selections and reports. State the actual developer benefit. Preserve historical reports with their truthful original audience.
