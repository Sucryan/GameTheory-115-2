"""Minimum smoke test for the HW1 graph game CLI skeleton.

This test intentionally verifies only the given sample case and output shape.
TODO(student): expand to additional graph instances after implementing real solvers.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


class MinimumCLITest(unittest.TestCase):
    """Given test case minimum verification target."""

    def test_given_sample_case(self) -> None:
        project_root = Path(__file__).resolve().parent
        script_path = project_root / "314581030_HW1_main.py"

        cmd = [
            sys.executable,
            str(script_path),
            "6",
            "010000",
            "101100",
            "010010",
            "010010",
            "001101",
            "000010",
        ]

        completed = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            completed.returncode,
            0,
            msg=f"Expected exit code 0, got {completed.returncode}. stderr={completed.stderr}",
        )

        stdout = completed.stdout
        self.assertIn("the cardinality of MIS-based IDS Game is 2", stdout)
        self.assertIn("the cardinality of Symmetric MDS-based IDS Game is 2", stdout)
        self.assertIn("the cardinality of Matching Game is 2", stdout)


if __name__ == "__main__":
    unittest.main()
