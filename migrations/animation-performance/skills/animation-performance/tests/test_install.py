import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SKILL=Path(__file__).resolve().parents[1]
class InstallTests(unittest.TestCase):
    def run_install(self,project):
        return subprocess.run([sys.executable,"-B",str(SKILL/"scripts/install.py"),"--project",str(project)],capture_output=True,text=True)
    def test_installs_whole_skill_and_preserves_source_bytes(self):
        with tempfile.TemporaryDirectory(prefix="skill project ") as temporary:
            project=Path(temporary);proc=self.run_install(project)
            self.assertEqual(proc.returncode,0,proc.stderr)
            target=project/".agents/skills/animation-performance"
            for source in SKILL.rglob("*"):
                if source.is_file() and "__pycache__" not in source.parts:
                    self.assertEqual((target/source.relative_to(SKILL)).read_bytes(),source.read_bytes())
    def test_existing_install_refused_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temporary:
            project=Path(temporary);self.assertEqual(self.run_install(project).returncode,0)
            marker=project/".agents/skills/animation-performance/SKILL.md"
            marker.write_text("User-owned content",encoding="utf-8")
            self.assertEqual(self.run_install(project).returncode,2)
            self.assertEqual(marker.read_text(encoding="utf-8"),"User-owned content")
    def test_missing_project_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"missing"
            self.assertEqual(self.run_install(path).returncode,2)
            self.assertFalse(path.exists())
if __name__=="__main__":unittest.main()
