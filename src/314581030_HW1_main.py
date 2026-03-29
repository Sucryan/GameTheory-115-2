#!/usr/bin/env python3
"""HW1 Graph Game main program skeleton.

This file focuses on architecture, interface, data flow, and I/O format.
The actual game-solving algorithms are intentionally left as TODO blocks.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Any, Optional, Sequence


class Graph:
    """Simple graph container using 0-based node indices internally."""

    def __init__(self, n: int, adjacency_matrix: list[list[int]], adjacency_list: list[list[int]]) -> None:
        self.n = n
        self.adjacency_matrix = adjacency_matrix
        self.adjacency_list = adjacency_list

    def degree(self, i: int) -> int:
        self._validate_node_index(i)
        return len(self.adjacency_list[i])

    def neighbors(self, i: int) -> list[int]:
        self._validate_node_index(i)
        return list(self.adjacency_list[i])

    def is_edge(self, i: int, j: int) -> bool:
        self._validate_node_index(i)
        self._validate_node_index(j)
        return self.adjacency_matrix[i][j] == 1

    def _validate_node_index(self, i: int) -> None:
        if not (0 <= i < self.n):
            raise IndexError(f"node index out of range: {i}, expected 0 <= i < {self.n}")


@dataclass
class SolverResult:
    """Common return type for all game solvers."""

    cardinality: int
    move_count: Optional[int]
    state: Any
    is_valid: bool


def parse_args(argv: Optional[Sequence[str]] = None) -> tuple[int, list[str]]:
    """Parse command-line arguments.

    Expected format:
      python 314581030_HW1_main.py n row1 row2 ... rowN
    where each row is an n-length bit string.
    """
    parser = argparse.ArgumentParser(
        description="Read graph bit-strings and run three graph-game solvers (skeleton)."
    )
    parser.add_argument("n", type=int, help="Number of nodes")
    parser.add_argument(
        "bitstrings",
        nargs="*",
        help="n bit strings, each of length n (characters must be 0/1)",
    )

    args = parser.parse_args(argv)
    validate_input_format(args.n, args.bitstrings)
    return args.n, list(args.bitstrings)


def validate_input_format(n: int, bitstrings: Sequence[str]) -> None:
    """Validate basic input format and raise ValueError for invalid inputs."""
    if n <= 0:
        raise ValueError(f"n must be a positive integer, got: {n}")

    if len(bitstrings) != n:
        raise ValueError(
            f"expected {n} bit strings after n, but got {len(bitstrings)}"
        )

    for idx, row in enumerate(bitstrings):
        if len(row) != n:
            raise ValueError(
                f"row {idx} has length {len(row)}, expected exactly {n}"
            )
        if any(ch not in {"0", "1"} for ch in row):
            raise ValueError(
                f"row {idx} contains non-bit characters; only '0' or '1' are allowed"
            )

    # TODO(student): confirm assignment-specific graph constraints from PDF.
    # Examples that may need additional checks after definition is clarified:
    # - directed vs undirected graph requirement (matrix symmetry)
    # - whether self-loop entries diagonal[i][i] must be 0


def build_graph_from_bitstrings(n: int, bitstrings: Sequence[str]) -> Graph:
    """Build Graph object from validated bit-string rows."""
    adjacency_matrix: list[list[int]] = [[int(ch) for ch in row] for row in bitstrings]
    adjacency_list: list[list[int]] = [
        [j for j, value in enumerate(row) if value == 1] for row in adjacency_matrix
    ]
    return Graph(n=n, adjacency_matrix=adjacency_matrix, adjacency_list=adjacency_list)


def solve_mis_based_ids(graph: Graph) -> SolverResult:
    """Skeleton solver for Requirement 1-1: MIS-based IDS Game.

    TODO(student): implement full game logic based on HW1 formal definition.
    Keep 0-based indices internally; if output explanation needs human-readable
    nodes, map to 1-based labels (node1, node2, ...).
    """
    _ = graph
    return SolverResult(
        cardinality=2,
        move_count=None,
        state={"status": "placeholder", "game": "MIS-based IDS"},
        is_valid=True,
    )


def solve_symmetric_mds_based_ids(graph: Graph) -> SolverResult:
    """Skeleton solver for Requirement 1-2: Symmetric MDS-based IDS Game.

    TODO(student): implement complete solver with mathematically correct
    dominance/game-state transitions according to HW1 definition.
    """
    _ = graph
    return SolverResult(
        cardinality=2,
        move_count=None,
        state={"status": "placeholder", "game": "Symmetric MDS-based IDS"},
        is_valid=True,
    )


def solve_maximal_matching(graph: Graph) -> SolverResult:
    """Skeleton solver for Requirement 2: Matching Game.

    TODO(student): clarify if assignment asks for maximal or maximum matching
    strategy in this game context, then implement corresponding game solver.
    """
    _ = graph
    return SolverResult(
        cardinality=2,
        move_count=None,
        state={"status": "placeholder", "game": "Matching Game"},
        is_valid=True,
    )


def pretty_print_results(ans1: int, ans2: int, ans3: int) -> None:
    """Print outputs in exactly the required homework format."""
    print("Requirement 1-1:")
    print(f"the cardinality of MIS-based IDS Game is {ans1}")
    print()
    print("Requirement 1-2:")
    print(f"the cardinality of Symmetric MDS-based IDS Game is {ans2}")
    print()
    print("Requirement 2:")
    print(f"the cardinality of Matching Game is {ans3}")


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Program entrypoint.

    Data flow:
    1. parse input
    2. build graph
    3. run three game solvers in order
    4. print three cardinalities in required format
    """
    try:
        n, bitstrings = parse_args(argv)
        graph = build_graph_from_bitstrings(n, bitstrings)

        result_1 = solve_mis_based_ids(graph)
        result_2 = solve_symmetric_mds_based_ids(graph)
        result_3 = solve_maximal_matching(graph)

        pretty_print_results(
            result_1.cardinality,
            result_2.cardinality,
            result_3.cardinality,
        )
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
