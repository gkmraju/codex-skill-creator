"""Run and preserve actual local verification results."""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "local-tooling"
OUT.mkdir(parents=True, exist_ok=True)
checks = [
    ("tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("registry", [sys.executable, "-m", "skill_migration", "validate"]),
    ("syntax", [sys.executable, "-m", "compileall", "-q", "skill_migration", "tests"]),
]
results = []
for name, command in checks:
    run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    log = OUT / (name + ".log")
    log.write_text(run.stdout + run.stderr, encoding="utf-8")
    results.append({"check": name, "command": command, "exit_code": run.returncode,
                    "log": log.relative_to(ROOT).as_posix()})
    print(f"{name}: exit {run.returncode} ({log.relative_to(ROOT).as_posix()})")
(OUT / "results.json").write_text(json.dumps({
    "recorded_at": datetime.now().astimezone().isoformat(),
    "scope": "Local tooling checks with synthetic fixtures; no real skill acceptance or external CI.",
    "checks": results,
}, indent=2) + "\n", encoding="utf-8")
raise SystemExit(0 if all(r["exit_code"] == 0 for r in results) else 1)
