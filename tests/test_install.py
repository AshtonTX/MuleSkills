"""Exercise the installer against isolated projects; never touch a real project."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROTECTED = (".github/copilot-instructions.md", ".github/mule/team-profile.md")
SHARED = ".github/instructions/dataweave.instructions.md"


def snapshot(root):
    """Record contents and links without following links outside the fixture."""
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            relative = str(path.relative_to(root))
            if path.is_symlink():
                result[relative] = ("link", os.readlink(path))
            elif path.is_dir():
                result[relative] = ("directory",)
            else:
                result[relative] = ("file", path.read_bytes())
    return result


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mule-installer-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = self.root / "guardrails with spaces"
        self.bundle.mkdir()
        shutil.copytree(ROOT / "overlay", self.bundle / "overlay")
        (self.bundle / "scripts").mkdir()
        self.script = self.bundle / "scripts/install.sh"
        shutil.copy2(ROOT / "scripts/install.sh", self.script)
        self.project = self.root / "mule project"
        self.project.mkdir()
        (self.project / "pom.xml").write_text("<project/>\n", encoding="utf-8")

    def install(self, *args, project=None, env=None):
        return subprocess.run(
            ["bash", str(self.script), str(project or self.project), *args],
            capture_output=True, text=True, env=env,
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_first_install_and_repeat_are_complete_and_idempotent(self):
        self.assert_success(self.install())
        source = self.bundle / "overlay"
        files = [path for path in source.rglob("*") if path.is_file()]
        for path in files:
            self.assertEqual((self.project / path.relative_to(source)).read_bytes(), path.read_bytes())
        before = snapshot(self.project)
        modified = {path: path.stat().st_mtime_ns for path in self.project.rglob("*") if path.is_file()}
        result = self.install()
        self.assert_success(result)
        self.assertIn(f"Added 0, updated 0, already current {len(files)}.", result.stdout)
        self.assertEqual(snapshot(self.project), before)
        self.assertEqual({path: path.stat().st_mtime_ns for path in modified}, modified)

    def test_default_preserves_changes_and_update_only_replaces_shared_files(self):
        self.assert_success(self.install())
        for relative in (*PROTECTED, SHARED):
            (self.project / relative).write_text("Project's custom rules\n", encoding="utf-8")
        unrelated = self.project / ".github/instructions/local.instructions.md"
        unrelated.write_text("Unrelated instructions\n", encoding="utf-8")
        before = snapshot(self.project)
        self.assert_success(self.install())
        self.assertEqual(snapshot(self.project), before)

        self.assert_success(self.install("--update"))
        self.assertEqual((self.project / SHARED).read_bytes(), (self.bundle / "overlay" / SHARED).read_bytes())
        for relative in PROTECTED:
            self.assertEqual((self.project / relative).read_text(), "Project's custom rules\n")
        self.assertEqual(unrelated.read_text(), "Unrelated instructions\n")

    def test_unsafe_destinations_fail_before_any_project_changes(self):
        cases = ("file-link", "dangling-link", "root-link", "parent-link", "file-directory", "parent-file")
        for number, case in enumerate(cases):
            for update in (False, True):
                with self.subTest(case=case, update=update):
                    project = self.root / f"unsafe-{number}-{update}"
                    project.mkdir()
                    outside = self.root / f"outside-{number}-{update}"
                    outside.mkdir()
                    (outside / "sentinel").write_text("Unrelated data\n", encoding="utf-8")
                    if case == "root-link":
                        (project / ".github").symlink_to(outside, target_is_directory=True)
                    elif case == "parent-link":
                        (project / ".github").mkdir()
                        (project / ".github/instructions").symlink_to(outside, target_is_directory=True)
                    elif case == "parent-file":
                        (project / ".github").mkdir()
                        (project / ".github/mule").write_text("Existing file\n", encoding="utf-8")
                    else:
                        destination = project / SHARED
                        destination.parent.mkdir(parents=True)
                        if case == "file-directory":
                            destination.mkdir()
                        else:
                            target = "sentinel" if case == "file-link" else "not-created"
                            destination.symlink_to(outside / target)
                    before = snapshot(project)
                    external_before = snapshot(outside)
                    result = self.install(*(["--update"] if update else []), project=project)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertEqual(snapshot(project), before)
                    self.assertEqual(snapshot(outside), external_before)

    def test_missing_and_empty_overlay_fail_without_writing(self):
        shutil.rmtree(self.bundle / "overlay")
        before = snapshot(self.project)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("overlay", result.stderr)
        self.assertEqual(snapshot(self.project), before)
        (self.bundle / "overlay/.github").mkdir(parents=True)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no files", result.stderr)
        self.assertEqual(snapshot(self.project), before)

    def test_source_symlinks_are_not_silently_skipped(self):
        source = self.bundle / "overlay" / SHARED
        source.unlink()
        source.symlink_to(self.root / "missing-source")
        before = snapshot(self.project)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symbolic link", result.stderr)
        self.assertEqual(snapshot(self.project), before)

    def test_enumeration_failure_is_not_reported_as_success(self):
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        fake_find = bin_dir / "find"
        fake_find.write_text("#!/usr/bin/env bash\nexit 9\n", encoding="utf-8")
        fake_find.chmod(0o755)
        env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"])
        before = snapshot(self.project)
        result = self.install(env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("enumerate overlay", result.stderr)
        self.assertEqual(snapshot(self.project), before)

    def test_invalid_arguments_and_missing_target_fail_without_writing(self):
        before = snapshot(self.project)
        self.assertEqual(self.install("--unknown").returncode, 2)
        missing = self.root / "missing-project"
        self.assertNotEqual(self.install(project=missing).returncode, 0)
        self.assertFalse(missing.exists())
        self.assertEqual(snapshot(self.project), before)

    def test_shell_checkout_stays_lf_with_autocrlf_enabled(self):
        attributes = ROOT / ".gitattributes"
        if attributes.is_file():
            shutil.copy2(attributes, self.bundle / ".gitattributes")

        def git(*args):
            subprocess.run(
                ["git", "-C", str(self.bundle), "-c", "core.autocrlf=true", "-c", "core.safecrlf=false", *args],
                check=True, capture_output=True, text=True,
            )

        git("init", "--quiet")
        git("add", "scripts/install.sh")
        if attributes.is_file():
            git("add", ".gitattributes")
        self.script.unlink()
        git("checkout-index", "scripts/install.sh")
        self.assertNotIn(b"\r\n", self.script.read_bytes())
        self.assert_success(self.install())


if __name__ == "__main__":
    unittest.main()
