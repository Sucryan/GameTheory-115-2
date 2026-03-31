#!/usr/bin/env python3
"""Emit predefined small graphs in ws_generator-compatible format.

This script is designed for checker.py integration. checker.py invokes a
generator with arguments: --n --k --p --seed. We accept the same arguments for
compatibility, but the emitted graph is selected by MANUAL_CASE env var.
"""

from __future__ import annotations

import argparse
import os
import sys


CASES: dict[str, tuple[int, list[str]]] = {
    # Assignment given testcase
    "given_case": (
        6,
        ["010000", "101100", "010010", "010010", "001101", "000010"],
    ),
    # Path graphs
    "P2": (2, ["01", "10"]),
    "P3": (3, ["010", "101", "010"]),
    "P4": (4, ["0100", "1010", "0101", "0010"]),
    "P5": (5, ["01000", "10100", "01010", "00101", "00010"]),
    # Cycle graphs
    "C4": (4, ["0101", "1010", "0101", "1010"]),
    "C5": (5, ["01001", "10100", "01010", "00101", "10010"]),
    "C6": (6, ["010001", "101000", "010100", "001010", "000101", "100010"]),
    # Star graph (center=0, 5 leaves)
    "Star6": (6, ["011111", "100000", "100000", "100000", "100000", "100000"]),
    # Dense/complete graphs
    "K3": (3, ["011", "101", "110"]),
    "K4": (4, ["0111", "1011", "1101", "1110"]),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manual graph emitter")
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--p", type=float, required=True)
    parser.add_argument("--seed", type=int, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    case_name = os.environ.get("MANUAL_CASE", "").strip()
    if not case_name:
        available = ", ".join(sorted(CASES))
        raise SystemExit(f"MANUAL_CASE is required. Available: {available}")
    if case_name not in CASES:
        available = ", ".join(sorted(CASES))
        raise SystemExit(f"Unknown MANUAL_CASE='{case_name}'. Available: {available}")

    n, rows = CASES[case_name]
    if args.n != n:
        raise SystemExit(
            f"checker requested n={args.n} but case {case_name} has n={n}. "
            "Please pass matching --n-values."
        )

    # Output format: "n row1 row2 ... rowN"
    sys.stdout.write(" ".join([str(n), *rows]) + "\n")


if __name__ == "__main__":
    main()
