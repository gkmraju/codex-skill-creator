# Compact Telegram report

Credentials stay in the ignored .env.telegram file. Existing configured values and delivery receipts are preserved. Template and sender: skill_migration/telegram.py; message header: CODEX SKILL LAB.

Preview/send an actual dated run JSON:

    python -B -m skill_migration.telegram reports/YYYY-MM-DD/run.json --preview reports/YYYY-MM-DD/telegram-preview.html
    python -B -m skill_migration.telegram reports/YYYY-MM-DD/run.json --send

Use a unique run_id and measured duration with its scope. The report includes the actual skill/outcome, software-developer benefit, essential verification and public fork link. Keep detailed evidence in files, not the outward message.

Full report JSON retains the sender's required fields: run_id, date, duration_seconds, measurement_scope, next_step, repositories_discovered, skills_reviewed, migrations_completed and skills. Each skill records name/outcome, usefulness/audience, impact with evidence, changes, validation, limitations, learning and HTTPS links. No discovery is performed by this queue workflow: repositories_discovered is zero unless actual discovery occurred; reviewed count is the number of distinct actual skill decisions.

Published entries require publication.repository_url, commit_sha, ci_conclusion=success and matching ci_url from actual inspected results. The queue's publication record additionally verifies fork metadata and artifact/source identity before marking used. Presence of fields alone is not proof of external facts.

Delivery requires --send and enabled valid env configuration. Credentials/destination IDs are never printed. Ignored evidence/telegram/ receipts prevent blind retries after uncertain delivery; inspect an existing attempt before retrying. Archived historical reports remain historical.

A pending or blocked conversion is reported as unfinished. Future reports target software developers; estimated impact is never presented as measured adoption or savings.
