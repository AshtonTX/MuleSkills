"""Check accepted metadata and failures that would otherwise reach an install."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mule-checker-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "overlay", self.root / "overlay")
        (self.root / "scripts").mkdir()
        self.script = self.root / "scripts/check.py"
        shutil.copy2(ROOT / "scripts/check.py", self.script)
        self.instruction = self.root / "overlay/.github/instructions/dataweave.instructions.md"
        self.skill = self.root / "overlay/.github/skills/team-mule-guardrails/SKILL.md"
        self.recipes = self.root / "overlay/.github/mule/task-recipes.md"

    def check(self):
        return subprocess.run([sys.executable, str(self.script)], capture_output=True, text=True)

    def assert_valid(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_invalid(self, expected):
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(expected, result.stdout)

    def test_current_overlay_is_valid(self):
        self.assert_valid()

    def test_malformed_metadata_is_rejected(self):
        values = (
            'applyTo: "**/*.dwl',
            "applyTo: '**/*.dwl",
            'applyTo: "**/*.dwl" trailing garbage',
            'applyTo:"**/*.dwl"',
            'applyTo: "**/*.dwl"\napplyTo: "**/*.xml"',
            'applyTo: |\n  **/*.dwl',
            'applyTo: ["**/*.dwl"]',
            'applyTo: true',
            'applyTo: null',
            'applyTo: *unresolved-alias',
            'applyTo: "bad\\qescape"',
        )
        for value in values:
            with self.subTest(value=value):
                self.instruction.write_text(f"---\n{value}\n---\n", encoding="utf-8")
                self.assert_invalid("dataweave.instructions.md:")

    def test_empty_metadata_and_empty_patterns_are_rejected(self):
        values = ('', '# no value', '"" # empty', "''", '"   "', '"**/*.dwl,"')
        for value in values:
            with self.subTest(value=value):
                self.instruction.write_text(f"---\napplyTo: {value}\n---\n", encoding="utf-8")
                self.assert_invalid("applyTo must set nonempty glob patterns")

    def test_supported_quotes_comments_and_crlf_are_valid(self):
        self.instruction.write_bytes(
            b"---\r\n# Comment\r\n\r\napplyTo: '**/*.dwl' # Files\r\ndescription: 'DataWeave rules.'\r\n---\r\n"
        )
        self.skill.write_text(
            "---\nname: 'team-mule-guardrails'\n"
            "description: 'Use the team''s rules: inspect Mule changes.' # Comment\n---\n",
            encoding="utf-8",
        )
        self.assert_valid()
        self.skill.write_text(
            '---\nname: "team-mule-guardrails"\n'
            'description: "Review \\"Mule\\" changes."\n---\n', encoding="utf-8",
        )
        self.assert_valid()

    def test_skill_requires_matching_name_and_nonempty_description(self):
        self.skill.write_text("---\nname: other-skill\ndescription: Review Mule changes\n---\n", encoding="utf-8")
        self.assert_invalid("name must be 'team-mule-guardrails'")
        self.skill.write_text("---\nname: team-mule-guardrails\ndescription: ' ' # Empty\n---\n", encoding="utf-8")
        self.assert_invalid("description is required")
        self.skill.write_text(
            "---\nname: team-mule-guardrails\ndescription: Review Mule\ndescription: Again\n---\n",
            encoding="utf-8",
        )
        self.assert_invalid("duplicate metadata key 'description'")

    def test_nested_instructions_are_checked(self):
        nested = self.instruction.parent / "nested/additional.instructions.md"
        nested.parent.mkdir()
        nested.write_text("# Missing metadata\n", encoding="utf-8")
        self.assert_invalid("nested/additional.instructions.md: front matter")
        nested.write_text('---\napplyTo: "**/*.dwl"\n---\n', encoding="utf-8")
        self.assert_invalid("nested/additional.instructions.md: description is required")
        nested.write_text('---\napplyTo: "**/*.dwl"\ndescription: "Extra rules."\n---\n', encoding="utf-8")
        self.assert_valid()

    def test_overlay_file_too_large_for_one_read_is_rejected(self):
        limit = 18_000
        head = '---\napplyTo: "**/*.dwl"\ndescription: "DataWeave rules."\n---\n'
        self.instruction.write_text(head + "x" * (limit - len(head)), encoding="utf-8")
        self.assert_valid()
        self.instruction.write_text(head + "x" * (limit - len(head) + 1), encoding="utf-8")
        self.assert_invalid(f"{limit + 1} bytes exceeds {limit}")
        reference = self.skill.parent / "references/dataweave-performance.md"
        self.instruction.write_text(head, encoding="utf-8")
        reference.write_text("x" * (limit + 1), encoding="utf-8")
        self.assert_invalid("references/dataweave-performance.md")

    def test_instruction_description_is_required(self):
        self.instruction.write_text('---\napplyTo: "**/*.dwl"\ndescription: "DataWeave rules."\n---\n', encoding="utf-8")
        self.assert_valid()
        for front_matter in ('applyTo: "**/*.dwl"', 'applyTo: "**/*.dwl"\ndescription: " "'):
            with self.subTest(front_matter=front_matter):
                self.instruction.write_text(f"---\n{front_matter}\n---\n", encoding="utf-8")
                self.assert_invalid("dataweave.instructions.md: description is required")

    def test_missing_reference_file_is_reported(self):
        (self.skill.parent / "references/mule-connectors.md").unlink()
        self.assert_invalid("missing overlay file:")

    def test_missing_required_file_is_reported(self):
        self.instruction.unlink()
        self.assert_invalid("missing overlay file:")

    def test_broken_inline_links_with_titles_are_checked(self):
        links = (
            '[Missing](not-present.md)',
            '[Missing](not-present.md "Title")',
            "[Missing](not-present.md 'Title')",
            '[Missing](not-present.md (Title))',
            '[Missing](<not present.md> "Title")',
        )
        for link in links:
            with self.subTest(link=link):
                self.recipes.write_text(link + "\n", encoding="utf-8")
                self.assert_invalid("broken link")

    def test_existing_titled_and_encoded_links_are_valid(self):
        (self.recipes.parent / "extra notes.md").write_text("Notes\n", encoding="utf-8")
        (self.recipes.parent / "notes(v2).md").write_text("Notes\n", encoding="utf-8")
        self.recipes.write_text(
            '[Profile](team-profile.md "Project facts")\n'
            '[Notes](<extra notes.md> "Notes")\n'
            '[Notes](extra%20notes.md#heading)\n'
            '[Notes](notes(v2).md)\n'
            '[Notes](notes\\(v2\\).md)\n'
            '[Website](HTTPS://example.invalid/ "External")\n'
            '[Heading](#heading)\n', encoding="utf-8",
        )
        self.assert_valid()

    def test_escaped_punctuation_link_checks_the_decoded_path(self):
        destination = self.recipes.parent / "some(file).md"
        destination.write_text("Notes\n", encoding="utf-8")
        self.recipes.write_text('[File](some\\(file\\).md)\n', encoding="utf-8")
        self.assert_valid()
        destination.unlink()
        self.assert_invalid("broken link some(file).md")

    def test_only_markdown_ascii_punctuation_is_unescaped_before_percent_decoding(self):
        for name in ("someq.md", "some\u2014.md", "some(file).md"):
            (self.recipes.parent / name).write_text("Notes\n", encoding="utf-8")
        targets = (r"some\q.md", "some\\\u2014.md", "some%5C%28file%5C%29.md")
        for target in targets:
            with self.subTest(target=target):
                self.recipes.write_text(f"[File]({target})\n", encoding="utf-8")
                self.assert_invalid("broken link")

    def test_titled_link_cannot_leave_overlay(self):
        (self.root / "outside.md").write_text("Not installed\n", encoding="utf-8")
        self.recipes.write_text('[Outside](../../../outside.md "Title")\n', encoding="utf-8")
        self.assert_invalid("link leaves overlay/")


if __name__ == "__main__":
    unittest.main()
