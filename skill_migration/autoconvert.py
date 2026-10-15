"""Source-driven Codex packaging for supported documentation-only developer skills.

No model calls and no preconverted artifact requirement. Runtime adapters are trusted
code; upstream executable helpers and provider-specific tool workflows are refused.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import zipfile

import yaml
from . import tool as t

TEMPLATES = Path(__file__).with_name("conversion_templates")
PROFILES = {
    "polars": {"package": "polars==1.44.2",
        "request": "Build a typed lazy CSV aggregation while preserving string IDs and validating joins.",
        "example": "The acceptance case keeps IDs 001/002/003 as strings, aggregates team A to 30 and team B to 5, compares eager/streaming results and rejects duplicate right-side join keys."},
    "networkx": {"package": "networkx==3.5",
        "request": "Find a weighted shortest path and check disconnected nodes in a dependency graph.",
        "example": "The acceptance graph chooses api -> cache -> db with total weight 3 instead of the direct weight-9 edge, and detects a disconnected node."},
    "simpy": {"package": "simpy==4.1.1",
        "request": "Model two jobs competing for a capacity-one resource and verify their event order.",
        "example": "The acceptance simulation runs two two-unit jobs on a capacity-one resource; they start at time 0 and time 2 and finish at time 2 and time 4."},
}
UNSUPPORTED = re.compile(r"(?i)(AskUserQuestion|TaskCreate|TaskUpdate|Task tool|Skill tool|mcp__\w+|\.claude/|CLAUDE\.md|Claude Code|Anthropic API)")
CHECK_NAMES = [("fresh package and library behavior", "behavior")]


def eligible_source(folder):
    files = t.files_under(folder)
    if len(files) > 50 or sum(p.stat().st_size for p in files) > 5_000_000:
        raise t.Invalid("Automatic conversion source exceeds size/file limits")
    for path in files:
        if path.suffix.lower() != ".md" or path.stat().st_size > 1_000_000:
            raise t.Invalid("This automatic adapter accepts Markdown resources only; executable helpers need review")
        text = path.read_text(encoding="utf-8")
        if UNSUPPORTED.search(text):
            raise t.Invalid("Source needs a provider-specific tool adaptation outside the supported converter")
        if t.PRIVATE.search(text):
            raise t.Invalid("Source contains private path or credential markers")


def normalize_skill(text, name, description, package):
    parts = re.split(r"(?m)^---\s*$", text, maxsplit=2)
    if len(parts) != 3 or parts[0].strip():
        raise t.Invalid("Invalid skill frontmatter")
    body = re.sub(r"(?ms)^## Citing Scientific Agent Skills\s*$.*\Z", "", parts[2]).strip()
    header = yaml.safe_dump({"name": name, "description": description}, sort_keys=False).strip()
    intro = ("## Codex execution\n\n"
        "Use the project's Python environment and available Codex file/shell tools. "
        "Install the complete skill with scripts/install.py; runtime requirements are in requirements.txt. "
        "Respect the user's inputs, requested outputs and existing project conventions. "
        "Load linked references only when needed. Upstream examples may require adaptation; "
        "this package's exercised scope is documented in the repository evaluation.\n\n"
        "Tested dependency lock: " + package + ". Optional cloud/GPU integrations are outside package tests.\n\n")
    return "---\n" + header + "\n---\n\n" + intro + (
        "> The guidance below is adapted from upstream. Any upstream review dates, validation suites "
        "or benchmark statements describe that source, not additional tests performed by this package.\n\n") + body + "\n"


def license_record(checkout, skill):
    checkout, skill = Path(checkout).resolve(), Path(skill).resolve()
    notices = []
    for folder in [skill, *skill.parents]:
        if not folder.is_relative_to(checkout):
            break
        for name in ["LICENSE", "LICENSE.md", "LICENSE.txt"]:
            path = folder / name
            if path.is_file() and path not in notices:
                text = path.read_text(encoding="utf-8")
                grant = text[text.find("Permission is hereby granted"):]
                standard = (TEMPLATES / "mit-permission.txt").read_text(encoding="utf-8")
                if "MIT License" not in text or " ".join(grant.split()) != " ".join(standard.split()):
                    raise t.Invalid("Automatic publication accepts recognized complete MIT notices only")
                notices.append(path)
        if folder == checkout:
            break
    if not notices:
        raise t.Invalid("No recognized applicable MIT notice; manual license review required")
    attribution = "; ".join(line.strip() for path in notices
        for line in path.read_text(encoding="utf-8").splitlines() if line.strip().lower().startswith("copyright"))
    if not attribution:
        raise t.Invalid("MIT notice has no source attribution")
    return [{"path": p.relative_to(checkout).as_posix(), "sha256": t.sha(p)} for p in notices], attribution


def build_from_checkout(root, selected, checkout, revision, skill_path):
    folder = t.within(checkout, skill_path)
    meta = t.metadata(folder)
    name = meta["name"]
    if name not in PROFILES:
        raise t.Invalid("No supported automatic runtime adapter for this skill")
    eligible_source(folder)
    profile = PROFILES[name]
    notices, attribution = license_record(checkout, folder)
    candidate = {"id": f"csv-{selected['csv_row']}-{name}", "slug": name, "status": "assessed",
        "source": {"collection": "auto-csv", "location": str(checkout.resolve()),
            "origin": selected["repository"], "skill_path": skill_path, "revision": revision,
            "attribution": attribution, "sha256": t.tree_sha(folder), "license_files": notices,
            "license_decision": "allowed"},
        "assessment": {d: {"status": "unresolved", "notes": "Automatic checks pending"} for d in t.DIMENSIONS},
        "checks": {"codex_overlap": "pass", "prior_work": "pass"}, "blockers": [],
        "artifact": None, "evidence": []}
    ledger = t.read_json(root / "registry/candidates.json")
    if any(c["slug"] == name or (c["source"]["origin"] == selected["repository"]
        and c["source"]["skill_path"] == skill_path) for c in ledger["candidates"]):
        raise t.Invalid("Existing candidate/artifact must be resumed rather than overwritten")
    run_id = str(os.environ.get("GITHUB_RUN_ID", "local"))
    if not re.fullmatch(r"[a-z0-9-]+", run_id):
        raise t.Invalid("Invalid run ID")
    base = f"evidence/auto/{candidate['id']}/{run_id}"

    def evidence(kind, summary, digest=None, cases=None):
        report = {"kind": kind, "outcome": "pass", "reviewer": "Python automatic converter; scoped machine checks, no LLM",
            "recorded_at": datetime.now(timezone.utc).isoformat(), "summary": summary,
            "source_sha256": candidate["source"]["sha256"], "source": t.public_source(candidate),
            "references": [selected["repository"] + "/tree/" + revision + "/" + skill_path,
                "registry/queue-policy.json"]}
        if digest:
            report["artifact_sha256"] = digest
        if cases:
            report.update(environment=f"Python {platform.python_version()} / {platform.system()}; dependency {profile['package']}",
                cases=cases)
        path = base + "/" + kind + ".json"
        t.write_json(root / path, report)
        entry = {"kind": kind, "path": path, "sha256": t.sha(root / path), "artifact_sha256": digest}
        candidate["evidence"].append(entry)

    evidence("license", "Recognized full MIT permission/notice/warranty text; original notices hashed and preserved. No license equivalence inference.")
    policy = t.read_json(root / "registry/queue-policy.json")
    evidence("codex_overlap", f"Accepted user screening for CSV row {selected['csv_row']}, CSV hash {policy['csv_sha256']}. No fresh equivalence search.")
    evidence("prior_work", "Compared source/path and target slug against the local candidate ledger; publication also preserves differing remote work.")
    artifact = t.stage(root, candidate)
    skill = artifact / "skills" / name
    (skill / "SKILL.md").write_text(normalize_skill((folder / "SKILL.md").read_text(encoding="utf-8"),
        name, meta["description"], profile["package"]), encoding="utf-8", newline="\n")
    for path in (skill / "references").rglob("*.md") if (skill / "references").exists() else []:
        text = path.read_text(encoding="utf-8")
        path.write_text("> Retained upstream reference. Historical validation claims below belong to upstream; "
            "see this package's evaluation for checks actually exercised here.\n\n" + text, encoding="utf-8", newline="\n")
    for sub, template in [("scripts/install.py", "install.py"), ("tests/test_package.py", "test_package.py")]:
        target = skill / sub
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((TEMPLATES / template).read_bytes())
    (skill / "requirements.txt").write_text(profile["package"] + "\n", encoding="utf-8", newline="\n")
    (skill / "licenses").mkdir(exist_ok=True)
    for index, notice in enumerate(notices):
        shutil.copyfile(checkout / notice["path"], skill / "licenses" / f"{index}-{Path(notice['path']).name}")
    repository = "https://github.com/gkmraju/codex-skill-" + name
    values = {"TITLE": name.title(), "DESCRIPTION": meta["description"].replace("\n", " "),
        "SLUG": name, "REQUEST": profile["request"], "EXAMPLE": profile["example"],
        "REPOSITORY": repository, "AUTHOR": attribution, "REVISION": revision,
        "SOURCE_URL": selected["repository"] + "/tree/" + revision + "/" + skill_path,
        "LICENSE_NAME": Path(notices[0]["path"]).name}
    readme = (TEMPLATES / "README.md.tmpl").read_text(encoding="utf-8")
    for key, value in values.items():
        readme = readme.replace("{{" + key + "}}", value)
    (artifact / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    shutil.copyfile(checkout / notices[0]["path"], artifact / "LICENSE")
    (artifact / ".gitattributes").write_text("* -text\n", encoding="utf-8")
    workflow = {"name": "Validate Codex skill", "on": ["push", "pull_request", "workflow_dispatch"],
        "permissions": {"contents": "read"}, "jobs": {"validate": {
            "strategy": {"matrix": {"os": ["ubuntu-latest", "windows-latest"], "python": ["3.11", "3.13"]}},
            "runs-on": "${{ matrix.os }}", "steps": [
                {"uses": "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"},
                {"uses": "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
                    "with": {"python-version": "${{ matrix.python }}"}},
                {"run": f"python -m pip install -r skills/{name}/requirements.txt"},
                {"run": f"python -B -m unittest discover -s skills/{name}/tests -v",
                    "env": {"PYTHONDONTWRITEBYTECODE": "1"}}]}}}
    (artifact / ".github/workflows").mkdir(parents=True, exist_ok=True)
    (artifact / ".github/workflows/validate.yml").write_text(yaml.safe_dump(workflow, sort_keys=False), encoding="utf-8", newline="\n")
    (artifact / "docs/migration.md").write_text(
        "# Automatic conversion\n\nGenerated from the pinned upstream skill by Python on GitHub. "
        "Normalize metadata to Codex name/description; retain Markdown resources; remove automatic "
        "scientific citation directives while preserving source attribution; add complete project installation, "
        "trusted runtime acceptance tests, dependency lock, README and independent skill CI. "
        "No existing converted package or model output was used.\n", encoding="utf-8")
    (artifact / "docs/compatibility.md").write_text(
        "# Compatibility\n\nCodex SKILL.md name/description and project .agents/skills installation. "
        "Python 3.11+; locked dependency " + profile["package"] +
        ". Source contains Markdown resources only; provider-specific tool workflows are refused. "
        "No native Codex session or reasoning-quality evaluation is claimed.\n", encoding="utf-8")
    candidate["source"]["location"] = f"sources/auto-csv-{selected['csv_row']}"
    return candidate, profile, base, evidence


def run_checks(root, candidate, profile, base):
    runtime = root / "tmp/auto-runtime"
    if runtime.exists():
        raise t.Invalid("Use a fresh runner for automatic conversion acceptance")
    subprocess.run([sys.executable, "-m", "venv", str(runtime)], check=True, capture_output=True, timeout=120)
    python = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    install = subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check", profile["package"]],
        capture_output=True, timeout=240)
    if install.returncode:
        raise t.Invalid("Locked runtime dependency installation failed; inspect runner logs")
    artifact = t.within(root, candidate["artifact"])
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    run = subprocess.run([str(python), "-B", "-m", "unittest", "discover",
        "-s", f"skills/{candidate['slug']}/tests", "-v"], cwd=artifact, env=env,
        capture_output=True, timeout=180)
    log = (run.stdout + run.stderr).decode("utf-8", errors="replace")
    log = log.replace(str(root), ".").replace(root.as_posix(), ".")
    if run.returncode:
        path = root / "tmp/cloud-logs/automatic-tests.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(log, encoding="utf-8")
        raise t.Invalid("Generated package acceptance failed; inspect Actions test logs")
    if t.PRIVATE.search(log):
        raise t.Invalid("Private path in test output; inspect rather than publish raw output")
    path = base + "/tests.txt"
    (root / path).write_text(log, encoding="utf-8", newline="\n")
    return [{"name": CHECK_NAMES[0][0], "scope": "behavior", "exit_code": 0,
        "output_sha256": t.sha(root / path)}], path


def finish(root, candidate, profile, base, evidence, checks, output_path):
    artifact = root / candidate["artifact"]
    (artifact / "docs/evaluation.md").write_text(
        "# Executed acceptance\n\nFour package tests passed on the conversion runner: fresh byte-exact "
        "installation, overwrite refusal, missing-project refusal and a bounded runtime case.\n\n" +
        profile["example"] + "\n\nDependency: " + profile["package"] +
        ". No agent/model session, broad upstream example suite, production benchmark, cloud or GPU "
        "integration was executed. Skill CI is a separate publication prerequisite.\n", encoding="utf-8")
    notes = {
        "format": "Name/description-only Codex frontmatter; remaining scaffolds and references structurally checked.",
        "resources": "Source is bounded Markdown-only content; complete resources copied and references validated.",
        "platform": "Python portable installer; Windows/Ubuntu CI required before queue completion.",
        "tools": "No provider-specific tool workflow detected by supported markers; available Codex file/shell tools used.",
        "runtime": "Locked library installed and bounded behavior exercised; no native agent/model execution claimed.",
        "installation": "Complete fresh .agents/skills installation and refusal paths passed.",
        "license": "Recognized MIT notices preserved byte-exactly; copyright attribution retained."}
    candidate.update(status="release-ready", blockers=[], assessment={k: {"status": "compatible", "notes": v} for k, v in notes.items()})
    digest = t.tree_sha(artifact)
    evidence("compatibility", "Generated Codex metadata, complete local resources and installer behavior checked; scope described in package docs.", digest)
    evidence("functional", "Generated installer and bounded library behavior tests actually passed.", digest, cases=[{
        "prompt": profile["request"], "expected": profile["example"],
        "observed": "Four acceptance tests passed; bounded runtime behavior and failure paths exercised. No model/agent reasoning evaluation.",
        "outcome": "pass", "outputs": [{"path": output_path, "sha256": t.sha(root / output_path)}]}])
    evidence("security", "Markdown-only source, provider-tool/private-marker checks, exact MIT preservation and reviewed trusted generated helpers. Heuristics are not a guarantee against malicious prose.", digest)
    evidence("review", "Automated artifact/link/schema checks, resolved README template, factual source attribution and bounded validation claims. No human or LLM semantic review inferred.", digest)
    errors = t.schema_errors({"schema_version": 1, "candidates": [candidate]}) + t.release_errors(root, candidate)
    if errors:
        raise t.Invalid("; ".join(errors))
    return digest


def convert(root, selected, client, metadata):
    ledger = t.read_json(root / "registry/candidates.json")
    resumed = next((c for c in ledger["candidates"] if c["id"].startswith(f"csv-{selected['csv_row']}-")
        and c["source"]["origin"] == selected["repository"]), None)
    if resumed:
        from .cloud import verify_source
        errors = t.release_errors(root, resumed)
        if errors or resumed["slug"] not in PROFILES:
            raise t.Invalid("Existing automatic conversion needs repair; refusing replacement")
        verify_source(root, resumed, client)
        base = f"evidence/auto/{resumed['id']}/{os.environ.get('GITHUB_RUN_ID', 'local')}"
        (root / base).mkdir(parents=True, exist_ok=True)
        checks, _ = run_checks(root, resumed, PROFILES[resumed["slug"]], base)
        return bundle_result(root, resumed, checks)
    repository = selected["repository"].removeprefix("https://github.com/")
    revision = client.api("/repos/" + repository + "/commits/" + metadata["default_branch"])["sha"]
    tree = client.api("/repos/" + repository + "/git/trees/" + revision + "?recursive=1")
    if not tree or tree.get("truncated"):
        raise t.Invalid("Repository tree unavailable/truncated; automatic selection needs review")
    paths = [x["path"] for x in tree["tree"] if x["type"] == "blob" and x["path"].endswith("/SKILL.md")
        and Path(x["path"]).parent.name in PROFILES]
    paths.sort(key=lambda p: (list(PROFILES).index(Path(p).parent.name), p))
    if not paths:
        raise t.Invalid("No supported automatic developer runtime skill found (currently polars, networkx, simpy)")
    skill_path = str(Path(paths[0]).parent).replace("\\", "/")
    checkout = root / f"sources/auto-csv-{selected['csv_row']}"
    if checkout.exists():
        raise t.Invalid("Source checkout exists; automatic conversion requires a fresh runner")
    checkout.parent.mkdir(parents=True, exist_ok=True)
    client.git(root, "clone", "--filter=blob:none", "--sparse", "--no-checkout",
        selected["repository"] + ".git", str(checkout))
    client.git(checkout, "-c", "core.autocrlf=false", "sparse-checkout", "set", skill_path)
    client.git(checkout, "-c", "core.autocrlf=false", "checkout", "--detach", revision)
    if client.git(checkout, "rev-parse", "HEAD").decode().strip() != revision:
        raise t.Invalid("Source revision mismatch")
    candidate, profile, base, evidence = build_from_checkout(root, selected, checkout, revision, skill_path)
    checks, output = run_checks(root, candidate, profile, base)
    digest = finish(root, candidate, profile, base, evidence, checks, output)
    return bundle_result(root, candidate, checks)


def bundle_result(root, candidate, checks):
    bundle = root / "tmp/auto-conversion.zip"
    bundle.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("candidate.json", json.dumps(candidate, ensure_ascii=False))
        for file in t.files_under(root / candidate["artifact"]):
            archive.write(file, "artifact/" + file.relative_to(root / candidate["artifact"]).as_posix())
        for file in t.files_under(root / "evidence/auto" / candidate["id"]):
            archive.write(file, file.relative_to(root).as_posix())
    return candidate, checks, t.tree_sha(root / candidate["artifact"]), t.sha(bundle)


def import_bundle(root, selected, result):
    """Treat evaluation output as data; never execute it in the credentialed job."""
    bundle = root / "tmp/auto-conversion.zip"
    if not bundle.is_file() or t.sha(bundle) != result.get("bundle_sha256"):
        raise t.Invalid("Generated conversion bundle missing or changed")
    with zipfile.ZipFile(bundle) as archive:
        items = archive.infolist()
        if len(items) > 150 or sum(i.file_size for i in items) > 20_000_000:
            raise t.Invalid("Conversion bundle exceeds limits")
        folded = set()
        for item in items:
            t.portable(item.filename)
            if item.filename.casefold() in folded or item.is_dir() or item.external_attr >> 16 & 0o170000 == 0o120000:
                raise t.Invalid("Duplicate/directory/linked bundle member")
            folded.add(item.filename.casefold())
        candidate = json.loads(archive.read("candidate.json"))
        source = candidate["source"]
        if source["origin"] != selected["repository"] or candidate["id"] != result["candidate_id"]:
            raise t.Invalid("Generated candidate does not match current row")
        if candidate["slug"] not in PROFILES or candidate["artifact"] != "migrations/" + candidate["slug"]:
            raise t.Invalid("Unsupported generated artifact path/profile")
        if not re.fullmatch(r"[a-f0-9]{40}", source["revision"]):
            raise t.Invalid("Generated source must pin an immutable commit")
        expected_id = f"csv-{selected['csv_row']}-{candidate['slug']}"
        if candidate["id"] != expected_id:
            raise t.Invalid("Generated candidate ID is not row-bound")
        ledger = t.read_json(root / "registry/candidates.json")
        existing = next((c for c in ledger["candidates"] if c["id"] == candidate["id"]), None)
        if existing and existing != candidate:
            raise t.Invalid("Existing candidate differs; preserve it rather than overwrite")
        proposed = ledger["candidates"] if existing else [*ledger["candidates"], candidate]
        errors = t.schema_errors({"schema_version": 1, "candidates": proposed})
        if errors:
            raise t.Invalid("; ".join(errors))
        for item in items:
            name = item.filename
            if name == "candidate.json":
                continue
            if name.startswith("artifact/"):
                relative = candidate["artifact"] + "/" + name.removeprefix("artifact/")
            elif name.startswith("evidence/auto/" + candidate["id"] + "/") and name.endswith((".json", ".txt")):
                relative = name
            else:
                raise t.Invalid("Unexpected generated bundle member")
            target = t.within(root, relative, False)
            raw = archive.read(item)
            if target.exists():
                if not target.is_file() or target.read_bytes() != raw:
                    raise t.Invalid("Refusing to overwrite existing conversion data")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
    if t.tree_sha(root / candidate["artifact"]) != result["artifact_sha256"]:
        raise t.Invalid("Generated artifact fingerprint mismatch")
    errors = t.release_errors(root, candidate)
    if errors:
        raise t.Invalid("; ".join(errors))
    if not existing:
        ledger["candidates"].append(candidate)
    t.write_json(root / "registry/candidates.json", ledger)
    return candidate
