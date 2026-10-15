# Current checkpoint

Updated 2026-10-15. CSV row 4 is completed: animation-performance.

- Public upstream fork: https://github.com/gkmraju/codex-skill-animation-performance
- Source parent: https://github.com/emilkowalski/skills
- Published commit: 3d0f24923a762dff7a5d684fbc758fcce540f1f3
- Successful five-job CI: https://github.com/gkmraju/codex-skill-animation-performance/actions/runs/38748679532
- Verification: 3 installer tests, 3 browser scenarios, native Codex discovery and independent fix/audit-only checks passed. No physical-device/FPS claims.
- Queue: rows 2/3 blocked by authenticated 404; row 4 used; next row 5. Original 154-source CSV unchanged.
- Current reports: reports/2026-10-15; provenance and artifact-bound evidence recorded.
- Previous desktop schedule is superseded by the Python cloud migration below.

The active workflow remains CSV top-to-bottom, software developers only, no repeated equivalence search or star refresh. Preserve archived history and credentials. Current completion timing excludes earlier work and overnight interruption.

## Python cloud migration - 2026-10-15

Python-only runner implemented; no LLM/API dependency. The desktop automation is paused.
The GitHub cron is 01:30 UTC / 07:00 IST and remains gated by CLOUD_RUNNER_ENABLED until activation.
Existing publication and queue state above are preserved; the next row is still row 5.
Credential transfer was blocked by automatic approval review pending explicit authorization for
SKILL_PUBLISH_TOKEN, TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in this repository's Actions secrets.
See docs/cloud-runner.md for reviewed recipes, manual intervention, retries and remaining activation.
