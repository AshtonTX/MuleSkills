"""Check that overlay/github is a faithful, current rendering of overlay/shared."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mule-build-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "overlay", self.root / "overlay")
        (self.root / "scripts").mkdir()
        self.script = self.root / "scripts/build.py"
        shutil.copy2(ROOT / "scripts/build.py", self.script)
        self.shared = self.root / "overlay/shared"
        self.github = self.root / "overlay/github"

    def build(self, *args):
        return subprocess.run([sys.executable, str(self.script), *args], capture_output=True, text=True)

    def assert_current(self):
        result = self.build("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_stale(self, expected):
        result = self.build("--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(expected, result.stdout)

    def test_committed_github_layout_is_current(self):
        self.assert_current()

    def test_same_files_in_both_layouts(self):
        shared = [p for p in self.shared.rglob("*") if p.is_file()]
        github = [p for p in self.github.rglob("*") if p.is_file()]
        self.assertEqual(len(shared), len(github))
        self.assertTrue((self.github / ".github/copilot-instructions.md").is_file())
        self.assertFalse((self.github / "CLAUDE.md").exists())
        self.assertFalse((self.github / ".claude").exists())

    def test_scope_key_and_links_are_converted(self):
        rule = (self.github / ".github/instructions/dataweave.instructions.md").read_text(encoding="utf-8")
        self.assertIn('\napplyTo: "**/*.dwl,', rule)
        self.assertNotIn("\npaths:", rule)
        self.assertIn("](../skills/team-mule-guardrails/references/dataweave-performance.md)", rule)
        source = (self.shared / ".claude/rules/dataweave.md").read_text(encoding="utf-8")
        self.assertEqual(source.replace("\npaths:", "\napplyTo:", 1), rule)

        skill = (self.github / ".github/skills/team-mule-guardrails/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("](../../instructions/mule-xml.instructions.md)", skill)
        self.assertIn("](../../mule/team-profile.md)", skill)
        rules = (self.github / ".github/copilot-instructions.md").read_text(encoding="utf-8")
        self.assertIn("](mule/team-profile.md)", rules)
        self.assertIn("](instructions/)", rules)
        recipes = (self.github / ".github/mule/task-recipes.md").read_text(encoding="utf-8")
        self.assertIn("](../instructions/maven.instructions.md)", recipes)

    def test_edit_in_shared_makes_github_stale_until_rebuilt(self):
        rule = self.shared / ".claude/rules/maven.md"
        rule.write_text(rule.read_text(encoding="utf-8") + "- A new rule.\n", encoding="utf-8")
        self.assert_stale("differs or missing: overlay/github/.github/instructions/maven.instructions.md")
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_current()
        generated = (self.github / ".github/instructions/maven.instructions.md").read_text(encoding="utf-8")
        self.assertTrue(generated.endswith("- A new rule.\n"))

    def test_hand_edit_in_github_is_detected_and_overwritten(self):
        generated = self.github / ".github/instructions/munit.instructions.md"
        original = generated.read_bytes()
        generated.write_bytes(original + b"Edited in the wrong place.\n")
        self.assert_stale("munit.instructions.md")
        self.assertEqual(self.build().returncode, 0)
        self.assertEqual(generated.read_bytes(), original)

    def test_new_and_removed_files_follow_the_source(self):
        extra = self.shared / ".claude/rules/logging.md"
        extra.write_text(
            '---\npaths: "**/log4j2.xml"\ndescription: "Logging rules."\n---\n\nSee [the profile](../../.github/mule/team-profile.md).\n',
            encoding="utf-8",
        )
        self.assertEqual(self.build().returncode, 0)
        generated = self.github / ".github/instructions/logging.instructions.md"
        self.assertEqual(
            generated.read_text(encoding="utf-8"),
            '---\napplyTo: "**/log4j2.xml"\ndescription: "Logging rules."\n---\n\nSee [the profile](../mule/team-profile.md).\n',
        )
        extra.unlink()
        self.assert_stale("no longer generated: overlay/github/.github/instructions/logging.instructions.md")
        self.assertEqual(self.build().returncode, 0)
        self.assertFalse(generated.exists())
        self.assert_current()

    def test_crlf_source_is_converted(self):
        rule = self.shared / ".claude/rules/maven.md"
        rule.write_bytes(rule.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(self.build().returncode, 0)
        generated = (self.github / ".github/instructions/maven.instructions.md").read_bytes()
        self.assertTrue(generated.startswith(b"---\r\napplyTo: "))

    def test_unconvertible_source_fails_without_writing(self):
        before = {p: p.read_bytes() for p in self.github.rglob("*") if p.is_file()}
        rule = self.shared / ".claude/rules/maven.md"
        original = rule.read_text(encoding="utf-8")
        cases = {
            "link out of the layout": (original + "[Out](../../../../README.md)\n", "does not point inside the layout"),
            "link to a missing file": (original + "[Gone](missing.md)\n", "does not point inside the layout"),
            "no scope key": (original.replace("\npaths:", "\nglobs:", 1), "must set paths exactly once"),
            "no front matter": ("# Rules\n", "no front matter"),
        }
        for name, (text, message) in cases.items():
            with self.subTest(case=name):
                rule.write_text(text, encoding="utf-8")
                result = self.build()
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(message, result.stdout)
                self.assertEqual({p: p.read_bytes() for p in self.github.rglob("*") if p.is_file()}, before)
        stray = self.shared / "notes.md"
        rule.write_text(original, encoding="utf-8")
        stray.write_text("Notes\n", encoding="utf-8")
        result = self.build()
        self.assertEqual(result.returncode, 1)
        self.assertIn("no place for this path in the GitHub layout", result.stdout)

    def test_titled_links_are_converted(self):
        rules = self.shared / "CLAUDE.md"
        rules.write_text(
            rules.read_text(encoding="utf-8")
            + '[Profile](.github/mule/team-profile.md "Project facts")\n'
            + "[Rules](.claude/rules/dataweave.md#correctness 'DataWeave')\n"
            + "[Recipes](.github/mule/task-recipes.md (Prompts))\n"
            + '[Docs](https://example.invalid/a "External")\n',
            encoding="utf-8",
        )
        self.assertEqual(self.build().returncode, 0)
        generated = (self.github / ".github/copilot-instructions.md").read_text(encoding="utf-8")
        self.assertIn('[Profile](mule/team-profile.md "Project facts")\n', generated)
        self.assertIn("[Rules](instructions/dataweave.instructions.md#correctness 'DataWeave')\n", generated)
        self.assertIn("[Recipes](mule/task-recipes.md (Prompts))\n", generated)
        self.assertIn('[Docs](https://example.invalid/a "External")\n', generated)
        self.assert_current()

    def test_reference_style_definitions_are_converted(self):
        rules = self.shared / "CLAUDE.md"
        rules.write_text(
            rules.read_text(encoding="utf-8")
            + "See [the profile][profile], [the rules][dw] and [the docs][docs].[^note]\n\n"
            + "[profile]: .github/mule/team-profile.md\n"
            + '  [dw]: .claude/rules/dataweave.md#correctness "DataWeave rules"\n'
            + "[docs]: https://example.invalid/a\n"
            + "[^note]: A footnote, not a link.\n",
            encoding="utf-8",
        )
        self.assertEqual(self.build().returncode, 0)
        generated = (self.github / ".github/copilot-instructions.md").read_text(encoding="utf-8")
        self.assertIn("\n[profile]: mule/team-profile.md\n", generated)
        self.assertIn('\n  [dw]: instructions/dataweave.instructions.md#correctness "DataWeave rules"\n', generated)
        self.assertIn("\n[docs]: https://example.invalid/a\n", generated)
        self.assertIn("\n[^note]: A footnote, not a link.\n", generated)
        self.assertIn("See [the profile][profile], [the rules][dw] and [the docs][docs].[^note]\n", generated)
        self.assert_current()

    def test_reference_style_definitions_that_cannot_be_converted_are_rejected(self):
        before = {p: p.read_bytes() for p in self.github.rglob("*") if p.is_file()}
        rules = self.shared / "CLAUDE.md"
        original = rules.read_text(encoding="utf-8")
        cases = {
            "[profile]: <.github/mule/team-profile.md>": "cannot convert link",
            "[profile]: .github/mule/team%2Dprofile.md": "cannot convert link",
            "[profile]: .github/mule/missing.md": "does not point inside the layout",
            "[profile]: ../outside.md": "does not point inside the layout",
        }
        for definition, message in cases.items():
            with self.subTest(definition=definition):
                rules.write_text(original + "[Profile][profile]\n\n" + definition + "\n", encoding="utf-8")
                result = self.build()
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(message, result.stdout)
                self.assertEqual({p: p.read_bytes() for p in self.github.rglob("*") if p.is_file()}, before)

    def test_link_forms_that_cannot_be_converted_are_rejected(self):
        # Copying one of these unchanged would leave a link that points nowhere, or somewhere else.
        before = {p: p.read_bytes() for p in self.github.rglob("*") if p.is_file()}
        rules = self.shared / "CLAUDE.md"
        original = rules.read_text(encoding="utf-8")
        (self.shared / ".github/mule/notes(v2).md").write_text("Notes\n", encoding="utf-8")
        links = (
            '[Profile](<.github/mule/team-profile.md> "Project facts")',
            "[Profile](<.github/mule/team-profile.md>)",
            "[Notes](.github/mule/notes(v2).md)",
            "[Notes](.github/mule/notes\\(v2\\).md)",
            "[Profile](.github/mule/team%2Dprofile.md)",
            "[Profile](.github/mule/team-profile.md?plain=1)",
        )
        for link in links:
            with self.subTest(link=link):
                rules.write_text(original + link + "\n", encoding="utf-8")
                result = self.build()
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("cannot convert link", result.stdout)
                self.assertEqual({p: p.read_bytes() for p in self.github.rglob("*") if p.is_file()}, before)

    def test_unknown_argument_is_rejected(self):
        self.assertEqual(self.build("--write").returncode, 2)


if __name__ == "__main__":
    unittest.main()
