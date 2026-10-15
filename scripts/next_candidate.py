"""Select and record one row from the accepted CSV queue, in source order."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"pending", "in-progress", "completed", "blocked", "skipped"}

def load_queue(root):
    policy = json.loads((root/"registry/queue-policy.json").read_text(encoding="utf-8"))
    raw = (root/policy["csv_file"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != policy["csv_sha256"]:
        raise ValueError("CSV changed since accepted curation; refresh its recorded approval")
    state = json.loads((root/"registry/queue-state.json").read_text(encoding="utf-8"))
    if state.get("schema_version") != 1 or not isinstance(state.get("rows"), dict):
        raise ValueError("Invalid queue state")
    reader = csv.DictReader(raw.decode("utf-8-sig").splitlines())
    if reader.fieldnames != ["Name", "Approx_Stars", "GitHub_Link"]:
        raise ValueError("Expected Name, Approx_Stars, GitHub_Link columns")
    return policy, state, list(reader)

def next_row(root=ROOT, excluded_rows=()):
    policy, state, rows = load_queue(root)
    for index, row in enumerate(rows, 2):
        progress = state["rows"].get(str(index), {})
        if not isinstance(progress, dict) or progress.get("status", "pending") not in STATUSES:
            raise ValueError("Invalid status for CSV row "+str(index))
        if index in excluded_rows or progress.get("status") in {"completed", "blocked", "skipped"}:
            continue
        parsed = urlsplit(row["GitHub_Link"])
        if (parsed.scheme != "https" or parsed.netloc != "github.com"
            or not re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", parsed.path)
            or parsed.query or parsed.fragment):
            raise ValueError("Expected a plain GitHub repository URL at CSV row "+str(index))
        return {"csv_row":index, "name":row["Name"], "approx_stars":row["Approx_Stars"],
            "repository":row["GitHub_Link"].rstrip("/"), "screening":"accepted user curation; no fresh equivalence search",
            "audience":policy["audience"], "progress":progress}
    return {"status":"queue-exhausted","next_action":"Request another curated batch; do not start discovery"}

def publication_record(root, selected, candidate_id, publication_path):
    sys.path.insert(0, str(ROOT))
    from skill_migration import tool
    data = tool.read_json(root/"registry/candidates.json")
    errors = tool.schema_errors(data)
    if errors:
        raise ValueError("; ".join(errors))
    candidate = next((c for c in data["candidates"] if c["id"] == candidate_id), None)
    if not candidate or candidate["source"]["origin"].rstrip("/") != selected["repository"]:
        raise ValueError("Candidate must belong to the selected CSV repository")
    errors = tool.release_errors(root, candidate)
    if errors:
        raise ValueError("; ".join(errors))
    evidence = tool.read_json(tool.within(root, publication_path))
    repo = evidence.get("repository_url", "")
    if not re.fullmatch(r"https://github[.]com/gkmraju/codex-skill-[a-z0-9-]+", repo):
        raise ValueError("Expected the individual public skill repository")
    parent = evidence.get("fork_parent_url", "").rstrip("/")
    renamed_source = (type(evidence.get("source_repository_id")) is int
        and evidence["source_repository_id"] > 0
        and evidence["source_repository_id"] == evidence.get("fork_parent_repository_id")
        and evidence.get("source_repository_url") == selected["repository"]
        and evidence.get("resolved_source_repository_url") == parent
        and re.fullmatch(r"https://github[.]com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", parent))
    if evidence.get("fork") is not True or (parent != selected["repository"] and not renamed_source):
        raise ValueError("Publication evidence must identify an actual fork of this source")
    if not re.fullmatch(r"[a-f0-9]{40}", evidence.get("commit_sha", "")):
        raise ValueError("Publication needs the actual pushed commit")
    if evidence.get("ci_conclusion") != "success" or not re.fullmatch(re.escape(repo)+r"/actions/runs/\d+", evidence.get("ci_url", "")):
        raise ValueError("Publication needs completed successful CI")
    if evidence.get("artifact_sha256") != tool.tree_sha(root/candidate["artifact"]):
        raise ValueError("Publication artifact differs from the reviewed artifact")
    return {"candidate_id":candidate_id,"selected_skill_path":candidate["source"]["skill_path"],
            **{key:evidence[key] for key in ("repository_url","commit_sha","ci_url","artifact_sha256","fork_parent_url")}}

def mark(root, row_number, status, reason="", candidate_id=None, publication_path=None, skill_path=None):
    selected = next_row(root)
    if selected.get("csv_row") != row_number:
        raise ValueError("Only the current next/resumable row can be updated")
    _, state, _ = load_queue(root)
    progress = dict(selected["progress"])
    if status in {"skipped", "blocked"} and not reason.strip():
        raise ValueError("Skipped/blocked rows require a concrete reason")
    if status == "completed":
        if not candidate_id or not publication_path:
            raise ValueError("Completion requires candidate and publication evidence")
        progress.update(publication_record(root, selected, candidate_id, publication_path))
    if skill_path:
        from pathlib import PurePosixPath
        if "\\" in skill_path or PurePosixPath(skill_path).is_absolute() or any(p in {".","..",""} for p in skill_path.split("/")):
            raise ValueError("Skill path must be source-relative")
        progress["selected_skill_path"] = skill_path
    progress.update(status=status, source_repository=selected["repository"])
    if reason:
        progress["reason"] = reason
    state["rows"][str(row_number)] = progress
    path = root/"registry/queue-state.json"
    with tempfile.NamedTemporaryFile("w",dir=path.parent,encoding="utf-8",newline="\n",delete=False) as handle:
        json.dump(state,handle,indent=2);handle.write("\n");temp=Path(handle.name)
    try:
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)
    return {"csv_row":row_number,"progress":progress}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=ROOT)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("next")
    record = sub.add_parser("mark")
    record.add_argument("row",type=int)
    record.add_argument("status",choices=["in-progress","completed","blocked","skipped"])
    record.add_argument("--reason",default="")
    record.add_argument("--skill-path")
    record.add_argument("--candidate")
    record.add_argument("--publication",help="Workspace-relative actual publication evidence JSON")
    args = parser.parse_args(argv)
    try:
        if args.command == "mark":
            result = mark(args.root.resolve(),args.row,args.status,args.reason,args.candidate,args.publication,args.skill_path)
        else:
            result = next_row(args.root.resolve())
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("ERROR: "+str(exc),file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
