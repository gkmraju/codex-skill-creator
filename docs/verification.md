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

GitHub Actions configuration is present. Hosted results must be checked separately; no queued run is described as passing.
