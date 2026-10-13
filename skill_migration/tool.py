"""Inventory, assess, stage, validate and package reviewed skill migrations.

This tool never executes upstream scripts or publishes. Evidence is supplied by
reviewers; hashes establish integrity, not truth of a reviewer's claims.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

import yaml
from jsonschema import Draft202012Validator

DIMENSIONS = ("format", "resources", "platform", "tools", "runtime", "installation", "license")
KINDS = ("license", "codex_overlap", "prior_work", "compatibility", "functional", "security", "review")
BOUND = {"compatibility", "functional", "security", "review"}
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PRIVATE = re.compile(r"(?:(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/Users/|/home/|C:\\Users\\|-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\n]+)\)")
CODE_PATH = re.compile(r"\x60((?:scripts|references|assets|agents)/[^\x60\n]+)\x60")
RESERVED = {"con", "prn", "aux", "nul"} | {f"com{i}" for i in range(1, 10)} | {f"lpt{i}" for i in range(1, 10)}
ROOT = Path(__file__).resolve().parents[1]


class Invalid(ValueError):
    pass


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
        tmp = Path(f.name)
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def portable(value):
    """Release-relative paths use forward slashes and work on Windows too."""
    if not isinstance(value, str) or not value or "\\" in value:
        raise Invalid(f"Invalid relative path: {value!r}")
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in ("", ".", "..") for x in value.split("/")):
        raise Invalid(f"Unsafe relative path: {value}")
    for part in p.parts:
        if any(ord(c) < 32 or c in '<>:"|?*' for c in part) or part.endswith((" ", ".")):
            raise Invalid(f"Nonportable path: {value}")
        if part.split(".")[0].lower() in RESERVED:
            raise Invalid(f"Reserved path: {value}")
    return p


def linked(path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def within(root, value, must_exist=True):
    p = portable(value)
    root = Path(root).resolve()
    target = root.joinpath(*p.parts)
    cur = root
    for part in p.parts:
        cur = cur / part
        if linked(cur):
            raise Invalid(f"Linked path rejected: {value}")
    if not target.resolve().is_relative_to(root):
        raise Invalid(f"Path escapes root: {value}")
    if must_exist and not target.exists():
        raise Invalid(f"Missing path: {value}")
    return target


def files_under(root):
    root = Path(root)
    if linked(root) or not root.is_dir():
        raise Invalid(f"Not a regular directory: {root}")
    found, folded = [], set()
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            p = Path(current) / name
            rel = p.relative_to(root).as_posix()
            portable(rel)
            if linked(p):
                raise Invalid(f"Linked path rejected: {rel}")
            key = rel.casefold()
            if key in folded:
                raise Invalid(f"Case-colliding path: {rel}")
            folded.add(key)
            if name.lower() in {".git", ".env", ".aws", ".ssh", "__pycache__", "credentials", "credentials.json", "id_rsa", "id_ed25519"} or name.lower().startswith(".env.") or p.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
                raise Invalid(f"Private or generated file rejected: {rel}")
            if p.is_file():
                found.append(p)
    return sorted(found, key=lambda p: p.relative_to(root).as_posix())


def tree_sha(root):
    manifest = [(p.relative_to(root).as_posix(), sha(p)) for p in files_under(root)]
    return hashlib.sha256(json.dumps(manifest, separators=(",", ":")).encode()).hexdigest()


def metadata(folder):
    text = (Path(folder) / "SKILL.md").read_text(encoding="utf-8-sig")
    parts = re.split(r"(?m)^---\s*$", text, maxsplit=2)
    if len(parts) != 3 or parts[0].strip():
        raise Invalid("SKILL.md must start with YAML frontmatter")
    # Reject duplicate keys; safe_load alone silently overwrites them.
    node = yaml.compose(parts[1])
    if not isinstance(node, yaml.MappingNode):
        raise Invalid("Frontmatter must be a mapping")
    keys = [key.value for key, _ in node.value]
    if len(set(keys)) != len(keys):
        raise Invalid("Duplicate frontmatter key")
    data = yaml.safe_load(parts[1])
    name, desc = data.get("name"), data.get("description")
    if not isinstance(name, str) or not SLUG.fullmatch(name) or len(name) > 63:
        raise Invalid("Invalid skill name")
    if not isinstance(desc, str) or not desc.strip():
        raise Invalid("Missing skill description")
    if not parts[2].strip():
        raise Invalid("Missing skill instructions")
    return data


def skill_errors(folder, expected=None):
    errors = []
    try:
        meta = metadata(folder)
        if expected and meta["name"] != expected:
            errors.append("Skill name must match candidate slug")
        all_files = files_under(folder)
        for p in all_files:
            if p.suffix.lower() not in {".md", ".yaml", ".yml"}:
                continue
            text = p.read_text(encoding="utf-8")
            refs = [m.group(1) for m in LINK.finditer(text)]
            refs += CODE_PATH.findall(text)
            # Markdown reference-style links.
            refs += re.findall(r"(?m)^\s*\[[^\]]+\]:\s*(\S+)", text)
            for raw in refs:
                raw = raw.strip().strip("<>")
                raw = raw.split(' "')[0]
                parsed = urlsplit(raw)
                if parsed.scheme in {"http", "https", "mailto"} or raw.startswith("#"):
                    continue
                rel = unquote(parsed.path)
                if not rel:
                    continue
                try:
                    base = p.parent.relative_to(folder)
                    within(folder, (base / rel).as_posix())
                except Invalid as e:
                    errors.append(f"{p.name}: {e}")
    except (Invalid, OSError, UnicodeError, yaml.YAMLError, ValueError) as e:
        errors.append(str(e))
    return errors


def schema_errors(data):
    schema = read_json(ROOT / "schemas/registry.schema.json")
    errors = [
        f"{'/'.join(map(str, e.absolute_path)) or 'registry'}: {e.message}"
        for e in Draft202012Validator(schema).iter_errors(data)
    ]
    if errors:
        return errors
    seen_ids, seen_slugs, seen_sources = set(), set(), set()
    for c in data["candidates"]:
        source = c["source"]
        identity = (source["origin"].rstrip("/").casefold(), source["skill_path"].casefold())
        for label, value, seen in (("id", c["id"], seen_ids), ("slug", c["slug"], seen_slugs), ("source", identity, seen_sources)):
            if value in seen:
                errors.append(f"Duplicate {label}: {value}")
            seen.add(value)
        try:
            portable(source["skill_path"])
            for file in source["license_files"]:
                portable(file["path"])
            if c["artifact"] is not None:
                portable(c["artifact"])
            for e in c["evidence"]:
                portable(e["path"])
        except Invalid as e:
            errors.append(f"{c['id']}: {e}")
        kinds = [e["kind"] for e in c["evidence"]]
        if len(set(kinds)) != len(kinds):
            errors.append(f"{c['id']}: Duplicate evidence kind")
    return errors


def report_errors(root, c, entry, artifact_hash=None):
    try:
        p = within(root, entry["path"])
        if not p.is_file() or sha(p) != entry["sha256"]:
            raise Invalid("Evidence file hash mismatch")
        report = read_json(p)
        if not isinstance(report, dict):
            raise Invalid("Evidence report must be an object")
        for key in ("reviewer", "recorded_at", "summary"):
            if not isinstance(report.get(key), str) or not report[key].strip():
                raise Invalid(f"Evidence missing {key}")
        timestamp = datetime.fromisoformat(report["recorded_at"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise Invalid("Evidence timestamp requires a timezone")
        if report.get("kind") != entry["kind"] or report.get("outcome") != "pass":
            raise Invalid("Evidence must identify its kind and passing outcome")
        if report.get("source_sha256") != c["source"]["sha256"] or report.get("source") != public_source(c):
            raise Invalid("Evidence is for a different source identity or snapshot")
        if not isinstance(report.get("references"), list) or not report["references"] or not all(isinstance(r, str) and r.strip() for r in report["references"]):
            raise Invalid("Evidence requires inspectable references")
        if entry["kind"] in BOUND:
            if not artifact_hash or entry["artifact_sha256"] != artifact_hash:
                raise Invalid("Evidence is stale or not bound to current artifact")
            if report.get("artifact_sha256") != artifact_hash:
                raise Invalid("Report artifact fingerprint mismatch")
        if entry["kind"] == "functional":
            if not isinstance(report.get("environment"), str) or not report["environment"].strip():
                raise Invalid("Functional evidence requires environment")
            cases = report.get("cases")
            if not isinstance(cases, list) or not cases:
                raise Invalid("Functional evidence requires exercised cases")
            for case in cases:
                if not isinstance(case, dict) or not all(isinstance(case.get(k), str) and case[k].strip() for k in ("prompt", "expected", "observed")) or case.get("outcome") != "pass":
                    raise Invalid("Functional case needs prompt, expected, observed, and outcome")
                outputs = case.get("outputs")
                if not isinstance(outputs, list) or not outputs:
                    raise Invalid("Functional case requires captured output files")
                for output in outputs:
                    captured = within(root, output["path"])
                    if sha(captured) != output["sha256"]:
                        raise Invalid("Functional output hash mismatch")
        return []
    except (Invalid, OSError, ValueError, TypeError, KeyError) as e:
        return [f"{entry['kind']}: {e}"]


def selection_errors(root, c):
    errors = []
    if c["status"] == "rejected":
        errors.append("Rejected candidate cannot be staged")
    if c["source"]["license_decision"] != "allowed":
        errors.append("License redistribution decision is unresolved or prohibited")
    entries = {e["kind"]: e for e in c["evidence"]}
    for kind in ("license", "codex_overlap", "prior_work"):
        if kind != "license" and c["checks"][kind] != "pass":
            errors.append(f"{kind}: must pass before staging")
        if kind not in entries:
            errors.append(f"{kind}: missing evidence")
        else:
            errors += report_errors(root, c, entries[kind])
    return errors


def artifact_errors(root, c):
    try:
        package = within(root, c["artifact"])
        files = files_under(package)
        required = ("README.md", "UPSTREAM.md", "docs/migration.md", "docs/compatibility.md", "docs/evaluation.md", ".codex-plugin/plugin.json", "provenance.json")
        for name in required:
            p = within(package, name)
            if not p.is_file() or not p.read_bytes().strip():
                raise Invalid(f"Required file is empty: {name}")
        manifest = read_json(package / ".codex-plugin/plugin.json")
        if manifest != {"name": "codex-skill-" + c["slug"], "version": "0.1.0", "description": metadata(package / "skills" / c["slug"])["description"], "skills": "./skills/"}:
            raise Invalid("Unexpected skills-only plugin manifest")
        if sorted(p.name for p in (package / "skills").iterdir()) != [c["slug"]]:
            raise Invalid("Package must contain exactly one skill")
        provenance = read_json(package / "provenance.json")
        if provenance != public_source(c):
            raise Invalid("Package provenance differs from registry")
        for index, license_file in enumerate(c["source"]["license_files"]):
            p = within(package, f"licenses/{index}-{PurePosixPath(license_file['path']).name}")
            if not p.is_file() or not p.read_bytes().strip() or sha(p) != license_file["sha256"]:
                raise Invalid("Missing, empty, or altered license file")
        if not c["source"]["license_files"]:
            raise Invalid("Package needs applicable license and notice files")
        for p in files:
            rel = p.relative_to(package).as_posix()
            allowed = rel in required or rel in {"LICENSE", ".gitattributes", ".github/workflows/validate.yml"} or rel.startswith(("skills/" + c["slug"] + "/", "licenses/"))
            if not allowed:
                raise Invalid(f"Unexpected package file: {rel}")
            if p.suffix.lower() in {".md", ".json", ".py", ".sh", ".ps1", ".yaml", ".yml", ".txt"}:
                if PRIVATE.search(p.read_text(encoding="utf-8")):
                    raise Invalid(f"Private path or credential pattern in {rel}")
        return skill_errors(package / "skills" / c["slug"], c["slug"])
    except (Invalid, OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as e:
        return [str(e)]


def public_source(c):
    source = c["source"]
    return {k: source[k] for k in ("origin", "skill_path", "revision", "attribution", "sha256", "license_files")}


def release_errors(root, c):
    errors = selection_errors(root, c)
    if c["status"] != "release-ready":
        errors.append("Candidate status is not release-ready")
    if c["blockers"]:
        errors.append("Unresolved blockers: " + ", ".join(c["blockers"]))
    for dim, assessment in c["assessment"].items():
        if assessment["status"] != "compatible":
            errors.append(f"{dim}: assessment is {assessment['status']}")
    if not c["source"]["revision"]:
        errors.append("Source revision or immutable version is missing")
    if not c["artifact"]:
        return errors + ["Artifact is missing"]
    structural = artifact_errors(root, c)
    errors += structural
    if structural:
        return errors
    digest = tree_sha(within(root, c["artifact"]))
    entries = {e["kind"]: e for e in c["evidence"]}
    for kind in BOUND:
        if kind not in entries:
            errors.append(f"{kind}: missing evidence")
        else:
            errors += report_errors(root, c, entries[kind], digest)
    return errors


def validate(root, data):
    errors = schema_errors(data)
    if errors:
        return errors
    for c in data["candidates"]:
        if c["artifact"]:
            errors += [f"{c['id']}: {e}" for e in artifact_errors(root, c)]
        if c["status"] == "release-ready":
            errors += [f"{c['id']}: {e}" for e in release_errors(root, c)]
        elif c["status"] == "migrated" and not c["artifact"]:
            errors.append(f"{c['id']}: migrated candidate lacks artifact")
        for entry in c["evidence"]:
            if entry["kind"] not in BOUND:
                errors += [f"{c['id']}: {e}" for e in report_errors(root, c, entry)]
    return errors


def inventory(collection, collection_id, origin, attribution, revision=None):
    if not SLUG.fullmatch(collection_id):
        raise Invalid("Collection id must be a slug")
    collection = Path(collection).resolve()
    # Refuse discovery through directory links, but exclude Git metadata.
    found = []
    for current, dirs, files in os.walk(collection, followlinks=False):
        if linked(Path(current)):
            raise Invalid("Linked source directory")
        dirs[:] = sorted(d for d in dirs if d not in {".git", ".venv", "node_modules", "__pycache__"})
        for d in dirs:
            if linked(Path(current) / d):
                raise Invalid("Linked source directory")
        if "SKILL.md" in files:
            folder = Path(current)
            meta = metadata(folder)
            skill_path = folder.relative_to(collection).as_posix()
            if skill_path == ".":
                raise Invalid("Inventory a parent collection, not a single skill directory")
            candidate = {
                "id": collection_id + "-" + meta["name"], "slug": meta["name"], "status": "discovered",
                "source": {"collection": collection_id, "location": str(collection), "origin": origin,
                           "skill_path": skill_path, "revision": revision, "attribution": attribution,
                           "sha256": tree_sha(folder), "license_files": [], "license_decision": "unknown"},
                "assessment": {dim: {"status": "unresolved", "notes": "Not yet reviewed."} for dim in DIMENSIONS},
                "checks": {"codex_overlap": "pending", "prior_work": "pending"},
                "blockers": ["License and redistribution unresolved", "Codex overlap review pending", "Prior-work review pending"],
                "artifact": None, "evidence": [],
            }
            found.append(candidate)
    if not found:
        raise Invalid("No SKILL.md files discovered")
    return found


def source_folder(c):
    source = c["source"]
    folder = within(Path(source["location"]), source["skill_path"])
    if tree_sha(folder) != source["sha256"]:
        raise Invalid("Source changed since inventory; re-inventory and review")
    return folder


def assess(c):
    folder = source_folder(c)
    findings = {dim: [] for dim in DIMENSIONS}
    findings["format"] = skill_errors(folder)
    findings["resources"] = [p.relative_to(folder).as_posix() for p in files_under(folder)]
    for p in files_under(folder):
        if p.suffix.lower() not in {".md", ".py", ".sh", ".ps1", ".yaml", ".yml", ".json", ".txt"}:
            continue
        text = p.read_text(encoding="utf-8")
        for dim, pattern in {
            "platform": r"(?i)\b(bash|powershell|linux|macos|windows)\b",
            "tools": r"(?i)\b(mcp|slack|telegram|github|api|browser)\b",
            "runtime": r"(?i)(claude|CLAUDE\.md|\.claude|Task tool|subagent)",
            "installation": r"(?i)\b(pip|npm|uv|install|docker)\b",
        }.items():
            hits = sorted(set(re.findall(pattern, text)))
            if hits:
                findings[dim].append({"file": p.relative_to(folder).as_posix(), "markers": hits})
    findings["license"] = {"decision": c["source"]["license_decision"], "files": c["source"]["license_files"]}
    return {"candidate": c["id"], "source_sha256": c["source"]["sha256"],
            "notice": "Heuristic findings only; no compatibility or license approval is inferred.",
            "findings": findings}


def stage(root, c):
    errors = selection_errors(root, c)
    if errors:
        raise Invalid("\n".join(errors))
    folder = source_folder(c)
    collection = Path(c["source"]["location"])
    licenses = [within(collection, x["path"]) for x in c["source"]["license_files"]]
    if not licenses or any(not x.is_file() or not x.read_bytes().strip() for x in licenses):
        raise Invalid("Applicable license and notice files are required")
    if any(sha(p) != record["sha256"] for p, record in zip(licenses, c["source"]["license_files"])):
        raise Invalid("Source license changed since review")
    target_rel = f"migrations/{c['slug']}"
    target = within(root, target_rel, False)
    snapshot = within(root, f"sources/{c['id']}/{c['source']['sha256']}", False)
    if any(output.is_relative_to(folder.resolve()) or folder.resolve().is_relative_to(output) for output in (target.resolve(), snapshot.resolve())):
        raise Invalid("Source and generated outputs must be disjoint")
    if target.exists() or snapshot.exists():
        raise Invalid("Refusing to overwrite migration or source snapshot")
    target.parent.mkdir(parents=True, exist_ok=True)
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
        build = Path(tmp) / "package"
        skill = build / "skills" / c["slug"]
        shutil.copytree(folder, skill)
        meta = metadata(skill)
        if meta["name"] != c["slug"]:
            raise Invalid("Rename candidate slug only after adapting the staged skill; initial slug must match source")
        if tree_sha(skill) != c["source"]["sha256"]:
            raise Invalid("Source changed while staging")
        (build / "licenses").mkdir()
        for index, license_file in enumerate(licenses):
            shutil.copyfile(license_file, build / "licenses" / f"{index}-{license_file.name}")
        write_json(build / "provenance.json", public_source(c))
        write_json(build / ".codex-plugin/plugin.json", {
            "name": "codex-skill-" + c["slug"], "version": "0.1.0",
            "description": meta["description"], "skills": "./skills/",
        })
        docs = {
            "README.md": f"# codex-skill-{c['slug']}\n\nLocal migration under review. Install the reviewed skills/{c['slug']} folder in your Codex skills directory, or load this skills-only plugin using the documented plugin workflow. Functional acceptance is required before use.\n\nSee UPSTREAM.md, licenses/, and docs/.\n",
            "UPSTREAM.md": f"# Upstream attribution\n\nSource: {c['source']['origin']}\n\nSkill: {c['source']['skill_path']}\n\nRevision: {c['source']['revision'] or 'unresolved'}\n\nAttribution: {c['source']['attribution']}\n\nSource SHA-256: {c['source']['sha256']}\n\nApplicable license and notice files are preserved in licenses/.\n",
            "docs/migration.md": "# Migration record\n\nStaged from the unchanged upstream skill. Record every adaptation, rationale, and limitation here before review. Staging is not a completed migration.\n",
            "docs/compatibility.md": "# Compatibility\n\nReview metadata, resources, platform, tools, runtime, installation, and license. Record supported environments and unresolved assumptions here.\n",
            "docs/evaluation.md": "# Evaluation\n\nNo functional workflow has been exercised yet. Record real prompts, observed outputs, environment, and acceptance results here. Store captured evidence in the control repository.\n",
        }
        for name, text in docs.items():
            p = build / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        shutil.copytree(folder, snapshot / "skill")
        shutil.copytree(build / "licenses", snapshot / "licenses")
        write_json(snapshot / "provenance.json", public_source(c))
        shutil.move(str(build), target)
    c["artifact"] = target_rel
    c["status"] = "assessed"
    c["blockers"] = sorted(set(c["blockers"] + ["Staged source requires adaptation and functional evaluation"]))
    return target


def package(root, c):
    errors = release_errors(root, c)
    if errors:
        raise Invalid("\n".join(errors))
    folder = within(root, c["artifact"])
    digest = tree_sha(folder)
    target = within(root, f"dist/codex-skill-{c['slug']}-{digest[:12]}.zip", False)
    if target.exists():
        raise Invalid("Refusing to overwrite existing package")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".zip", delete=False) as f:
        tmp = Path(f.name)
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in files_under(folder):
                rel = p.relative_to(folder).as_posix()
                info = zipfile.ZipInfo(rel, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                z.writestr(info, p.read_bytes())
        if tree_sha(folder) != digest:
            raise Invalid("Artifact changed during packaging")
        # Check archived content against the validated current tree.
        with zipfile.ZipFile(tmp) as z:
            actual = [(n, hashlib.sha256(z.read(n)).hexdigest()) for n in z.namelist()]
            expected = [(p.relative_to(folder).as_posix(), sha(p)) for p in files_under(folder)]
            if actual != expected:
                raise Invalid("Archive differs from reviewed artifact")
        tmp.rename(target)
        return target
    finally:
        tmp.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--registry", default="registry/candidates.json")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    inv = sub.add_parser("inventory")
    inv.add_argument("collection", type=Path)
    for field in ("collection-id", "origin", "attribution"):
        inv.add_argument("--" + field, required=True)
    inv.add_argument("--revision")
    for cmd in ("assess", "stage", "release-check", "package", "fingerprint"):
        sub.add_parser(cmd).add_argument("candidate")
    rec = sub.add_parser("record-evidence")
    rec.add_argument("candidate")
    rec.add_argument("kind", choices=KINDS)
    rec.add_argument("path")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        registry = within(root, args.registry)
        data = read_json(registry)
        errors = schema_errors(data)
        if errors:
            raise Invalid("\n".join(errors))
        if args.command == "inventory":
            additions = inventory(args.collection, args.collection_id, args.origin, args.attribution, args.revision)
            data["candidates"].extend(additions)
            errors = schema_errors(data)
            if errors:
                raise Invalid("\n".join(errors))
            write_json(registry, data)
            print(f"Inventoried {len(additions)} candidate(s); approvals remain pending")
            return 0
        if args.command == "validate":
            errors = validate(root, data)
            if errors:
                raise Invalid("\n".join(errors))
            print(f"Registry valid: {len(data['candidates'])} candidate(s). Structural validation only.")
            return 0
        c = next((c for c in data["candidates"] if c["id"] == args.candidate), None)
        if c is None:
            raise Invalid(f"Unknown candidate: {args.candidate}")
        if args.command == "assess":
            path = within(root, f"assessments/{c['id']}.json", False)
            if path.exists():
                raise Invalid("Assessment report already exists; preserve it before reassessment")
            write_json(path, assess(c))
            print(path)
        elif args.command == "stage":
            print(stage(root, c))
            write_json(registry, data)
        elif args.command == "fingerprint":
            print(tree_sha(within(root, c["artifact"])) if c["artifact"] else c["source"]["sha256"])
        elif args.command == "record-evidence":
            path = within(root, args.path)
            digest = tree_sha(within(root, c["artifact"])) if args.kind in BOUND and c["artifact"] else None
            entry = {"kind": args.kind, "path": args.path, "sha256": sha(path), "artifact_sha256": digest}
            errors = report_errors(root, c, entry, digest)
            if errors:
                raise Invalid("\n".join(errors))
            c["evidence"] = [e for e in c["evidence"] if e["kind"] != args.kind] + [entry]
            write_json(registry, data)
            print("Recorded reviewer-supplied evidence; no approval was inferred")
        elif args.command == "release-check":
            errors = release_errors(root, c)
            if errors:
                raise Invalid("\n".join(errors))
            print("Local release gates passed. Publication and external CI remain separate.")
        elif args.command == "package":
            print(package(root, c))
        return 0
    except (Invalid, OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
