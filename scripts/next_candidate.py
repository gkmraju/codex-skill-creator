"""Print only the next source row from the user-curated migration queue."""
import csv
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
def next_row(root=ROOT):
    policy = json.loads((root/"registry/queue-policy.json").read_text(encoding="utf-8"))
    queue = root/policy["csv_file"]
    raw = queue.read_bytes()
    if hashlib.sha256(raw).hexdigest() != policy["csv_sha256"]:
        raise ValueError("CSV changed since accepted curation; refresh its recorded approval before running")
    state = json.loads((root/"registry/queue-state.json").read_text(encoding="utf-8"))
    rows = csv.DictReader(raw.decode("utf-8-sig").splitlines())
    if rows.fieldnames != ["Name", "Approx_Stars", "GitHub_Link"]:
        raise ValueError("Expected Name, Approx_Stars, GitHub_Link columns")
    for index, row in enumerate(rows, 2):
        progress = state["rows"].get(str(index), {})
        status = progress.get("status", "pending")
        if status not in {"pending", "in-progress", "completed", "blocked", "skipped"}:
            raise ValueError("Unknown status for CSV row "+str(index))
        if status in {"completed", "blocked", "skipped"}:
            continue
        parsed = urlsplit(row["GitHub_Link"])
        if (parsed.scheme != "https" or parsed.netloc != "github.com"
            or len(parsed.path.strip("/").split("/")) != 2 or parsed.query or parsed.fragment):
            raise ValueError("Expected a plain GitHub repository URL at CSV row "+str(index))
        return {"csv_row":index, "name":row["Name"], "approx_stars":row["Approx_Stars"],
            "repository":row["GitHub_Link"], "screening":"accepted user curation; do not repeat Codex equivalence search",
            "audience":policy["audience"], "progress":progress}
    return {"status":"queue-exhausted","next_action":"Request another user-curated batch; do not start broad discovery"}

if __name__ == "__main__":
    try:
        print(json.dumps(next_row(),ensure_ascii=False,indent=2))
    except (OSError, ValueError, KeyError) as exc:
        print("ERROR: "+str(exc),file=sys.stderr)
        raise SystemExit(1)
