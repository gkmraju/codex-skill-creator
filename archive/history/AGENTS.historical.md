# Project contract

For daily runs, start with docs/daily-workflow.md and python -B scripts/next_candidate.py. Load only the current checkpoint at the top of STATUS.md when needed; historical records are not startup context. README.md documents CLI operations.

The user authorized the initial control-project commit and push to gkmraju/codex-skill-creator. The user authorizes publishing a fully verified selected skill in a separate public gkmraju/codex-skill-<slug> repository once the documented gates pass; future work targets software developers only and uses the user-curated CSV queue. The user explicitly accepted its Claude-only/non-portable screening; do not repeat public/installed Codex-equivalence searches or broad discovery for these rows. Telegram journey reports to the configured destination are authorized when .env.telegram is enabled; keep credentials and receipts private. Preserve upstream and installed skill files.

For registry, evidence, or gate changes, read docs/registry.md and docs/release-gates.md. For module design, read docs/architecture.md. For publication planning, read docs/publication.md. For daily runs or outward reports, read docs/daily-workflow.md and docs/telegram.md.

Verify changed behavior through the command interface with isolated fixtures. Run the documented local checks before handoff and record actual results, skips, and unresolved work in STATUS.md. Structural checks and synthetic tests are separate from functional acceptance of real skills.

Preserve existing work. Never infer license permission, tool equivalence, prior migration, CI success, or release status from a status field.
