<div align="center">

# 🧩 CODEX SKILL LAB

### Curated Claude skills. Rebuilt for Codex. Published for developers.

[![Queue: 154 sources](https://img.shields.io/badge/queue-154_sources-6366f1?style=flat-square)](registry/claude_only_skills_with_stars.csv)
[![Audience: developers](https://img.shields.io/badge/audience-software_developers-0891b2?style=flat-square)](docs/daily-workflow.md)
[![Daily: 07:00 IST](https://img.shields.io/badge/daily-07%3A00_IST-f59e0b?style=flat-square)](docs/daily-workflow.md)
[![Validate](https://github.com/gkmraju/codex-skill-creator/actions/workflows/validate.yml/badge.svg)](https://github.com/gkmraju/codex-skill-creator/actions/workflows/validate.yml)

[Source queue](registry/claude_only_skills_with_stars.csv) · [Workflow](docs/daily-workflow.md) · [Cloud setup](docs/cloud-runner.md) · [Current checkpoint](STATUS.md) · [Telegram](docs/telegram.md)

</div>

---

## One queue. One workflow. One schedule.

Work through the manually curated CSV **from top to bottom**. Pick the next unused row, recreate one selected skill for Codex, and publish it in an actual upstream fork containing the converted skill and its supporting resources.

The queue is already screened by the user. Its original order and approximate star counts are preserved.

```mermaid
flowchart LR
    A["Next unused CSV row"] --> B["Select a developer skill"]
    B --> R{"Reviewed recipe?"}
    R -->|Yes| C["Reconstruct Codex conversion"]
    R -->|No| M["Telegram · manual adaptation"]
    C --> D["Test and verify installation"]
    D --> E["Create upstream fork"]
    E --> F["Publish and pass CI"]
    F --> G["Mark used · Telegram report"]
```

## What happens each day

| Stage | Result |
| :--- | :--- |
| **Pick** | One pending or resumable row; no repeated discovery |
| **Convert** | Reviewed Python recipe reconstructs Codex instructions and resources |
| **Verify** | License/provenance, actual behavior and release evidence |
| **Fork & publish** | gkmraju/codex-skill-<slug>, source lineage retained, successful CI |
| **Record** | Durable queue progress and a compact Telegram report |

A row becomes **completed only after publication and successful CI**. Unsupported conversions stay unfinished and request manual intervention through Telegram. Repaired rows resume from their checkpoint.

## Run locally

Python 3.10+ is required for the queue and conversion tooling.

```text
python -m pip install -r requirements.txt
python -B scripts/next_candidate.py next
```

Start the selected row with its actual skill path:

```text
python -B scripts/next_candidate.py mark 2 in-progress --skill-path skills/example
```

After the conversion gates, real fork publication and CI pass:

```text
python -B scripts/next_candidate.py mark 2 completed --candidate source-skill-id --publication evidence/publication/example.json
```

See the [workflow](docs/daily-workflow.md) for skipped/blocked rows and publication details.

## A small, durable workspace

| Path | Purpose |
| :--- | :--- |
| [registry/claude_only_skills_with_stars.csv](registry/claude_only_skills_with_stars.csv) | Original 154-source queue |
| [registry/queue-state.json](registry/queue-state.json) | Used, skipped, blocked and resumable rows |
| [registry/queue-policy.json](registry/queue-policy.json) | Accepted screening and CSV fingerprint |
| [registry/candidates.json](registry/candidates.json) | Current conversion and evidence ledger |
| migrations/ | Reviewed single-skill packages |
| reports/ | Concise current run reports |
| [archive/](archive/README.md) | Recoverable historical work; excluded from daily context |

## Runs on GitHub. No LLM required.

One Python workflow requests a daily run at **07:00 IST** on GitHub-hosted Ubuntu.
Your PC and Codex desktop app can be off. No OpenAI key or model calls are needed.
GitHub scheduling can be delayed; exact start times are not guaranteed.

Python handles the CSV, pinned source checks, reviewed replacement recipes, behavior tests,
actual forks, successful CI, durable checkpoints and Telegram reporting. A new unsupported
skill needs a manual adaptation/review and recipe before automatic publication.
The initial recipe reproduces the previously published animation skill; it does not approve
unreviewed remaining rows. A daily release is a target, not a guarantee.

[Setup, secrets and manual intervention](docs/cloud-runner.md) ·
[Daily GitHub workflow](.github/workflows/daily-migration.yml)

## Telegram delivery

GitHub runs use encrypted Actions secrets. The ignored .env.telegram file remains available for local use. The existing **CODEX SKILL LAB** report includes the skill, developer benefit, essential verification, measured duration and repository link.

[Template and sender](skill_migration/telegram.py) · [Configuration](docs/telegram.md)

## Verification

```text
python -B scripts/verify.py
```

Control-project tests check queue progression, validation, evidence and reporting. Each converted skill also needs its own behavioral/install checks and successful CI.

Source authors retain attribution. Applicable licenses and immutable source revisions accompany every derivative. Historical work is preserved in the [archive](archive/README.md).

Every published skill gets the same README polish: [README standard](docs/skill-readme.md) · [Reusable template](templates/skill-repository-readme.md).
