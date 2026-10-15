"""Python-only daily runner. Unknown conversions require manual intervention."""
import argparse
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from . import tool as t
from . import telegram
from .github import GitHub

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import next_candidate as queue

IST = timezone(timedelta(hours=5, minutes=30))


def date_ist():
    return datetime.now(IST).date().isoformat()


def safe_reason(value):
    if t.PRIVATE.search(value) or "api.telegram.org/bot" in value or "github_pat_" in value:
        return "Check failed; private details withheld. Inspect the Actions run."
    return " ".join(value.split())[:400]


def recipe_for(root, selected):
    recipes = t.read_json(root / "registry/conversion-recipes.json")
    matches = [r for r in recipes["recipes"] if r["repository"] == selected["repository"]]
    if len(matches) > 1:
        raise t.Invalid("Multiple recipes for one row; select one actual skill manually")
    return matches[0] if matches else None


def candidate_for(root, recipe):
    data = t.read_json(root / "registry/candidates.json")
    errors = t.schema_errors(data)
    if errors:
        raise t.Invalid("; ".join(errors))
    candidate = next((c for c in data["candidates"] if c["id"] == recipe["candidate_id"]), None)
    if not candidate or candidate["source"]["origin"] != recipe["repository"]:
        raise t.Invalid("Recipe candidate/source mismatch")
    if candidate["source"]["revision"] != recipe["revision"]:
        raise t.Invalid("Recipe revision mismatch")
    if t.tree_sha(t.within(root, candidate["artifact"])) != recipe["artifact_sha256"]:
        raise t.Invalid("Reviewed replacement artifact changed; manual review required")
    errors = t.release_errors(root, candidate)
    if errors:
        raise t.Invalid("; ".join(errors))
    return candidate


def require_unused(root, candidate):
    _, state, _ = queue.load_queue(root)
    for progress in state["rows"].values():
        if progress.get("status") == "completed" and (
            progress.get("candidate_id") == candidate["id"] or (
                progress.get("source_repository") == candidate["source"]["origin"] and
                progress.get("selected_skill_path") == candidate["source"]["skill_path"])):
            raise t.Invalid("Source skill already completed in this queue; select an unused skill manually")


def verify_source(root, candidate, client, checkout_eol="lf"):
    """Fetch pinned public source; never execute upstream code or instructions."""
    checkout = root / "tmp/cloud-source"
    if checkout.exists():
        raise t.Invalid("Source checkout exists; use a fresh runner")
    checkout.parent.mkdir(parents=True, exist_ok=True)
    client.git(root, "clone", "--no-checkout", "--filter=blob:none",
        candidate["source"]["origin"] + ".git", str(checkout))
    source = candidate["source"]
    revision = source["revision"]
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise t.Invalid("Cloud recipe requires an immutable Git commit")
    if checkout_eol not in {"lf", "crlf"}:
        raise t.Invalid("Recipe checkout_eol must be lf or crlf")
    client.git(checkout, "-c", "core.autocrlf=" + ("true" if checkout_eol == "crlf" else "false"),
        "checkout", "--detach", revision)
    if client.git(checkout, "rev-parse", "HEAD").decode().strip() != revision:
        raise t.Invalid("Source checkout revision mismatch")
    if t.tree_sha(t.within(checkout, source["skill_path"])) != source["sha256"]:
        raise t.Invalid("Source skill hash changed")
    for notice in source["license_files"]:
        if t.sha(t.within(checkout, notice["path"])) != notice["sha256"]:
            raise t.Invalid("Original license hash mismatch")


def evaluate_recipe(root, recipe, client, run_command=subprocess.run):
    candidate = candidate_for(root, recipe)
    verify_source(root, candidate, client, recipe.get("checkout_eol", "lf"))
    reviewed = t.within(root, candidate["artifact"])
    artifact = root / "dist/cloud-conversion" / candidate["slug"]
    if artifact.exists():
        raise t.Invalid("Conversion directory exists; use a fresh runner")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(reviewed, artifact)
    if t.tree_sha(artifact) != recipe["artifact_sha256"]:
        raise t.Invalid("Reconstructed package differs from reviewed recipe")
    checks = recipe.get("checks", [])
    if not checks or not any(c.get("scope") == "behavior" for c in checks):
        raise t.Invalid("Recipe needs an exercised behavior check")
    output = []
    for index, check in enumerate(checks):
        argv = check["argv"]
        if not isinstance(argv, list) or not argv or argv[0] not in {"python", "node"}:
            raise t.Invalid("Recipe checks require explicit Python/Node argv")
        command = [sys.executable if argv[0] == "python" else "node", *argv[1:]]
        run = run_command(command, cwd=artifact, capture_output=True, timeout=180)
        path = root / f"tmp/cloud-logs/check-{index}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(run.stdout + run.stderr)
        output.append({"name": check["name"], "scope": check["scope"],
            "exit_code": run.returncode, "output_sha256": t.sha(path)})
        if run.returncode:
            raise t.Invalid(f"Recipe check failed: {check['name']}; inspect Actions artifacts")
    if t.tree_sha(artifact) != recipe["artifact_sha256"]:
        raise t.Invalid("Checks modified the reviewed artifact")
    return candidate, output


def evaluate(root, client=None):
    selected = queue.next_row(root)
    result = {"schema_version": 1, "date": date_ist(), "started_at": time.time(),
        "base_commit": os.environ.get("GITHUB_SHA", "local"), "run_id": os.environ.get("GITHUB_RUN_ID", "local"), "selected": selected,
        "status": "intervention", "checks": []}
    client = client or GitHub()
    try:
        if selected.get("status") == "queue-exhausted":
            result.update(status="exhausted", reason="CSV exhausted; supply another curated batch")
        else:
            source = selected["repository"].removeprefix("https://github.com/")
            if not client.api("/repos/" + source):
                raise t.Invalid("Source unavailable (GitHub HTTP 404); verify the CSV URL/access")
            recipe = recipe_for(root, selected)
            if recipe is None:
                raise t.Invalid("No reviewed Python recipe; manually adapt one developer skill and add behavior tests")
            require_unused(root, candidate_for(root, recipe))
            candidate, checks = evaluate_recipe(root, recipe, client)
            result.update(status="ready", candidate_id=candidate["id"],
                artifact_sha256=recipe["artifact_sha256"], checks=checks, reason="Recipe and checks passed")
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        result["reason"] = safe_reason(str(error))
    t.write_json(root / "tmp/cloud-result.json", result)
    print(json.dumps({"status": result["status"], "reason": result["reason"]}))
    return result


def publication(root, candidate, result, client):
    """Publish the reviewed tree. Existing remote work is reused only byte-exactly."""
    if (client.api("/user") or {}).get("login") != "gkmraju":
        raise t.Invalid("Publishing credential must belong to gkmraju")
    name = "codex-skill-" + candidate["slug"]
    path = "/repos/gkmraju/" + name
    source = candidate["source"]["origin"]
    meta = client.api(path)
    created = not meta
    if created:
        client.api("/repos/" + source.removeprefix("https://github.com/") + "/forks",
            "POST", {"name": name, "default_branch_only": True})
        for _ in range(30):
            meta = client.api(path)
            if meta:
                break
            time.sleep(2)
    if not meta or meta.get("fork") is not True or meta.get("parent", {}).get("html_url") != source:
        raise t.Invalid("Target must be an actual fork of the selected source")
    if meta.get("private") or meta.get("html_url") != "https://github.com/gkmraju/" + name:
        raise t.Invalid("Unexpected/private publication target")
    checkout = root / "dist/cloud-publication" / name
    checkout.parent.mkdir(parents=True, exist_ok=True)
    if checkout.exists():
        raise t.Invalid("Publication checkout exists; use a fresh runner")
    client.git(root, "clone", meta["clone_url"], str(checkout))
    artifact = t.within(root, candidate["artifact"])
    expected = {p.relative_to(artifact).as_posix(): p.read_bytes() for p in t.files_under(artifact)}

    def matches():
        names = client.git(checkout, "ls-tree", "-r", "--name-only", "HEAD").decode().splitlines()
        return set(names) == set(expected) and all(
            client.git(checkout, "show", "HEAD:" + name) == value for name, value in expected.items())

    if not matches():
        if not created:
            raise t.Invalid("Existing target differs; preserve remote work and inspect manually")
        if not checkout.resolve().is_relative_to((root / "dist/cloud-publication").resolve()):
            raise t.Invalid("Unsafe publication checkout")
        client.git(checkout, "rm", "-r", "--ignore-unmatch", "--", ".")
        for name, raw in expected.items():
            target = checkout / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        client.git(checkout, "add", "--all")
        client.git(checkout, "commit", "-m", "Publish reviewed Codex skill: " + candidate["slug"])
        if not matches():
            raise t.Invalid("Committed bytes differ from reviewed artifact")
        client.git(checkout, "push", "origin", "HEAD:" + meta["default_branch"])
    commit = client.git(checkout, "rev-parse", "HEAD").decode().strip()
    proof = {"repository_url": meta["html_url"], "commit_sha": commit,
        "artifact_sha256": t.tree_sha(artifact), "fork": True, "fork_parent_url": source,
        "ci_conclusion": "pending"}
    proof_file = run_folder(root, result) / "publication.json"
    t.write_json(proof_file, proof)
    workflow_path = path + "/actions/workflows/validate.yml"
    workflow = None
    for _ in range(20):
        workflow = client.api(workflow_path)
        if workflow:
            break
        time.sleep(3)
    if not workflow:
        raise t.Invalid("Published fork has no validation workflow; manual intervention required")
    if workflow["state"] != "active":
        client.api(workflow_path + "/enable", "PUT")
    client.api(workflow_path + "/dispatches", "POST", {"ref": meta["default_branch"]})
    for _ in range(120):
        runs = client.api(path + "/actions/runs?head_sha=" + commit + "&per_page=100")
        relevant = [r for r in runs.get("workflow_runs", []) if r["workflow_id"] == workflow["id"]]
        for run in relevant:
            if run["status"] == "completed" and run["conclusion"] == "success":
                jobs = client.api(path + f"/actions/runs/{run['id']}/jobs?per_page=100")
                if jobs["total_count"] > 100 or not jobs["jobs"] or not all(
                    j["status"] == "completed" and j["conclusion"] == "success" for j in jobs["jobs"]):
                    continue
                proof.update(ci_url=run["html_url"], ci_conclusion="success")
                t.write_json(proof_file, proof)
                return proof
        if relevant and all(r["status"] == "completed" for r in relevant):
            raise t.Invalid("Skill CI did not pass; published fork needs intervention")
        time.sleep(10)
    raise t.Invalid("CI still pending after 20 minutes; resume after inspection")


def run_folder(root, result):
    run_id = result.get("run_id", os.environ.get("GITHUB_RUN_ID", "local"))
    if not re.fullmatch(r"[a-z0-9-]+", str(run_id)):
        raise t.Invalid("Invalid cloud run ID")
    return root / "reports/cloud" / result["date"] / str(run_id)


def plan(root):
    state_file = root / "registry/cloud-state.json"
    state = t.read_json(state_file) if state_file.exists() else {"days": {}}
    previous = state["days"].get(date_ist())
    run = not previous or os.environ.get("RETRY_TODAY") == "true"
    if previous and previous["status"] == "published":
        run = False
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write("run=" + str(run).lower() + "\n")
    print("Daily run required" if run else "Today already recorded; no duplicate publication/Telegram")
    return run


def report(root, result):
    selected = result["selected"]
    item = None
    published = result["status"] == "published"
    if selected.get("csv_row") and result.get("candidate_id"):
        item = {"name": f"CSV row {selected['csv_row']}: {selected['name']}",
            "outcome": "published" if published else "deferred",
            "usefulness": "Reviewed Codex conversion" if published else "Manual intervention required",
            "audience": "software developers", "impact": "No adoption/savings measured",
            "impact_evidence": "Observed recipe checks and CI only", "changes": "Reviewed replacement recipe",
            "validation": result["reason"], "limitations": result["reason"],
            "learning": "Deterministic rules need source-specific review",
            "links": [{"label": "Source repository", "url": selected["repository"]}]}
        if published:
            item["publication"] = result["publication"]
    return {"manual_intervention": None if published else {"name": selected.get("name", "Queue"),
        "csv_row": selected.get("csv_row"), "repository": selected.get("repository"), "reason": result["reason"]},
        "run_id": "cloud-" + result["date"] + "-" + os.environ.get("GITHUB_RUN_ID", "local"),
        "date": result["date"], "duration_seconds": max(0, time.time() - result["started_at"]),
        "measurement_scope": "Python cloud run; no LLM usage", "repositories_discovered": 0,
        "skills_reviewed": int(item is not None), "migrations_completed": int(published),
        "skills": [item] if item else [],
        "next_step": "Next CSV row tomorrow" if published else result["reason"]}


def finalize(root, result, client=None):
    selected = queue.next_row(root)
    if result.get("schema_version") != 1 or result["selected"] != selected or result["date"] != date_ist():
        raise t.Invalid("Stale/wrong queue result; refuse publication and state changes")
    if os.environ.get("GITHUB_SHA") and result["base_commit"] != os.environ["GITHUB_SHA"]:
        raise t.Invalid("Evaluation belongs to a different control commit")
    if result["status"] == "ready":
        try:
            recipe = recipe_for(root, selected)
            candidate = candidate_for(root, recipe)
            require_unused(root, candidate)
            if result["candidate_id"] != candidate["id"] or result["artifact_sha256"] != recipe["artifact_sha256"]:
                raise t.Invalid("Evaluation artifact/candidate mismatch")
            expected = [(c["name"], c["scope"]) for c in recipe["checks"]]
            actual = [(c["name"], c["scope"]) for c in result["checks"]]
            if expected != actual or any(c["exit_code"] != 0 for c in result["checks"]):
                raise t.Invalid("Incomplete evaluation results")
            queue.mark(root, selected["csv_row"], "in-progress", skill_path=candidate["source"]["skill_path"])
            proof = publication(root, candidate, result, client or GitHub())
            queue.mark(root, selected["csv_row"], "completed", candidate_id=candidate["id"],
                publication_path=(run_folder(root, result) / "publication.json").relative_to(root).as_posix())
            result.update(status="published", publication=proof,
                reason="Reviewed recipe, fresh behavior checks and completed skill CI passed")
        except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
            result.update(status="intervention", reason=safe_reason(str(error)))
    if result["status"] == "intervention" and selected.get("csv_row"):
        queue.mark(root, selected["csv_row"], "in-progress", reason=result["reason"])
    folder = run_folder(root, result)
    t.write_json(folder / "result.json", result)
    run_report = report(root, result)
    t.write_json(folder / "run.json", run_report)
    (folder / "telegram-preview.html").write_text(telegram.preview(telegram.render(run_report)), encoding="utf-8")
    (folder / "summary.md").write_text(f"# Python daily run: {result['date']}\n\n"
        f"Outcome: {result['status']}\n\n{result['reason']}\n\nNo LLM used. Details: result.json.\n", encoding="utf-8")
    (root / "STATUS.md").write_text("# Current checkpoint\n\n" +
        (folder / "summary.md").read_text(encoding="utf-8") +
        "\nQueue remains authoritative. Daily runner: GitHub Actions, 07:00 IST.\n", encoding="utf-8")
    state_path = root / "registry/cloud-state.json"
    state = t.read_json(state_path) if state_path.exists() else {"schema_version": 1, "days": {}}
    state["days"][result["date"]] = {"run_id": result.get("run_id", "local"),
        "status": result["status"], "report": (folder / "run.json").relative_to(root).as_posix()}
    t.write_json(state_path, state)
    # Reserve before the workflow commits the result; duplicate runs stop at plan().
    t.write_json(folder / "telegram-delivery.json", {"status": "reserved; inspect before any retry"})
    print(json.dumps({"status": result["status"], "reason": result["reason"]}))
    return result


def notify(root):
    folder = run_folder(root, {"date": date_ist()})
    saved = folder / "telegram-delivery.json"
    if not saved.exists() or t.read_json(saved).get("status") != "reserved; inspect before any retry":
        raise t.Invalid("Delivery was not reserved or was already attempted; inspect before retrying")
    run = t.read_json(folder / "run.json")
    # Persist the attempt before sending in the workflow; never expose destination/receipt details.
    t.write_json(saved, {"run_id": run["run_id"], "status": "attempting"})
    settings = telegram.load_env(root / ".env.telegram")
    try:
        telegram.send(telegram.render(run), run["run_id"], settings, state_dir=root / "evidence/telegram")
        t.write_json(saved, {"run_id": run["run_id"], "status": "confirmed"})
        print("Telegram confirmed delivery")
    except (ValueError, OSError) as error:
        t.write_json(saved, {"run_id": run["run_id"], "status": "unconfirmed; inspect before retrying"})
        raise t.Invalid(safe_reason(str(error))) from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["plan", "evaluate", "finalize", "notify", "recipe-check"])
    parser.add_argument("--result", type=Path, default=ROOT / "tmp/cloud-result.json")
    parser.add_argument("--recipe")
    args = parser.parse_args(argv)
    try:
        if args.action == "recipe-check":
            recipes = t.read_json(ROOT / "registry/conversion-recipes.json")["recipes"]
            recipe = next((r for r in recipes if r["id"] == args.recipe), None)
            if recipe is None:
                raise t.Invalid("Unknown recipe")
            candidate, checks = evaluate_recipe(ROOT, recipe, GitHub())
            print(json.dumps({"candidate": candidate["id"], "checks": checks}, indent=2))
        elif args.action == "plan":
            plan(ROOT)
        elif args.action == "evaluate":
            evaluate(ROOT)
        elif args.action == "finalize":
            if args.result.exists():
                result = t.read_json(args.result)
            else:
                result = {"schema_version": 1, "date": date_ist(), "started_at": time.time(),
                    "base_commit": os.environ.get("GITHUB_SHA", "local"),
                    "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
                    "selected": queue.next_row(ROOT), "status": "intervention", "checks": [],
                    "reason": "Evaluation job failed before producing a result; inspect Actions logs"}
            finalize(ROOT, result)
        else:
            notify(ROOT)
        return 0
    except (ValueError, RuntimeError, OSError, KeyError, TypeError) as error:
        print("ERROR: " + safe_reason(str(error)), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
