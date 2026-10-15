"""Install this whole skill into an existing project's .agents/skills directory."""
import argparse
from pathlib import Path
import shutil
import sys

SKILL = Path(__file__).resolve().parents[1]
def linked(path):
    return path.is_symlink() or (hasattr(path,"is_junction") and path.is_junction())

def install(project):
    project = Path(project).resolve()
    if not project.is_dir():
        raise ValueError("Project directory must already exist")
    target = project/".agents"/"skills"/SKILL.name
    if target.exists() or linked(target):
        raise ValueError("Skill already exists; inspect it before updating")
    for parent in (project/".agents", project/".agents"/"skills"):
        if linked(parent):
            raise ValueError("Linked installation path refused")
    if linked(SKILL) or any(linked(path) for path in SKILL.rglob("*")):
        raise ValueError("Linked skill resources refused")
    if target.resolve().is_relative_to(SKILL) or SKILL.is_relative_to(target.resolve()):
        raise ValueError("Source and installation must be disjoint")
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(SKILL,target)
    return target

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        target=install(args.project)
        print("Installed animation-performance in the project's .agents/skills folder")
        return 0
    except (ValueError,OSError) as exc:
        print("ERROR: "+str(exc),file=sys.stderr)
        return 2
if __name__=="__main__":
    raise SystemExit(main())
