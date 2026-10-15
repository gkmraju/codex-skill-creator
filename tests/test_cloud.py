import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from skill_migration import cloud
from skill_migration import tool as t


class CloudTests(unittest.TestCase):
    def setUp(self):
        from test_queue import QueueTests
        fixture = QueueTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.root = fixture.root
        t.write_json(self.root / "registry/conversion-recipes.json", {"schema_version": 1, "recipes": []})
        t.write_json(self.root / "registry/cloud-state.json", {"schema_version": 1, "days": {}})

    def result(self, **changes):
        result = {"schema_version": 1, "date": cloud.date_ist(), "started_at": 0,
            "base_commit": os.environ.get("GITHUB_SHA", "local"), "run_id": "local",
            "selected": cloud.queue.next_row(self.root), "status": "intervention",
            "checks": [], "reason": "No reviewed Python recipe"}
        result.update(changes)
        return result

    def test_unknown_recipe_reports_and_keeps_current_row(self):
        class Public:
            def api(self, path):
                return {"html_url": "https://github.com/example/first"}
        result = cloud.evaluate(self.root, Public())
        self.assertEqual(result["status"], "intervention")
        self.assertIn("No reviewed", result["reason"])
        with patch.object(cloud, "publication") as publish:
            cloud.finalize(self.root, result)
        publish.assert_not_called()
        selected = cloud.queue.next_row(self.root)
        self.assertEqual(selected["csv_row"], 2)
        self.assertEqual(selected["progress"]["status"], "in-progress")

    def test_missing_source_is_intervention_not_completed(self):
        class Missing:
            def api(self, path):
                return None
        result = cloud.evaluate(self.root, Missing())
        self.assertIn("404", result["reason"])
        cloud.finalize(self.root, result)
        self.assertEqual(cloud.queue.next_row(self.root)["csv_row"], 2)

    def test_stale_queue_result_cannot_publish(self):
        result = self.result()
        cloud.queue.mark(self.root, 2, "skipped", reason="Synthetic unavailable source")
        with self.assertRaisesRegex(ValueError, "Stale"):
            cloud.finalize(self.root, result)

    def test_completed_day_never_repeats_even_explicit_retry(self):
        t.write_json(self.root / "registry/cloud-state.json", {"schema_version": 1,
            "days": {cloud.date_ist(): {"status": "published"}}})
        with patch.dict(os.environ, {"RETRY_TODAY": "true"}):
            self.assertFalse(cloud.plan(self.root))

    def test_intervention_day_requires_explicit_retry(self):
        t.write_json(self.root / "registry/cloud-state.json", {"schema_version": 1,
            "days": {cloud.date_ist(): {"status": "intervention"}}})
        with patch.dict(os.environ, {"RETRY_TODAY": "false"}):
            self.assertFalse(cloud.plan(self.root))
        with patch.dict(os.environ, {"RETRY_TODAY": "true"}):
            self.assertTrue(cloud.plan(self.root))

    def test_changed_artifact_cannot_reuse_review(self):
        from test_migration import MigrationTests
        fixture = MigrationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.ready()
        t.write_json(fixture.root / "registry/candidates.json", fixture.data)
        recipe = {"candidate_id": fixture.c["id"], "repository": fixture.c["source"]["origin"],
            "revision": fixture.c["source"]["revision"],
            "artifact_sha256": t.tree_sha(fixture.root / fixture.c["artifact"])}
        cloud.candidate_for(fixture.root, recipe)
        (fixture.root / fixture.c["artifact"] / "README.md").write_text("changed")
        with self.assertRaisesRegex(ValueError, "artifact changed"):
            cloud.candidate_for(fixture.root, recipe)

    def test_failed_behavior_check_refuses_recipe(self):
        recipe = {"artifact_sha256": "a" * 64, "checks": [
            {"name": "behavior", "scope": "behavior", "argv": ["python", "check.py"]}]}
        artifact = self.root / "artifact"
        artifact.mkdir()
        class Failure:
            returncode = 1
            stdout = b"failed behavior"
            stderr = b""
        with patch.object(cloud, "candidate_for", return_value={"artifact": "artifact", "slug": "test"}), \
             patch.object(cloud, "verify_source"), patch.object(t, "tree_sha", return_value="a" * 64), self.assertRaisesRegex(ValueError, "check failed"):
            cloud.evaluate_recipe(self.root, recipe, None, run_command=lambda *a, **k: Failure())

    def test_private_error_details_are_not_reported(self):
        for message in [r"bad C:\Users\Name\secret", "ghp_" + "a" * 40,
                        "https://api.telegram.org/bot12345:secret/sendMessage"]:
            self.assertNotEqual(cloud.safe_reason(message), message)

    def test_unknown_source_is_not_counted_as_reviewed_skill(self):
        report = cloud.report(self.root, self.result())
        self.assertEqual(report["skills_reviewed"], 0)
        self.assertEqual(report["skills"], [])
        cloud.telegram.validate_report(report)

    def test_notification_requires_reservation_and_records_confirmation(self):
        result = self.result()
        with patch.dict(os.environ, {"GITHUB_RUN_ID": "local"}):
            cloud.finalize(self.root, result)
            with patch.object(cloud.telegram, "send", return_value=123) as send:
                cloud.notify(self.root)
                self.assertEqual(send.call_count, 1)
                with self.assertRaisesRegex(ValueError, "already attempted"):
                    cloud.notify(self.root)
                self.assertEqual(send.call_count, 1)
        state = t.read_json(cloud.run_folder(self.root, result) / "telegram-delivery.json")
        self.assertEqual(state["status"], "confirmed")

    def release_fixture(self):
        from test_migration import MigrationTests
        fixture = MigrationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.c["source"]["origin"] = "https://github.com/example/first"
        fixture.ready()
        t.write_json(fixture.root / "registry/candidates.json", fixture.data)
        for name in ["queue.csv", "queue-policy.json", "queue-state.json", "cloud-state.json"]:
            (fixture.root / "registry" / name).write_bytes((self.root / "registry" / name).read_bytes())
        recipe = {"candidate_id": fixture.c["id"], "repository": fixture.c["source"]["origin"],
            "revision": fixture.c["source"]["revision"],
            "artifact_sha256": t.tree_sha(fixture.root / fixture.c["artifact"]),
            "checks": [{"name": "synthetic behavior", "scope": "behavior"}]}
        t.write_json(fixture.root / "registry/conversion-recipes.json", {"recipes": [recipe]})
        result = self.result(status="ready", candidate_id=fixture.c["id"],
            artifact_sha256=recipe["artifact_sha256"],
            checks=[{"name": "synthetic behavior", "scope": "behavior", "exit_code": 0}])
        return fixture, result

    def test_only_observed_successful_publication_completes_row(self):
        fixture, result = self.release_fixture()
        repo = "https://github.com/gkmraju/codex-skill-demo"
        proof = {"repository_url": repo, "fork": True, "fork_parent_url": fixture.c["source"]["origin"],
            "artifact_sha256": result["artifact_sha256"], "commit_sha": "a" * 40,
            "ci_url": repo + "/actions/runs/123", "ci_conclusion": "success"}
        def observed(*args):
            t.write_json(cloud.run_folder(fixture.root, result) / "publication.json", proof)
            return proof
        with patch.object(cloud, "publication", side_effect=observed):
            final = cloud.finalize(fixture.root, result)
        self.assertEqual(final["status"], "published")
        self.assertEqual(cloud.queue.next_row(fixture.root)["csv_row"], 3)

    def test_ci_failure_keeps_row_unfinished(self):
        fixture, result = self.release_fixture()
        with patch.object(cloud, "publication", side_effect=t.Invalid("Skill CI did not pass")):
            final = cloud.finalize(fixture.root, result)
        self.assertEqual(final["status"], "intervention")
        self.assertEqual(cloud.queue.next_row(fixture.root)["csv_row"], 2)

    def test_prior_completed_skill_cannot_be_republished(self):
        fixture, result = self.release_fixture()
        state = t.read_json(fixture.root / "registry/queue-state.json")
        state["rows"]["99"] = {"status": "completed", "candidate_id": fixture.c["id"]}
        t.write_json(fixture.root / "registry/queue-state.json", state)
        with self.assertRaisesRegex(ValueError, "already completed"):
            cloud.require_unused(fixture.root, fixture.c)

    def test_existing_target_is_never_overwritten(self):
        from test_migration import MigrationTests
        fixture = MigrationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.ready()
        class Existing:
            operations = []
            def api(self, path, *args):
                if path == "/user":
                    return {"login": "gkmraju"}
                return {"fork": True, "parent": {"html_url": fixture.c["source"]["origin"]},
                    "private": False, "html_url": "https://github.com/gkmraju/codex-skill-demo",
                    "clone_url": "https://github.com/gkmraju/codex-skill-demo.git", "default_branch": "main"}
            def git(self, cwd, *args):
                self.operations.append(args[0])
                if args[0] == "ls-tree":
                    return b"existing-file.txt\n"
                return b""
        client = Existing()
        with self.assertRaisesRegex(ValueError, "Existing target differs"):
            cloud.publication(fixture.root, fixture.c, self.result(), client)
        self.assertNotIn("push", client.operations)
        self.assertNotIn("rm", client.operations)


if __name__ == "__main__":
    unittest.main()
