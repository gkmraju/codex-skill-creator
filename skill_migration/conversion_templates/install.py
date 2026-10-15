"""Copy this complete skill into an existing project's Codex discovery directory."""
import argparse
from pathlib import Path
import shutil
import sys

SKILL = Path(__file__).resolve().parents[1]


def linked(path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def install(project):
    project = Path(project).resolve()
    if not project.is_dir():
        raise ValueError("Project directory must already exist")
    target = project / ".agents" / "skills" / SKILL.name
    if target.exists() or linked(target):
        raise ValueError("Skill already exists; inspect before replacing it")
    if any(linked(p) for p in (project / ".agents", project / ".agents" / "skills")):
        raise ValueError("Linked destination refused")
    if linked(SKILL) or any(linked(p) for p in SKILL.rglob("*")):
        raise ValueError("Linked source refused")
    if target.resolve().is_relative_to(SKILL) or SKILL.is_relative_to(target.resolve()):
        raise ValueError("Source and destination must be disjoint")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SKILL, target)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    args = parser.parse_args()
    try:
        install(args.project)
        print("Installed " + SKILL.name + " in the project's .agents/skills directory")
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
