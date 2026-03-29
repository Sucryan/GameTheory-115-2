"""Smoke test for Problem 2 solver integration.

This test only checks that the main program can invoke the
Symmetric MDS-based IDS solver and print the required output line.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path


class Problem2SmokeTest(unittest.TestCase):
    """Basic integration check for Requirement 1-2 output path."""

    def test_problem2_solver_is_called(self) -> None:
        project_root = Path(__file__).resolve().parent
        script_path = project_root / "314581030_HW1_main.py"

        # A tiny undirected path graph with 3 nodes.
        # 0-1-2 in adjacency-matrix bit-string form.
        cmd = [
            sys.executable,
            str(script_path),
            "3",
            "010",
            "101",
            "010",
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
        self.assertIn("Requirement 1-2:", stdout)

        # Keep assertion flexible: only require a numeric cardinality output.
        self.assertRegex(
            stdout,
            r"the cardinality of Symmetric MDS-based IDS Game is \d+",
        )


if __name__ == "__main__":
    unittest.main()
