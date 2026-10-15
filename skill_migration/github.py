"""GitHub client. Credentials stay in memory and environment, never command arguments."""
import base64
import json
import os
import subprocess
import urllib.error
import urllib.request


class GitHub:
    def __init__(self, token=None):
        self.token = token or os.environ.get("SKILL_PUBLISH_TOKEN", "")

    def api(self, path, method="GET", data=None):
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "codex-skill-lab"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        request = urllib.request.Request("https://api.github.com" + path, method=method,
            data=json.dumps(data).encode() if data is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                raw = response.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            if error.code == 404 and method == "GET":
                return None
            raise RuntimeError(f"GitHub HTTP {error.code}: {method} {path}") from None

    def git(self, cwd, *args):
        env = dict(os.environ)
        if self.token:
            env.update(GIT_CONFIG_COUNT="2", GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                GIT_CONFIG_VALUE_0="AUTHORIZATION: basic " + base64.b64encode(
                    ("x-access-token:" + self.token).encode()).decode(),
                GIT_CONFIG_KEY_1="credential.helper", GIT_CONFIG_VALUE_1="", GIT_TERMINAL_PROMPT="0")
        run = subprocess.run(["git", "-c", "safe.directory=" + str(cwd),
            "-c", "user.name=gkmraju", "-c", "user.email=3195668+gkmraju@users.noreply.github.com",
            *args], cwd=cwd, env=env, capture_output=True, timeout=180)
        if run.returncode:
            raise RuntimeError("Git operation failed: " + args[0])
        return run.stdout
