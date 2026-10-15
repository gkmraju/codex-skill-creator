"""Commit only cloud-owned state; refuse remote advancement instead of overwriting."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from skill_migration.github import GitHub

client = GitHub()
base = client.git(ROOT, "rev-parse", "HEAD").strip()
client.git(ROOT, "fetch", "origin", "main")
remote = client.git(ROOT, "rev-parse", "origin/main").strip()
if base != remote:
    raise SystemExit("Remote advanced during this run. Preserve Actions output and rerun after inspection.")
client.git(ROOT, "add", "--", "registry/queue-state.json", "registry/cloud-state.json", "reports/cloud", "STATUS.md")
if client.git(ROOT, "diff", "--cached", "--name-only").strip():
    client.git(ROOT, "commit", "-m", "Record Python daily migration " + os.environ.get("GITHUB_RUN_ID", "local"))
    client.git(ROOT, "push", "origin", "HEAD:main")
print("Cloud checkpoint saved")
