"""Exercise the installer against isolated projects; never touch a real project.

Every test runs for both layouts: shared (the default) and github.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


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


class LayoutInstallerTests:
    """Shared test body; the subclasses below name the layout under test."""

    layout = ""
    layout_args = ()
    other = ""
    other_args = ()
    rules_file = ""        # this layout's repository-wide rules, owned by the project once installed
    other_rules_file = ""
    shared_rule = ""       # a rule file that --update replaces
    other_shared_rule = ""
    unrelated = ""         # a project file in the same folder that the installer must leave alone

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
        self.source = self.bundle / "overlay" / self.layout
        self.protected = (self.rules_file, ".github/mule/team-profile.md")
        self.project = self.root / "mule project"
        self.project.mkdir()
        (self.project / "pom.xml").write_text("<project/>\n", encoding="utf-8")

    def run_script(self, *args, project=None, env=None):
        return subprocess.run(
            ["bash", str(self.script), str(project or self.project), *args],
            capture_output=True, text=True, env=env,
        )

    def install(self, *args, project=None, env=None):
        return self.run_script(*self.layout_args, *args, project=project, env=env)

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def new_project(self, name):
        project = self.root / name
        project.mkdir()
        (project / "pom.xml").write_text("<project/>\n", encoding="utf-8")
        return project

    def test_first_install_and_repeat_are_complete_and_idempotent(self):
        self.assert_success(self.install())
        files = [path for path in self.source.rglob("*") if path.is_file()]
        for path in files:
            self.assertEqual((self.project / path.relative_to(self.source)).read_bytes(), path.read_bytes())
        installed = [path for path in self.project.rglob("*") if path.is_file() and path.name != "pom.xml"]
        self.assertEqual(len(installed), len(files))
        before = snapshot(self.project)
        modified = {path: path.stat().st_mtime_ns for path in self.project.rglob("*") if path.is_file()}
        result = self.install()
        self.assert_success(result)
        self.assertIn(f"Added 0, updated 0, already current {len(files)}.", result.stdout)
        self.assertEqual(snapshot(self.project), before)
        self.assertEqual({path: path.stat().st_mtime_ns for path in modified}, modified)

    def test_default_preserves_changes_and_update_only_replaces_shared_files(self):
        self.assert_success(self.install())
        for relative in (*self.protected, self.shared_rule):
            (self.project / relative).write_text("Project's custom rules\n", encoding="utf-8")
        unrelated = self.project / self.unrelated
        unrelated.write_text("Unrelated instructions\n", encoding="utf-8")
        before = snapshot(self.project)
        self.assert_success(self.install())
        self.assertEqual(snapshot(self.project), before)

        self.assert_success(self.install("--update"))
        self.assertEqual((self.project / self.shared_rule).read_bytes(), (self.source / self.shared_rule).read_bytes())
        for relative in self.protected:
            self.assertEqual((self.project / relative).read_text(), "Project's custom rules\n")
        self.assertEqual(unrelated.read_text(), "Unrelated instructions\n")

    def test_unsafe_destinations_fail_before_any_project_changes(self):
        cases = ("file-link", "dangling-link", "root-link", "parent-link", "file-directory", "parent-file")
        top, parent = Path(self.shared_rule).parts[0], Path(self.shared_rule).parent
        for number, case in enumerate(cases):
            for update in (False, True):
                with self.subTest(case=case, update=update):
                    project = self.root / f"unsafe-{number}-{update}"
                    project.mkdir()
                    outside = self.root / f"outside-{number}-{update}"
                    outside.mkdir()
                    (outside / "sentinel").write_text("Unrelated data\n", encoding="utf-8")
                    if case == "root-link":
                        (project / top).symlink_to(outside, target_is_directory=True)
                    elif case == "parent-link":
                        (project / top).mkdir()
                        (project / parent).symlink_to(outside, target_is_directory=True)
                    elif case == "parent-file":
                        (project / ".github").mkdir()
                        (project / ".github/mule").write_text("Existing file\n", encoding="utf-8")
                    else:
                        destination = project / self.shared_rule
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
        (self.source / ".github").mkdir(parents=True)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no files", result.stderr)
        self.assertEqual(snapshot(self.project), before)

    def test_source_symlinks_are_not_silently_skipped(self):
        source = self.source / self.shared_rule
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
        self.assertEqual(self.run_script("--layout", "nope").returncode, 2)
        self.assertEqual(self.run_script("--layout").returncode, 2)
        missing = self.root / "missing-project"
        self.assertNotEqual(self.install(project=missing).returncode, 0)
        self.assertFalse(missing.exists())
        self.assertEqual(snapshot(self.project), before)

    def test_layout_can_be_given_with_an_equals_sign(self):
        self.assert_success(self.run_script(f"--layout={self.layout}"))
        self.assertTrue((self.project / self.shared_rule).is_file())
        self.assertFalse((self.project / self.other_shared_rule).exists())

    def test_installing_beside_the_other_layout_is_refused_without_writing(self):
        # Copilot reads both sets of rule files, so both together load every rule twice.
        self.assert_success(self.run_script(*self.other_args))
        before = snapshot(self.project)
        for update in (False, True):
            with self.subTest(update=update):
                result = self.install(*(["--update"] if update else []))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(f"already has rule files from the '{self.other}' layout", result.stderr)
                self.assertIn(self.other_shared_rule, result.stderr)
                self.assertNotIn(".github/mule/", result.stderr)
                self.assertEqual(snapshot(self.project), before)

    def test_other_layouts_rules_file_alone_is_noted_not_refused(self):
        # That file may be the project's own, so it is left alone and pointed out.
        own = self.project / self.other_rules_file
        own.parent.mkdir(parents=True, exist_ok=True)
        own.write_text("Project's own rules\n", encoding="utf-8")
        result = self.install()
        self.assert_success(result)
        self.assertIn(f"Note: this project also has {self.other_rules_file}", result.stdout)
        self.assertEqual(own.read_text(), "Project's own rules\n")
        self.assertTrue((self.project / self.shared_rule).is_file())

    def test_shell_checkout_stays_lf_with_autocrlf_enabled(self):
        attributes = ROOT / ".gitattributes"
        if attributes.is_file():
            shutil.copy2(attributes, self.bundle / ".gitattributes")

        def git(*args):
            subprocess.run(
                ["git", "-C", str(self.bundle), "-c", "core.autocrlf=true", "-c", "core.safecrlf=false", *args],
                check=True, capture_output=True, text=True,
            )

        rule = f"overlay/{self.layout}/{self.shared_rule}"
        git("init", "--quiet")
        git("add", "scripts/install.sh", rule)
        if attributes.is_file():
            git("add", ".gitattributes")
        self.script.unlink()
        (self.bundle / rule).unlink()
        git("checkout-index", "scripts/install.sh", rule)
        self.assertNotIn(b"\r\n", self.script.read_bytes())
        # Installed rule files are counted against a byte limit, so they stay LF too.
        self.assertNotIn(b"\r\n", (self.bundle / rule).read_bytes())
        self.assert_success(self.install())


class SharedLayoutInstallerTests(LayoutInstallerTests, unittest.TestCase):
    layout = "shared"
    layout_args = ()
    other = "github"
    other_args = ("--layout", "github")
    rules_file = "CLAUDE.md"
    other_rules_file = ".github/copilot-instructions.md"
    shared_rule = ".claude/rules/dataweave.md"
    other_shared_rule = ".github/instructions/dataweave.instructions.md"
    unrelated = ".claude/rules/local.md"

    def test_shared_is_the_default_layout(self):
        self.assert_success(self.run_script())
        for relative in ("CLAUDE.md", ".claude/rules/mule-xml.md", ".claude/skills/team-mule-guardrails/SKILL.md",
                         ".github/mule/team-profile.md"):
            self.assertTrue((self.project / relative).is_file(), relative)
        self.assertFalse((self.project / ".github/instructions").exists())
        self.assertFalse((self.project / ".github/copilot-instructions.md").exists())


class GithubLayoutInstallerTests(LayoutInstallerTests, unittest.TestCase):
    layout = "github"
    layout_args = ("--layout", "github")
    other = "shared"
    other_args = ()
    rules_file = ".github/copilot-instructions.md"
    other_rules_file = "CLAUDE.md"
    shared_rule = ".github/instructions/dataweave.instructions.md"
    other_shared_rule = ".claude/rules/dataweave.md"
    unrelated = ".github/instructions/local.instructions.md"


if __name__ == "__main__":
    unittest.main()
