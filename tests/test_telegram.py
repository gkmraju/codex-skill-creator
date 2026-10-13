import copy
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from skill_migration import telegram as tg
from skill_migration.tool import Invalid


def fixture():
    return {"run_id":"synthetic-test","date":"2026-10-13","duration_seconds":62,
            "measurement_scope":"synthetic fixture timing","next_step":"Exercise real behavior.",
            "repositories_discovered":1,"skills_reviewed":1,"migrations_completed":0,
            "skills":[{"name":"<unsafe & skill>","outcome":"deferred","usefulness":"Reproducible art",
                      "audience":"Creative coders","impact":"Potential learning benefit",
                      "impact_evidence":"Estimate; no adoption measured","changes":"Draft instructions",
                      "validation":"Structural only","limitations":"Acceptance pending",
                      "learning":"Seed both random and noise generators",
                      "links":[{"label":"Source","url":"https://example.org/source"}]}]}


class TelegramTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.settings={"TELEGRAM_ENABLED":"true","TELEGRAM_BOT_TOKEN":"123456:"+"A"*35,
                       "TELEGRAM_CHAT_ID":"-100123456789"}
    def test_render_escapes_input_and_labels_estimate(self):
        text=tg.render(fixture())
        self.assertIn("&lt;unsafe &amp; skill&gt;",text)
        self.assertIn("0 published",text)
        self.assertIn("Not release-ready",text)
    def test_counts_cannot_claim_completion(self):
        r=fixture();r["migrations_completed"]=1
        with self.assertRaises(Invalid): tg.render(r)
    def test_bad_link_refused_and_long_text_compacted(self):
        r=fixture();r["skills"][0]["links"][0]["url"]="javascript:bad"
        with self.assertRaises(Invalid): tg.render(r)
        r=fixture();r["skills"][0]["changes"]="x"*5000
        self.assertLess(len(tg.render(r)), 1800)
    def test_published_outcome_requires_linked_commit_and_ci(self):
        r=fixture();r["skills"][0]["outcome"]="published";r["migrations_completed"]=1
        with self.assertRaises(Invalid): tg.render(r)
        r["skills"][0]["publication"]={
            "repository_url":"https://github.com/gkmraju/codex-skill-example",
            "commit_sha":"a"*40,"ci_conclusion":"success",
            "ci_url":"https://github.com/gkmraju/codex-skill-example/actions/runs/123"}
        self.assertIn("1 published",tg.render(r))

    def test_literal_env_parsing_does_not_execute(self):
        p=self.root/"env";p.write_text('TELEGRAM_ENABLED=false\nTELEGRAM_CHAT_ID="-100123"\n# comment\n')
        with patch.dict("os.environ",{},clear=True):
            env=tg.load_env(p)
        self.assertEqual("-100123",env["TELEGRAM_CHAT_ID"])
    def test_disabled_and_missing_credentials_do_not_send(self):
        with self.assertRaises(Invalid): tg.send("text","test",{},self.root)
        settings={**self.settings,"TELEGRAM_BOT_TOKEN":""}
        with self.assertRaises(Invalid): tg.send("text","test",settings,self.root)
        self.assertFalse((self.root/"test.json").exists())
    def test_mocked_delivery_and_repeat_denial(self):
        calls=[]
        def opener(req,timeout):
            calls.append(json.loads(req.data))
            return io.StringIO('{"ok":true,"result":{"message_id":42}}')
        self.assertEqual(42,tg.send("test","run",self.settings,self.root,opener))
        self.assertEqual("HTML",calls[0]["parse_mode"])
        with self.assertRaises(Invalid): tg.send("test","run",self.settings,self.root,opener)
        self.assertEqual(1,len(calls))
        state=json.loads((self.root/"run.json").read_text())
        self.assertNotIn("chat_id",state);self.assertNotIn("token",state)
    def test_error_withholds_token_and_blocks_uncertain_retry(self):
        def opener(req,timeout):
            raise urllib.error.URLError("URL includes "+self.settings["TELEGRAM_BOT_TOKEN"])
        with self.assertRaises(Invalid) as e: tg.send("text","run",self.settings,self.root,opener)
        self.assertNotIn(self.settings["TELEGRAM_BOT_TOKEN"],str(e.exception))
        with self.assertRaises(Invalid): tg.send("text","run",self.settings,self.root,opener)
    def test_preview_has_valid_document_and_escaped_content(self):
        text=tg.preview(tg.render(fixture()))
        self.assertIn("<!doctype html>",text)
        self.assertIn("&lt;unsafe",text)

if __name__=="__main__":
    unittest.main()
