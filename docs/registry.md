# Candidate and evidence format

schemas/registry.schema.json is the authoritative JSON Schema (Draft 2020-12). Unknown properties are rejected. Identifiers and slugs are lowercase hyphenated names, at most 63 characters. The registry has schema_version: 1 and a candidates array.

Each candidate records:

- id and slug, status, blockers, and a workspace-relative artifact path or null.
- source.collection, location, origin, skill_path, revision, attribution, sha256, license_files, and license_decision.
- assessment entries for format, resources, platform, tools, runtime, installation, and license. Each has status unresolved/compatible/blocked plus explanatory notes.
- checks.codex_overlap and checks.prior_work, each pending/pass/fail.
- evidence entries with kind, path, sha256, and artifact_sha256.

source.sha256 hashes an ordered manifest of all skill-relative file names and SHA-256 hashes. It includes supporting files. license_files is a list of objects with path and sha256; paths are relative to the source collection and can include applicable root licenses and notices. License files are preserved byte-for-byte and checked during packaging. source.revision must name an immutable commit or version for release, not an unverified branch label.

source.location is a local checkout path. Other registry paths use forward slashes, are relative to their documented root, and reject traversal, reserved Windows names, nonportable characters, symlinks, and junctions. Duplicate source identities are compared by origin and skill_path, independent of revision; updates belong to the existing candidate.

States describe progress; they do not grant approval:

- discovered: inventoried, reviews unresolved.
- assessed: review findings or staged source; adaptation can remain pending.
- migrated: adaptation exists, not necessarily release-ready.
- release-ready: every release gate must pass.
- rejected: preserve reasons; staging is refused.

## Evidence reports

Create reports from actual reviews; record-evidence never fabricates them. All reports are JSON objects with:

    {
      "kind": "codex_overlap",
      "outcome": "pass",
      "reviewer": "Actual reviewer",
      "recorded_at": "2026-10-13T18:30:00+05:30",
      "summary": "Describe the actual comparison and decision.",
      "source_sha256": "<candidate source.sha256>",
      "source": {
        "origin": "<candidate source.origin>",
        "skill_path": "<candidate source.skill_path>",
        "revision": "<candidate source.revision>",
        "attribution": "<candidate source.attribution>",
        "sha256": "<candidate source.sha256>",
        "license_files": [
          {"path": "LICENSE", "sha256": "<actual file hash>"}
        ]
      },
      "references": ["<inspectable source, inventory, comparison, or report>"]
    }

The source object must exactly match the public fields of the candidate. This binds the report to identity, revision, source contents, and licenses. References must be nonempty but are not fetched automatically. Reviewers must inspect them.

The four artifact-bound kinds (compatibility, functional, security, review) additionally require artifact_sha256, equal to the fingerprint command's current result.

A functional report also requires environment and nonempty cases:

    "environment": "Actual Codex/runtime/OS/tool versions",
    "cases": [
      {
        "prompt": "Actual exercised request",
        "expected": "Acceptance criteria",
        "observed": "Actual result and limitations",
        "outcome": "pass",
        "outputs": [
          {"path": "evidence/captured-output.txt", "sha256": "<actual hash>"}
        ]
      }
    ]

Capture outputs as workspace-relative regular files. Output hashes are checked. Reports from fixtures are explicitly synthetic and do not prove functional operation of a real migrated skill.

Only passing reports can be attached as approval evidence. Failed findings belong in assessment notes and blockers, and their raw reports can remain in evidence/. Keep reports outside migrations/ so adding evidence does not alter the artifact fingerprint. After modifying a package, rerun applicable evaluation and replace artifact-bound reports; changing just the hash is not revalidation.

For file hashes:

    python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('sources/upstream/LICENSE').read_bytes()).hexdigest())"

No automatic schema upgrade or registry deletion is provided. Preserve history in Git and review edits.
