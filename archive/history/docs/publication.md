# Later GitHub procedure

The user authorized committing and pushing the control project to gkmraju/codex-skill-creator on 2026-10-13. Individual skill releases and Telegram remain separate later work.

1. Inspect registry metadata, reports, captured outputs, package resources, and Git history for private information. Keep machine-specific locations local or use portable workspace-relative paths. Never commit credentials or source snapshots inadvertently.
2. Run the complete local checks. Finish all real candidate gates before distributing any individual skill; an empty control registry does not claim skill acceptance. Commit only reviewed project files.
3. When publication is explicitly authorized, reuse the existing gkmraju/codex-skill-creator and push the control repository. Configure GitHub Issues and the approved triage labels. Proposed labels: candidate, assessment, migration, blocked, release-review, duplicate, rejected. Exact default labels from the earlier setup were not recovered.
4. Wait for completed GitHub Actions results; queued runs are not evidence. Keep actual run URLs and results.
5. Extract each approved ZIP into a fresh folder; inspect it and create the separate gkmraju/codex-skill-<slug> repository. Preserve UPSTREAM.md, provenance.json, and applicable licenses/notices. Decide the licensing of original migration additions separately; the tool does not invent a project license or replace upstream licenses.
6. Add skill-specific tests and CI that exercise its actual resources, activation, behavior, and supported environments. Perform real plugin/skill installation acceptance. Commit, push, and wait for completed CI before a public release/tag.
7. Record repository URL, commit/tag, actual completed run results, and release outcome in the registry's evidence or a reviewed schema extension. Do not mark release-ready as synonymous with published.
8. Telegram reporting is a separate authorized integration once destination and credentials are available. Report verified outcomes and release links; keep tokens out of Git and packages.

There are no GitHub or Telegram mutation commands in the local tool.
