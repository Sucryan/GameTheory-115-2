#!/usr/bin/env python3
"""Watts-Strogatz graph generator for HW graph bit-string input format.

This script generates test graphs only.
It can also optionally run the homework main program immediately after
generation for quick smoke tests.
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
from pathlib import Path


def validate_parameters(n: int, k: int, p: float) -> None:
    """Validate WS model parameters.

    Constraints used here follow the assignment statement:
    - n is positive
    - k is even and 0 < k < n
    - p is in [0, 1]
    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if not (0 < k < n):
        raise ValueError(f"k must satisfy 0 < k < n, got k={k}, n={n}")
    if k % 2 != 0:
        raise ValueError(f"k must be even, got {k}")
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"p must be in [0, 1], got {p}")


def build_ring_lattice(n: int, k: int) -> list[set[int]]:
    """Build an n-node regular ring lattice.

    Construction rule:
    each node i connects to k/2 nearest neighbors on its left and right
    on a ring (modulo n). The graph is undirected and simple.
    """
    adjacency: list[set[int]] = [set() for _ in range(n)]
    half_k = k // 2

    for i in range(n):
        for step in range(1, half_k + 1):
            left = (i - step) % n
            right = (i + step) % n
            adjacency[i].add(left)
            adjacency[left].add(i)
            adjacency[i].add(right)
            adjacency[right].add(i)

    return adjacency


def _edge_list(adjacency: list[set[int]]) -> list[tuple[int, int]]:
    """Return undirected edge list as (u, v) with u < v."""
    edges: list[tuple[int, int]] = []
    for u, neighbors in enumerate(adjacency):
        for v in neighbors:
            if u < v:
                edges.append((u, v))
    return edges


def rewire_edges(adjacency: list[set[int]], p: float, rng: random.Random) -> None:
    """Rewire each original ring edge with probability p.

    Rules enforced during rewiring:
    - undirected simple graph
    - no self-loop
    - no duplicate edge

    We iterate over a snapshot of the original ring edges so each original edge
    is considered exactly once.
    """
    n = len(adjacency)
    original_edges = _edge_list(adjacency)

    for u, v in original_edges:
        if rng.random() >= p:
            continue

        adjacency[u].remove(v)
        adjacency[v].remove(u)

        # Candidate new endpoints avoid self-loop and duplicate edges.
        candidates = [w for w in range(n) if w != u and w not in adjacency[u]]

        if not candidates:
            # Conservatively restore if no legal rewiring target exists.
            adjacency[u].add(v)
            adjacency[v].add(u)
            continue

        w = rng.choice(candidates)
        adjacency[u].add(w)
        adjacency[w].add(u)


def ensure_no_isolated_nodes(adjacency: list[set[int]], rng: random.Random) -> None:
    """Ensure every node has degree at least 1.

    Rewiring can occasionally isolate nodes. To satisfy assignment constraints,
    this function adds the minimum number of repair edges: each isolated node
    gets one new connection to a legal target.

    The repair is conservative because it only adds edges and never removes any
    additional existing edges.
    """
    n = len(adjacency)

    isolated = [node for node in range(n) if len(adjacency[node]) == 0]
    for node in isolated:
        candidates = [other for other in range(n) if other != node and other not in adjacency[node]]
        if not candidates:
            raise RuntimeError("cannot repair isolated node in a complete graph scenario")

        target = rng.choice(candidates)
        adjacency[node].add(target)
        adjacency[target].add(node)


def adjacency_matrix_to_bitstrings(adjacency: list[set[int]]) -> list[str]:
    """Convert adjacency list-of-sets to n bit strings (length n each)."""
    n = len(adjacency)
    rows: list[str] = []
    for i in range(n):
        row_bits = ["1" if j in adjacency[i] else "0" for j in range(n)]
        rows.append("".join(row_bits))
    return rows


def generate_ws_graph(n: int, k: int, p: float, seed: int | None = None) -> list[set[int]]:
    """Generate a WS graph as adjacency list-of-sets."""
    validate_parameters(n, k, p)
    rng = random.Random(seed)

    adjacency = build_ring_lattice(n, k)
    rewire_edges(adjacency, p, rng)
    ensure_no_isolated_nodes(adjacency, rng)

    return adjacency


def _format_hw_input_line(n: int, bitstrings: list[str]) -> str:
    """Build single-line HW input style: n row1 row2 ... rowN."""
    return " ".join([str(n)] + bitstrings)


def main() -> None:
    """CLI entrypoint.

    Mode A (default): generate and print graph in HW bit-string format.
    Mode B (--run-main): generate graph and immediately invoke HW solver.
    """
    parser = argparse.ArgumentParser(description="Generate Watts-Strogatz graph test data for HW input format.")
    parser.add_argument("--n", type=int, required=True, help="Number of nodes")
    parser.add_argument("--k", type=int, required=True, help="Each node connects to k nearest neighbors on ring")
    parser.add_argument("--p", type=float, required=True, help="Rewiring probability in [0, 1]")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible generation")
    parser.add_argument(
        "--run-main",
        action="store_true",
        help="After generation, run 314581030_HW1_main.py with generated graph",
    )
    parser.add_argument(
        "--main-script",
        default="314581030_HW1_main.py",
        help="Main solver script filename under the same src folder",
    )

    args = parser.parse_args()

    adjacency = generate_ws_graph(args.n, args.k, args.p, seed=args.seed)
    bitstrings = adjacency_matrix_to_bitstrings(adjacency)
    hw_input = _format_hw_input_line(args.n, bitstrings)

    if not args.run_main:
        print(hw_input)
        return

    script_path = Path(__file__).resolve().parent / args.main_script
    command = [sys.executable, str(script_path), str(args.n), *bitstrings]

    # Show generated graph first so experiment logs always include the test case.
    print(hw_input)
    print()

    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")

    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
