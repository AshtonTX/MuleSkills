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

    def test_reference_definition_with_destination_on_the_next_line_is_converted(self):
        rules = self.shared / "CLAUDE.md"
        rules.write_text(
            rules.read_text(encoding="utf-8")
            + "See [the profile][profile] and [the rules][dw].\n\n"
            + "[profile]:\n  .github/mule/team-profile.md\n"
            + '[dw]:\n    .claude/rules/dataweave.md\n    "DataWeave rules"\n',
            encoding="utf-8",
        )
        self.assertEqual(self.build().returncode, 0)
        generated = (self.github / ".github/copilot-instructions.md").read_text(encoding="utf-8")
        self.assertIn("\n[profile]:\n  mule/team-profile.md\n", generated)
        self.assertIn('\n[dw]:\n    instructions/dataweave.instructions.md\n    "DataWeave rules"\n', generated)
        self.assert_current()
        rules.write_text(rules.read_text(encoding="utf-8") + "[gone]:\n  .github/mule/missing.md\n", encoding="utf-8")
        result = self.build()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("does not point inside the layout", result.stdout)

    def test_paths_the_generator_cannot_see_as_links_are_rejected(self):
        # Anything that would leave a shared-layout path in the generated files fails the build.
        before = {p: p.read_bytes() for p in self.github.rglob("*") if p.is_file()}
        rules = self.shared / "CLAUDE.md"
        original = rules.read_text(encoding="utf-8")
        cases = {
            '<a href=".github/mule/team-profile.md">Profile</a>': "cannot convert HTML link",
            "<img src='.github/mule/diagram.png'>": "cannot convert HTML link",
            "Open the files in `.claude/rules/` by hand.": ".claude/rules/ is not written as a link",
            "This file is installed as CLAUDE.md at the project root.": "is not written as a link",
            "<a href=.github/mule/team-profile.md>Profile</a>": "cannot convert HTML link",
            "See .github/mule/team-profile.md for the project's facts.": "is not written as a link",
            "The profile is `./.github/mule/team-profile.md`.": "is not written as a link",
            "[a [b [c] d] e](.github/mule/team-profile.md)": "is not written as a link",
            "Open `.github/mule/`.": ".github/mule/ is not written as a link",
            "[a [b [c] d] e](.github/mule/team\\-profile.md)": "is not written as a link",
            "[a [b [c] d] e](.github/mule/team%2Dprofile.md)": "is not written as a link",
            "[a [b [c] d] e](.github/mule/team-profile.md?plain=1)": "is not written as a link",
            "The skill lives in the .claude folder.": ".claude is not written as a link",
        }
        for line, message in cases.items():
            with self.subTest(line=line):
                rules.write_text(original + line + "\n", encoding="utf-8")
                result = self.build()
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(message, result.stdout)
                self.assertEqual({p: p.read_bytes() for p in self.github.rglob("*") if p.is_file()}, before)
        rules.write_text(original + '<a href="https://example.invalid/">External</a> <a href="#top">Top</a>\n', encoding="utf-8")
        self.assertEqual(self.build().returncode, 0)
        # A shared-layout path given from the project root, in a file that is not at the root:
        # it does not resolve from where the file sits, so the last guard is what catches it.
        rule = self.shared / ".claude/rules/maven.md"
        rule.write_text(
            rule.read_text(encoding="utf-8") + "- Open `.claude/rules/dataweave.md` from the project root.\n",
            encoding="utf-8",
        )
        result = self.build()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("would still mention .claude/", result.stdout)

    def test_link_label_with_nested_brackets_is_converted(self):
        rules = self.shared / "CLAUDE.md"
        rules.write_text(
            rules.read_text(encoding="utf-8") + "[the [project] profile](.github/mule/team-profile.md)\n",
            encoding="utf-8",
        )
        self.assertEqual(self.build().returncode, 0)
        generated = (self.github / ".github/copilot-instructions.md").read_text(encoding="utf-8")
        self.assertIn("[the [project] profile](mule/team-profile.md)\n", generated)

    def test_path_text_that_stays_correct_in_both_layouts_is_allowed(self):
        # A sibling that keeps its name, and a path that is not relative to this file, need no conversion.
        recipes = self.shared / ".github/mule/task-recipes.md"
        recipes.write_text(recipes.read_text(encoding="utf-8") + "Fill in team-profile.md first.\n", encoding="utf-8")
        rule = self.shared / ".claude/rules/maven.md"
        rule.write_text(
            rule.read_text(encoding="utf-8") + "- Record the result in `.github/mule/team-profile.md` at the project root.\n",
            encoding="utf-8",
        )
        # A folder whose relative path is the same in both layouts.
        skill = self.shared / ".claude/skills/team-mule-guardrails/SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "The detail is in the references/ folder.\n", encoding="utf-8")
        self.assertEqual(self.build().returncode, 0)
        self.assert_current()
        rule.write_text(rule.read_text(encoding="utf-8") + "- See dataweave.md for scripts.\n", encoding="utf-8")
        result = self.build()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("dataweave.md is not written as a link", result.stdout)

    def test_symbolic_links_are_refused_before_anything_is_written(self):
        outside = self.root / "outside"
        outside.mkdir()
        victim = outside / "victim.md"
        generated = self.github / ".github/instructions/maven.instructions.md"
        folder = self.github / ".github/skills"
        source_folder = self.shared / ".claude/skills"

        def link_output_file():
            generated.unlink()
            generated.symlink_to(victim)

        def link_output_folder():
            shutil.rmtree(folder)
            folder.symlink_to(outside, target_is_directory=True)

        def link_output_root():
            shutil.rmtree(self.github)
            self.github.symlink_to(outside, target_is_directory=True)

        def link_source_folder():
            shutil.move(str(source_folder), str(outside / "skills"))
            source_folder.symlink_to(outside / "skills", target_is_directory=True)

        for name, make_link in (("output file", link_output_file), ("output folder", link_output_folder),
                                ("output root", link_output_root), ("source folder", link_source_folder)):
            with self.subTest(case=name):
                # rmtree removes a link itself and never what it points to.
                shutil.rmtree(self.root / "overlay")
                shutil.rmtree(outside)
                outside.mkdir()
                victim.write_text("Unrelated data\n", encoding="utf-8")
                shutil.copytree(ROOT / "overlay", self.root / "overlay")
                # Make the source differ, so an unguarded build would write through the link.
                rule = self.shared / ".claude/rules/maven.md"
                rule.write_text(rule.read_text(encoding="utf-8") + "- A new rule.\n", encoding="utf-8")
                make_link()
                before = {str(p.relative_to(outside)): p.read_bytes() for p in outside.rglob("*") if p.is_file()}
                for args in (("--check",), ()):
                    result = self.build(*args)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn("symbolic links are not supported", result.stdout)
                    self.assertEqual(
                        {str(p.relative_to(outside)): p.read_bytes() for p in outside.rglob("*") if p.is_file()}, before
                    )
                    self.assertEqual(victim.read_text(encoding="utf-8"), "Unrelated data\n")

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
