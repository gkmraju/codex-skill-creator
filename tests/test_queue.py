import contextlib
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1]/"scripts/next_candidate.py"
spec = importlib.util.spec_from_file_location("queue_helper", PATH)
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        registry = self.root/"registry";registry.mkdir()
        self.csv = registry/"queue.csv"
        self.csv.write_bytes(b"Name,Approx_Stars,GitHub_Link\r\nFirst,100,https://github.com/example/first\r\nSecond,200,https://github.com/example/second\r\n")
        self.write("queue-policy.json", {"csv_file":"registry/queue.csv","csv_sha256":hashlib.sha256(self.csv.read_bytes()).hexdigest(),"audience":"software developers only"})
        self.write("queue-state.json", {"schema_version":1,"rows":{}})
        self.write("candidates.json", {"schema_version":1,"candidates":[]})
    def write(self, name, value):
        (self.root/"registry"/name).write_text(json.dumps(value),encoding="utf-8")
    def test_original_order_wins_over_star_counts(self):
        self.assertEqual(queue.next_row(self.root)["name"],"First")
    def test_in_progress_resumes_and_skip_advances(self):
        queue.mark(self.root,2,"in-progress",skill_path="skills/example")
        self.assertEqual(queue.next_row(self.root)["progress"]["selected_skill_path"],"skills/example")
        queue.mark(self.root,2,"skipped",reason="No eligible developer skill")
        self.assertEqual(queue.next_row(self.root)["csv_row"],3)
    def test_cannot_modify_later_row_or_skip_without_reason(self):
        original=(self.root/"registry/queue-state.json").read_bytes()
        for row,reason in [(3,"Unavailable"),(2,"")]:
            with self.assertRaises(ValueError):
                queue.mark(self.root,row,"blocked",reason=reason)
        self.assertEqual((self.root/"registry/queue-state.json").read_bytes(),original)
    def test_completed_without_release_or_publication_does_not_advance(self):
        with self.assertRaises(ValueError):
            queue.mark(self.root,2,"completed")
        with self.assertRaisesRegex(ValueError,"Candidate"):
            queue.mark(self.root,2,"completed",candidate_id="missing",publication_path="evidence/fake.json")
        self.assertEqual(queue.next_row(self.root)["csv_row"],2)
    def test_changed_csv_cannot_use_old_acceptance(self):
        with self.csv.open("ab") as handle:handle.write(b"\n")
        with self.assertRaisesRegex(ValueError,"CSV changed"):
            queue.next_row(self.root)
    def test_exhausted_queue_does_not_discover(self):
        queue.mark(self.root,2,"skipped",reason="No eligible skill")
        queue.mark(self.root,3,"blocked",reason="No license")
        self.assertEqual(queue.next_row(self.root)["status"],"queue-exhausted")
    def test_cli_failure_leaves_state_unchanged(self):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            code=queue.main(["--root",str(self.root),"mark","2","completed"])
        self.assertEqual(code,1)
        self.assertEqual(queue.next_row(self.root)["csv_row"],2)

    def test_completion_requires_matching_fork_ci_and_reviewed_artifact(self):
        # Synthetic release fixture; does not assert a real publication.
        from test_migration import MigrationTests
        from skill_migration import tool
        fixture=MigrationTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.c["source"]["origin"]="https://github.com/example/first"
        fixture.ready()
        tool.write_json(fixture.root/"registry/candidates.json",{"schema_version":1,"candidates":[fixture.c]})
        for name in ["queue.csv","queue-policy.json","queue-state.json"]:
            (fixture.root/"registry"/name).write_bytes((self.root/"registry"/name).read_bytes())
        repo="https://github.com/gkmraju/codex-skill-demo"
        proof={"repository_url":repo,"commit_sha":"a"*40,"ci_conclusion":"success","ci_url":repo+"/actions/runs/123",
               "artifact_sha256":tool.tree_sha(fixture.root/fixture.c["artifact"]),"fork":True,"fork_parent_url":"https://github.com/example/first"}
        path=fixture.root/"evidence/publication/demo.json"
        for field,value in [("fork",False),("fork_parent_url","https://github.com/example/other"),("ci_conclusion","queued"),("artifact_sha256","0"*64)]:
            bad=dict(proof);bad[field]=value;tool.write_json(path,bad)
            with self.subTest(field=field),self.assertRaises(ValueError):
                queue.mark(fixture.root,2,"completed",candidate_id=fixture.c["id"],publication_path="evidence/publication/demo.json")
            self.assertEqual(queue.next_row(fixture.root)["csv_row"],2)
        renamed = dict(proof, fork_parent_url="https://github.com/example/renamed",
            resolved_source_repository_url="https://github.com/example/renamed",
            source_repository_url="https://github.com/example/first",
            source_repository_id=123, fork_parent_repository_id=456)
        tool.write_json(path,renamed)
        with self.assertRaises(ValueError):
            queue.mark(fixture.root,2,"completed",candidate_id=fixture.c["id"],publication_path="evidence/publication/demo.json")
        renamed["fork_parent_repository_id"] = 123
        tool.write_json(path,renamed)
        queue.mark(fixture.root,2,"completed",candidate_id=fixture.c["id"],publication_path="evidence/publication/demo.json")
        self.assertEqual(queue.next_row(fixture.root)["csv_row"],3)

if __name__ == "__main__":
    unittest.main()
