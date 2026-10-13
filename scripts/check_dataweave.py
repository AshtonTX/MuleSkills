#!/usr/bin/env python3
"""Run retained native CLI observations, not Mule application tests.

Each tests/dataweave/*.dwl has either a .json expected result or a .error.txt
diagnostic that must accompany a nonzero exit. Requires an existing dw CLI;
never downloads tools or treats a missing executable as a successful skip.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path


FIXTURES = Path(__file__).resolve().parent.parent / "tests/dataweave"
LEVELS = ("2.4", "2.5", "2.6", "2.7", "2.8", "2.9")


def same_json(actual, expected):
    """Compare exact JSON numbers without treating False as zero."""
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        return actual.keys() == expected.keys() and all(
            same_json(actual[key], expected[key]) for key in expected
        )
    if isinstance(actual, list):
        return len(actual) == len(expected) and all(
            same_json(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected


def run_case(dw, level, script, output):
    expected_json = script.with_suffix(".json")
    expected_error = script.with_suffix(".error.txt")
    if expected_json.is_file() == expected_error.is_file():
        raise ValueError("fixture needs exactly one .json or .error.txt expectation")
    result = subprocess.run(
        [dw, "run", "--language-level", level, "-f", str(script), "-o", str(output)],
        capture_output=True, text=True, timeout=30,
    )
    diagnostic = result.stdout + result.stderr
    if expected_error.is_file():
        expected = expected_error.read_text(encoding="utf-8").strip()
        if not expected or result.returncode <= 0 or expected not in diagnostic:
            raise ValueError(
                f"expected a nonzero exit containing {expected!r}; "
                f"exit={result.returncode}\n{diagnostic}"
            )
    else:
        if result.returncode != 0:
            raise ValueError(f"CLI exit={result.returncode}\n{diagnostic}")
        actual = json.loads(output.read_text(encoding="utf-8"), parse_float=Decimal, parse_int=Decimal)
        expected = json.loads(expected_json.read_text(encoding="utf-8"), parse_float=Decimal, parse_int=Decimal)
        if not same_json(actual, expected):
            raise ValueError(f"expected {expected!r}\nactual   {actual!r}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dw", default="dw", help="existing CLI executable (default: dw on PATH)")
    parser.add_argument("--language-level", action="append", choices=LEVELS,
                        help="repeat to select levels; default: 2.4 through 2.9")
    args = parser.parse_args()
    levels = list(dict.fromkeys(args.language_level or LEVELS))
    scripts = sorted(FIXTURES.glob("*.dwl"))
    if not scripts:
        print(f"FAILED: no DataWeave fixtures in {FIXTURES}", file=sys.stderr)
        return 2
    try:
        version = subprocess.run([args.dw, "--version"], capture_output=True,
                                 text=True, timeout=10, check=True)
        if not version.stdout.strip():
            raise ValueError("CLI returned no version information")
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        print(f"FAILED: cannot run DataWeave CLI {args.dw!r}: {error}", file=sys.stderr)
        return 2
    print(version.stdout.strip(), flush=True)
    print("Native CLI observations; not a Mule/MUnit or older-engine compatibility test.", flush=True)
    passed = failed = 0
    with tempfile.TemporaryDirectory(prefix="guardrails-dataweave-") as directory:
        for level in levels:
            for script in scripts:
                output = Path(directory) / f"{level}-{script.stem}.json"
                try:
                    run_case(args.dw, level, script, output)
                except (OSError, subprocess.SubprocessError, ValueError) as error:
                    failed += 1
                    print(f"FAIL {level} {script.name}: {error}", flush=True)
                else:
                    passed += 1
                    print(f"PASS {level} {script.name}", flush=True)
    print(f"DataWeave: {passed} passed, {failed} failed, {len(levels)} language levels")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
