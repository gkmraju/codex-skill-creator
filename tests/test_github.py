import io
import json
import unittest
from unittest.mock import MagicMock, patch
import urllib.error
from skill_migration.github import GitHub


class GitHubRedirectTests(unittest.TestCase):
    def response(self, payload):
        response = MagicMock()
        response.__enter__.return_value = response
        response.read.return_value = json.dumps(payload).encode()
        return response

    def test_same_host_307_preserves_post_body(self):
        redirect = urllib.error.HTTPError("https://api.github.com/repos/old/name/forks", 307,
            "Moved", {"Location": "https://api.github.com/repositories/123/forks"}, io.BytesIO())
        opener = MagicMock()
        opener.open.side_effect = [redirect, self.response({"id": 456})]
        with patch("skill_migration.github.urllib.request.build_opener", return_value=opener):
            result = GitHub("synthetic-test-token").api("/repos/old/name/forks", "POST", {"name": "codex-skill-demo"})
        self.assertEqual(result["id"], 456)
        first, second = [call.args[0] for call in opener.open.call_args_list]
        self.assertEqual(first.data, second.data)
        self.assertEqual(second.get_method(), "POST")
        self.assertEqual(second.full_url, "https://api.github.com/repositories/123/forks")

    def test_cross_host_redirect_never_receives_credentials(self):
        redirect = urllib.error.HTTPError("https://api.github.com/repos/old/name", 307,
            "Moved", {"Location": "https://untrusted.invalid/collect"}, io.BytesIO())
        opener = MagicMock()
        opener.open.side_effect = redirect
        with patch("skill_migration.github.urllib.request.build_opener", return_value=opener):
            with self.assertRaisesRegex(RuntimeError, "Unsafe"):
                GitHub("synthetic-test-token").api("/repos/old/name")
        self.assertEqual(opener.open.call_count, 1)

    def test_redirect_loop_is_bounded(self):
        redirect = urllib.error.HTTPError("https://api.github.com/repos/loop/name", 307,
            "Moved", {"Location": "/repos/loop/name"}, io.BytesIO())
        opener = MagicMock()
        opener.open.side_effect = redirect
        with patch("skill_migration.github.urllib.request.build_opener", return_value=opener):
            with self.assertRaisesRegex(RuntimeError, "excessive"):
                GitHub("synthetic-test-token").api("/repos/loop/name")
        self.assertEqual(opener.open.call_count, 4)
