"""Check result comparison through the runner's CLI without installing DataWeave."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class DataWeaveRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mule-dataweave-runner-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "scripts").mkdir()
        self.runner = self.root / "scripts/check_dataweave.py"
        shutil.copy2(ROOT / "scripts/check_dataweave.py", self.runner)
        self.fixtures = self.root / "tests/dataweave"
        self.fixtures.mkdir(parents=True)
        (self.fixtures / "probe.dwl").write_text(
            "%dw 2.0\noutput application/json\n---\n{}\n", encoding="utf-8",
        )
        self.dw = self.root / "fake-dw"
        self.dw.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "from pathlib import Path\n"
            "if sys.argv[1:] == ['--version']:\n"
            "    print('Fake DataWeave CLI for runner tests')\n"
            "elif sys.argv[1] == 'run':\n"
            "    output = Path(sys.argv[sys.argv.index('-o') + 1])\n"
            "    output.write_bytes(Path(__file__).with_name('actual.json').read_bytes())\n"
            "else:\n"
            "    sys.exit(2)\n",
            encoding="utf-8",
        )
        self.dw.chmod(0o755)

    def run_comparison(self, expected, actual):
        (self.fixtures / "probe.json").write_text(expected, encoding="utf-8")
        (self.root / "actual.json").write_text(actual, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(self.runner), "--dw", str(self.dw), "--language-level", "2.9"],
            capture_output=True, text=True, timeout=10,
        )

    def assert_comparison_failed(self, result):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL 2.9 probe.dwl: expected", result.stdout)
        self.assertIn("actual", result.stdout)
        self.assertIn("DataWeave: 0 passed, 1 failed", result.stdout)

    def test_small_decimal_difference_fails(self):
        # Keep the exact JSON text: Python floats would erase this difference.
        result = self.run_comparison(
            '{"decimalSum": 0.3}', '{"decimalSum": 0.30000000000000001}',
        )
        self.assert_comparison_failed(result)

    def test_booleans_and_numbers_are_distinct(self):
        for expected, actual in (("true", "1"), ("1", "true"), ("false", "0"), ("0", "false")):
            with self.subTest(expected=expected, actual=actual):
                result = self.run_comparison(
                    '{"value": ' + expected + '}', '{"value": ' + actual + '}',
                )
                self.assert_comparison_failed(result)

    def test_reordered_object_keys_pass(self):
        result = self.run_comparison(
            '{"first": 1, "nested": {"a": true, "b": [2, 3]}, "empty": null}',
            '{"empty": null, "nested": {"b": [2, 3], "a": true}, "first": 1}',
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS 2.9 probe.dwl", result.stdout)
        self.assertIn("DataWeave: 1 passed, 0 failed", result.stdout)


if __name__ == "__main__":
    unittest.main()
