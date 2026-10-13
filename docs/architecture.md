# Architecture and decisions

Confirmed inputs are the fresh-session request and the user's pasted prior conversation, with the original chat inspected read-only. The workspace had only an initialized, uncommitted Git repository. No previous scaffold was recovered. Historical star counts, license assertions, and functional claims were not adopted as current facts.

The user selected gkmraju/codex-skill-creator as the control repository on 2026-10-13, replacing the earlier planned registry name. The current repository model is one control repository, gkmraju/codex-skill-creator, plus gkmraju/codex-skill-<slug> for each approved skill. GitHub Issues and default triage labels were approved for the later hosted workflow. Telegram details are deferred. Installed Matt Pocock skills are available; this phase uses codebase-design and writing-for-agents guidance, plus Codex skill-creator and official OpenAI documentation.

## Module design

The command-line module is the interface used by operators and end-to-end tests. It hides inventory merging, path checks, fingerprints, evidence checks, source preservation, and ZIP creation. Validation, staging, and packaging share the same release rules so changing a rule has locality. Python functions return findings for testable internal decisions; the command layer renders results and owns registry updates.

There is one filesystem implementation, so no speculative database, queue, provider interface, or repository abstraction is introduced. JSON plus atomic writes is sufficient for one local operator. Concurrent writers are not supported; use one command at a time and review changes in Git.

Staging copies intact source resources and then requires a deliberate adaptation step. A generic string replacement from Claude to Codex would risk false tool equivalence and is intentionally outside this implementation. Assessments surface markers without certifying behavior.

Evidence stays outside the package. Its file hash binds the report, the source identity binds its subject, and artifact fingerprints invalidate downstream reviews after output changes. Final packages include only reviewed skill contents, licenses, docs, plugin metadata, and public provenance.

## Outstanding phases

- Select and check out a real upstream source collection.
- Read-only GitHub discovery with recorded query, capture time, stars, commit identity, and license scope; rank candidates without treating stars as approval.
- Real semantic overlap and prior-work reviews.
- Complete a first real migration with behavioral evidence and installation acceptance.
- Add per-skill scenario tests suited to that skill rather than generic placeholder tests.
- Review source metadata and private information before publishing the registry.
- Publish the control repository under the current authorization; individual skill releases require their own complete gates.
- Add scheduling and Telegram reporting after credentials/destination are supplied through an appropriate secure connection.

The initial control-repository publication is authorized. No scheduled job or Telegram integration is running.
