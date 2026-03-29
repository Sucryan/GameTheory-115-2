#!/usr/bin/env python3
"""HW1 Graph Game main program skeleton.

This file focuses on architecture, interface, data flow, and I/O format.
The actual game-solving algorithms are intentionally left as TODO blocks.
"""

from __future__ import annotations

import argparse
import random
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


def build_degree_filtered_neighbor_sets(graph: Graph) -> list[set[int]]:
    """Build L_i sets from textbook definition.

    Definition mapping:
      L_i = { j | j is a neighbor of i, and deg(j) >= deg(i) }
    """
    degrees = [graph.degree(i) for i in range(graph.n)]
    l_sets: list[set[int]] = []

    for i in range(graph.n):
        l_i = {j for j in graph.neighbors(i) if degrees[j] >= degrees[i]}
        l_sets.append(l_i)

    return l_sets


def utility_for_node(i: int, state: Sequence[int], l_sets: Sequence[set[int]], alpha: float) -> float:
    """Compute u_i(C) exactly as defined in the textbook.

    Definition mapping:
      u_i(C) = c_i * (1 - alpha * sum_{j in L_i} c_j), with alpha > 1
    """
    c_i = state[i]
    neighboring_active_count = sum(state[j] for j in l_sets[i])
    return c_i * (1.0 - alpha * neighboring_active_count)


def best_response(i: int, state: Sequence[int], l_sets: Sequence[set[int]]) -> int:
    """Return BR_i from textbook rule.

    Definition mapping:
      - if exists j in L_i with c_j = 1, BR_i = 0
      - otherwise BR_i = 1
    """
    has_active_in_l_i = any(state[j] == 1 for j in l_sets[i])
    return 0 if has_active_in_l_i else 1


def run_best_response_dynamics(
    graph: Graph,
    initial_state: Sequence[int],
    l_sets: Sequence[set[int]],
    alpha: float,
    rng: random.Random,
    max_steps: int,
) -> tuple[list[int], int, bool]:
    """Run asynchronous best-response dynamics until convergence or step cap.

    Tie-breaking uses randomness by uniformly picking one currently improvable
    node at each step.
    """
    state = list(initial_state)
    move_count = 0

    for _ in range(max_steps):
        # Keep utility evaluation explicit to reflect textbook utility usage.
        _ = [utility_for_node(i, state, l_sets, alpha) for i in range(graph.n)]

        improvable_nodes = [
            i for i in range(graph.n) if state[i] != best_response(i, state, l_sets)
        ]
        if not improvable_nodes:
            return state, move_count, True

        chosen_i = rng.choice(improvable_nodes)
        state[chosen_i] = best_response(chosen_i, state, l_sets)
        move_count += 1

    return state, move_count, False


def cardinality(state: Sequence[int]) -> int:
    """Return the number of active nodes in a bit-vector state."""
    return sum(state)


def is_independent_dominating_set(graph: Graph, state: Sequence[int]) -> bool:
    """Check if active nodes form an Independent Dominating Set (IDS)."""
    # Independent set check: no edge between any two active nodes.
    for i in range(graph.n):
        if state[i] == 0:
            continue
        if any(state[j] == 1 for j in graph.neighbors(i)):
            return False

    # Dominating set check: every inactive node has at least one active neighbor.
    for i in range(graph.n):
        if state[i] == 1:
            continue
        if not any(state[j] == 1 for j in graph.neighbors(i)):
            return False

    return True


def generate_initial_states(n: int, rng: random.Random, random_start_count: int) -> list[list[int]]:
    """Build multiple initial states for multi-start execution."""
    starts: list[list[int]] = []

    # Two deterministic anchors.
    starts.append([0] * n)
    starts.append([1] * n)

    # Random starts for better exploration.
    for _ in range(random_start_count):
        starts.append([rng.randint(0, 1) for _ in range(n)])

    return starts


def solve_mis_based_ids(graph: Graph) -> SolverResult:
    """Solver for Requirement 1-1: MIS-based IDS Game.

    Implemented strictly from textbook definitions:
    1) State is bit vector C=(c_1,...,c_n), c_i in {0,1}
    2) L_i uses degree-filtered neighbors
    3) utility u_i(C)=c_i*(1-alpha*sum_{j in L_i} c_j), alpha>1
    4) best response rule follows existence of active node in L_i

    Multi-start best-response dynamics is used and the minimum cardinality
    among valid converged IDS outcomes is returned.
    """
    alpha = 2.0  # alpha > 1 as required by the definition.
    rng = random.Random()
    l_sets = build_degree_filtered_neighbor_sets(graph)

    random_start_count = max(16, 2 * graph.n)
    max_steps = max(1000, 50 * graph.n * graph.n)
    initial_states = generate_initial_states(graph.n, rng, random_start_count)

    best_valid: Optional[SolverResult] = None
    fallback: Optional[SolverResult] = None

    for start in initial_states:
        final_state, moves, converged = run_best_response_dynamics(
            graph=graph,
            initial_state=start,
            l_sets=l_sets,
            alpha=alpha,
            rng=rng,
            max_steps=max_steps,
        )
        final_cardinality = cardinality(final_state)
        is_valid = converged and is_independent_dominating_set(graph, final_state)

        candidate = SolverResult(
            cardinality=final_cardinality,
            move_count=moves,
            state={
                "bit_vector": final_state,
                "converged": converged,
                "alpha": alpha,
                "starts": len(initial_states),
            },
            is_valid=is_valid,
        )

        if fallback is None or candidate.cardinality < fallback.cardinality:
            fallback = candidate

        if not is_valid:
            continue

        if best_valid is None:
            best_valid = candidate
            continue

        if candidate.cardinality < best_valid.cardinality:
            best_valid = candidate
        elif candidate.cardinality == best_valid.cardinality:
            # Tie-breaking among same-cardinality valid outcomes uses randomness.
            best_valid = rng.choice([best_valid, candidate])

    if best_valid is not None:
        return best_valid

    # Defensive fallback: if no valid converged IDS is found, return the best
    # cardinality state we observed and mark it invalid.
    if fallback is None:
        return SolverResult(
            cardinality=graph.n,
            move_count=None,
            state={"bit_vector": [1] * graph.n, "converged": False, "alpha": alpha, "starts": 0},
            is_valid=False,
        )
    return fallback


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
