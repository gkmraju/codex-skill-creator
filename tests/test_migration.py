import contextlib
import copy
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from skill_migration import tool as t


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.collection = self.root / "upstream"
        self.skill = self.collection / "skills/demo"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("---\nname: demo\ndescription: Summarize supplied text.\n---\nRead [guide](references/guide.md).\n", encoding="utf-8")
        (self.skill / "references").mkdir()
        (self.skill / "references/guide.md").write_text("Use only supplied facts.\n", encoding="utf-8")
        (self.collection / "LICENSE").write_text("Synthetic test license, not upstream evidence.\n", encoding="utf-8")
        self.c = t.inventory(self.collection, "test", "https://example.org/test", "Synthetic fixture", "test-revision")[0]
        self.data = {"schema_version": 1, "candidates": [self.c]}
        t.write_json(self.root / "registry/candidates.json", self.data)

    def evidence(self, kind):
        digest = t.tree_sha(self.root / self.c["artifact"]) if kind in t.BOUND else None
        report = {"kind": kind, "outcome": "pass", "reviewer": "Synthetic test reviewer",
                  "recorded_at": "2026-10-13T12:00:00Z", "summary": "Synthetic gate fixture only.",
                  "source_sha256": self.c["source"]["sha256"], "source": t.public_source(self.c), "references": ["https://example.org/test"]}
        if digest:
            report["artifact_sha256"] = digest
        if kind == "functional":
            output = self.root / "evidence/output.txt"
            output.parent.mkdir(exist_ok=True)
            output.write_text("Synthetic observed output.\n", encoding="utf-8")
            report.update(environment="Synthetic environment", cases=[{
                "prompt": "Summarize supplied text.", "expected": "Only supplied facts.",
                "observed": "Synthetic observed output.", "outcome": "pass",
                "outputs": [{"path": "evidence/output.txt", "sha256": t.sha(output)}]}])
        p = self.root / f"evidence/{kind}.json"
        t.write_json(p, report)
        entry = {"kind": kind, "path": f"evidence/{kind}.json", "sha256": t.sha(p), "artifact_sha256": digest}
        self.c["evidence"] = [e for e in self.c["evidence"] if e["kind"] != kind] + [entry]
        return p

    def approve(self):
        self.c["source"]["license_files"] = [{"path": "LICENSE", "sha256": t.sha(self.collection / "LICENSE")}]
        self.c["source"]["license_decision"] = "allowed"
        self.c["checks"] = {"codex_overlap": "pass", "prior_work": "pass"}
        for kind in ("license", "codex_overlap", "prior_work"):
            self.evidence(kind)

    def ready(self):
        self.approve()
        t.stage(self.root, self.c)
        self.c["status"] = "release-ready"
        self.c["blockers"] = []
        self.c["assessment"] = {d: {"status": "compatible", "notes": "Synthetic review."} for d in t.DIMENSIONS}
        for kind in t.BOUND:
            self.evidence(kind)

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = t.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def test_inventory_leaves_approvals_pending(self):
        self.assertEqual([], t.schema_errors(self.data))
        self.assertEqual("unknown", self.c["source"]["license_decision"])
        self.assertEqual("pending", self.c["checks"]["codex_overlap"])

    def test_empty_registry_not_a_release(self):
        self.assertEqual([], t.validate(self.root, {"schema_version": 1, "candidates": []}))
        self.assertTrue(t.release_errors(self.root, self.c))

    def test_required_and_unknown_fields(self):
        del self.c["source"]["attribution"]
        self.c["unexpected"] = True
        self.assertTrue(t.schema_errors(self.data))

    def test_duplicate_ids_slugs_sources(self):
        self.data["candidates"].append(copy.deepcopy(self.c))
        errors = t.schema_errors(self.data)
        for field in ("id", "slug", "source"):
            self.assertTrue(any("Duplicate " + field in x for x in errors))

    def test_invalid_paths(self):
        for path in ("../escape", "C:/secret", "/absolute", "a\\b", "CON/file", "a/../b", "a./b"):
            self.c["artifact"] = path
            self.assertTrue(t.schema_errors(self.data), path)

    def test_missing_local_reference(self):
        (self.skill / "references/guide.md").unlink()
        self.assertTrue(t.skill_errors(self.skill))

    def test_reference_style_and_code_paths(self):
        with (self.skill / "SKILL.md").open("a") as f:
            f.write("\n[g]: references/missing.md\nUse \x60scripts/missing.py\x60.\n")
        self.assertEqual(2, len(t.skill_errors(self.skill)))

    def test_invalid_and_duplicate_yaml(self):
        for body in ("name: [bad", "name: demo\nname: other\ndescription: text"):
            (self.skill / "SKILL.md").write_text("---\n" + body + "\n---\nWork.\n")
            self.assertTrue(t.skill_errors(self.skill))

    def test_external_links_do_not_require_network(self):
        with (self.skill / "SKILL.md").open("a") as f:
            f.write("\n[docs](https://example.org/docs)\n")
        self.assertEqual([], t.skill_errors(self.skill))

    def test_symlink_escape(self):
        try:
            (self.skill / "references/link").symlink_to(self.root, target_is_directory=True)
        except OSError:
            self.skipTest("OS does not permit unprivileged symlinks")
        with self.assertRaises(t.Invalid):
            t.tree_sha(self.skill)

    def test_case_collision(self):
        (self.skill / "Case.txt").write_text("one")
        (self.skill / "case.txt").write_text("two")
        if len(list(self.skill.glob("*ase.txt"))) < 2:
            self.skipTest("Case-insensitive filesystem")
        with self.assertRaises(t.Invalid):
            t.tree_sha(self.skill)

    def test_private_files(self):
        (self.skill / ".env").write_text("SYNTHETIC=test\n")
        with self.assertRaises(t.Invalid):
            t.tree_sha(self.skill)

    def test_assessment_preserves_source_and_status(self):
        digest = t.tree_sha(self.skill)
        report = t.assess(self.c)
        self.assertEqual(digest, t.tree_sha(self.skill))
        self.assertEqual("discovered", self.c["status"])
        self.assertIn("Heuristic", report["notice"])

    def test_changed_source(self):
        (self.skill / "references/guide.md").write_text("Changed")
        with self.assertRaises(t.Invalid):
            t.assess(self.c)

    def test_stage_requires_selection_evidence(self):
        with self.assertRaises(t.Invalid):
            t.stage(self.root, self.c)
        self.assertFalse((self.root / "migrations").exists())

    def test_status_alone_does_not_pass(self):
        self.c["status"] = "release-ready"
        self.c["source"]["license_decision"] = "allowed"
        self.c["checks"] = {"codex_overlap": "pass", "prior_work": "pass"}
        self.assertTrue(t.release_errors(self.root, self.c))

    def test_stage_preserves_snapshot_and_resources(self):
        self.approve()
        digest = t.tree_sha(self.skill)
        folder = t.stage(self.root, self.c)
        self.assertEqual(digest, t.tree_sha(self.skill))
        self.assertEqual(digest, t.tree_sha(folder / "skills/demo"))
        self.assertEqual(digest, t.tree_sha(self.root / "sources/test-demo" / digest / "skill"))
        self.assertEqual("assessed", self.c["status"])
        self.assertEqual([], t.artifact_errors(self.root, self.c))
        with self.assertRaises(t.Invalid):
            t.stage(self.root, self.c)

    def test_evidence_tampering(self):
        self.approve()
        (self.root / "evidence/license.json").write_text("{}")
        self.assertTrue(t.selection_errors(self.root, self.c))

    def test_functional_output_tampering(self):
        self.ready()
        (self.root / "evidence/output.txt").write_text("tampered")
        self.assertTrue(any("output hash" in x for x in t.release_errors(self.root, self.c)))

    def test_functional_evidence_requires_cases(self):
        self.ready()
        p = self.root / "evidence/functional.json"
        r = t.read_json(p)
        r["cases"] = []
        t.write_json(p, r)
        next(e for e in self.c["evidence"] if e["kind"] == "functional")["sha256"] = t.sha(p)
        self.assertTrue(any("exercised cases" in x for x in t.release_errors(self.root, self.c)))

    def test_unresolved_assessments_and_blockers(self):
        self.ready()
        self.c["blockers"] = ["Unknown equivalence"]
        self.c["assessment"]["runtime"]["status"] = "unresolved"
        errors = t.release_errors(self.root, self.c)
        self.assertTrue(any("Unresolved blockers" in x for x in errors))
        self.assertTrue(any("runtime:" in x for x in errors))

    def test_artifact_changes_invalidate_evidence(self):
        self.ready()
        self.assertEqual([], t.release_errors(self.root, self.c))
        with (self.root / self.c["artifact"] / "skills/demo/SKILL.md").open("a") as f:
            f.write("\nChanged instructions.\n")
        self.assertTrue(any("stale" in x for x in t.release_errors(self.root, self.c)))

    def test_repeatable_package_and_contents(self):
        self.ready()
        archive = t.package(self.root, self.c)
        first = archive.read_bytes()
        with zipfile.ZipFile(archive) as z:
            self.assertIn("skills/demo/references/guide.md", z.namelist())
            self.assertIn(".codex-plugin/plugin.json", z.namelist())
            self.assertFalse(any(n.startswith(("sources/", "evidence/")) for n in z.namelist()))
            self.assertFalse(any(str(self.root).encode() in z.read(n) for n in z.namelist()))
        with self.assertRaises(t.Invalid):
            t.package(self.root, self.c)
        archive.unlink()
        self.assertEqual(first, t.package(self.root, self.c).read_bytes())

    def test_private_paths_and_unexpected_package_files(self):
        self.ready()
        folder = self.root / self.c["artifact"]
        (folder / "docs/migration.md").write_text("C:\\Users\\Private\\project")
        self.assertTrue(t.artifact_errors(self.root, self.c))
        (folder / "private.txt").write_text("private")
        self.assertTrue(t.artifact_errors(self.root, self.c))

    def test_cli_duplicate_preserves_registry(self):
        self.assertEqual(0, self.cli("validate")[0])
        before = (self.root / "registry/candidates.json").read_bytes()
        code, out, err = self.cli("inventory", str(self.collection), "--collection-id", "test",
                                  "--origin", "https://example.org/test", "--attribution", "Synthetic")
        self.assertEqual(1, code)
        self.assertIn("Duplicate", err)
        self.assertEqual(before, (self.root / "registry/candidates.json").read_bytes())
        self.assertEqual(1, self.cli("assess", "missing")[0])

    def test_cli_end_to_end(self):
        self.approve()
        t.write_json(self.root / "registry/candidates.json", self.data)
        self.assertEqual(0, self.cli("assess", self.c["id"])[0])
        self.assertEqual(0, self.cli("stage", self.c["id"])[0])
        self.c = t.read_json(self.root / "registry/candidates.json")["candidates"][0]
        self.c["status"] = "release-ready"
        self.c["blockers"] = []
        self.c["assessment"] = {d: {"status": "compatible", "notes": "Synthetic review."} for d in t.DIMENSIONS}
        for kind in t.BOUND:
            self.evidence(kind)
        t.write_json(self.root / "registry/candidates.json", {"schema_version": 1, "candidates": [self.c]})
        self.assertEqual(0, self.cli("validate")[0])
        self.assertEqual(0, self.cli("release-check", self.c["id"])[0])
        self.assertEqual(0, self.cli("package", self.c["id"])[0])

    def test_license_hash_mismatch_prevents_stage(self):
        self.approve()
        (self.collection / "LICENSE").write_text("Changed license")
        with self.assertRaises(t.Invalid):
            t.stage(self.root, self.c)
        self.assertFalse((self.root / "migrations/demo").exists())

    def test_changed_identity_invalidates_selection_evidence(self):
        self.approve()
        self.c["source"]["origin"] = "https://example.org/different"
        self.assertTrue(t.selection_errors(self.root, self.c))

    def test_altered_packaged_license_is_rejected(self):
        self.ready()
        (self.root / self.c["artifact"] / "licenses/0-LICENSE").write_text("Altered")
        self.assertTrue(any("altered license" in e for e in t.artifact_errors(self.root, self.c)))

    def test_frontmatter_description_can_contain_dashes(self):
        (self.skill / "SKILL.md").write_text("---\nname: demo\ndescription: 'Use text --- summarize it.'\n---\nWork.\n")
        self.assertEqual([], t.skill_errors(self.skill))

    def test_non_passing_and_incomplete_reports_are_rejected(self):
        self.approve()
        p = self.root / "evidence/license.json"
        report = t.read_json(p)
        report["outcome"] = "fail"
        t.write_json(p, report)
        entry = next(e for e in self.c["evidence"] if e["kind"] == "license")
        entry["sha256"] = t.sha(p)
        self.assertTrue(t.selection_errors(self.root, self.c))

    def test_record_evidence_cli_rejects_incomplete_report(self):
        t.write_json(self.root / "evidence/incomplete.json", {"kind": "license"})
        self.assertEqual(1, self.cli("record-evidence", self.c["id"], "license", "evidence/incomplete.json")[0])

    def test_record_evidence_cli_hashes_actual_report(self):
        self.approve()
        t.write_json(self.root / "registry/candidates.json", self.data)
        self.assertEqual(0, self.cli("record-evidence", self.c["id"], "license", "evidence/license.json")[0])
        saved = t.read_json(self.root / "registry/candidates.json")["candidates"][0]
        entry = next(e for e in saved["evidence"] if e["kind"] == "license")
        self.assertEqual(t.sha(self.root / entry["path"]), entry["sha256"])

    def test_source_and_snapshot_overlap_rejected(self):
        source = self.root / "sources"
        source.mkdir()
        (source / "SKILL.md").write_text("---\nname: other\ndescription: Test.\n---\nWork.\n")
        (self.root / "LICENSE").write_text("Synthetic")
        self.c = t.inventory(self.root, "overlap", "https://example.org/test", "Synthetic", "rev")[0]
        # Select the source rooted exactly where snapshots would be created.
        candidates = t.inventory(self.root, "overlap", "https://example.org/test", "Synthetic", "rev")
        self.c = next(c for c in candidates if c["source"]["skill_path"] == "sources")
        self.c["source"]["license_files"] = [{"path": "LICENSE", "sha256": t.sha(self.root / "LICENSE")}]
        self.c["source"]["license_decision"] = "allowed"
        self.c["checks"] = {"codex_overlap": "pass", "prior_work": "pass"}
        for kind in ("license", "codex_overlap", "prior_work"):
            self.evidence(kind)
        with self.assertRaises(t.Invalid):
            t.stage(self.root, self.c)


if __name__ == "__main__":
    unittest.main()
