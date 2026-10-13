# Tooling verification

Local checks completed on 2026-10-13:
- Python 3.13.13 with PyYAML 6.0.3 and jsonschema 4.25.1.
- 34 tests ran: 32 passed, 2 skipped.
- Registry validation passed with zero real candidates.
- Syntax checks passed.
- JSON Schema self-validation, workflow configuration, and documentation links checked.

The skipped tests concern case-sensitive file collisions and creation of unprivileged symlinks on Windows. The configured Linux CI job is intended to exercise both.

Tests use synthetic sources and review evidence. They exercise inventory, assessment, evidence integrity, staging, release denial, and deterministic packaging. They do not validate a real skill's activation, behavior, or installation in Codex.

Raw logs are saved locally by scripts/verify.py and ignored by Git because they may contain host-specific paths. This summary reports actual observed results without publishing those paths.

GitHub Actions completed successfully on implementation commit 317f56988395abd13f4a9262c45feae2a86bb8db, on both ubuntu-latest and windows-latest. Completed run: https://github.com/gkmraju/codex-skill-creator/actions/runs/38407304142. This validates tooling, not any real skill's behavior.
