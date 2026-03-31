#!/usr/bin/env python3
"""Standalone checker and benchmark tool for HW1 graph-game solvers.

This script intentionally does NOT modify the stdout format or internal logic
of `314581030_HW1_main.py`. It imports solver functions directly and performs
exact validation on returned final states.
"""

from __future__ import annotations

import argparse
import importlib.util
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import matplotlib.pyplot as plt


EPSILON = 1e-9


@dataclass
class BenchmarkPoint:
    """Aggregated benchmark metrics at one x-axis point (n or p)."""

    x_value: float
    avg_cardinality_problem1: float
    avg_cardinality_problem2: float
    avg_cardinality_problem3: float
    avg_move_count_problem1: float
    avg_move_count_problem2: float
    avg_move_count_problem3: float
    valid_rate_problem1: float
    valid_rate_problem2: float
    valid_rate_problem3: float
    maximal_rate_problem3: float
    ne_rate_problem1: float
    ne_rate_problem2: float
    ne_rate_problem3: float
    avg_unmatched_p3: float
    avg_unmatched_neighbor_p3: float


@dataclass
class TrialMetrics:
    """Per-trial metrics before averaging."""

    cardinality_problem1: float
    cardinality_problem2: float
    cardinality_problem3: float
    move_count_problem1: float
    move_count_problem2: float
    move_count_problem3: float
    valid_problem1: bool
    valid_problem2: bool
    valid_problem3: bool
    maximal_problem3: bool
    ne_problem1: bool
    ne_problem2: bool
    ne_problem3: bool
    unmatched_count_p3: float
    unmatched_neighbor_count_p3: float


def load_main_module(main_path: Path) -> Any:
    """Load `314581030_HW1_main.py` as a module from its file path."""
    module_name = "hw1_main_module"
    spec = importlib.util.spec_from_file_location(module_name, str(main_path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module spec from: {main_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def parse_ws_output(raw_output: str) -> tuple[int, list[str]]:
    """Parse `ws_generator.py` output into (n, bitstrings).

    Expected canonical form is one line:
      n row1 row2 ... rowN
    but this parser is slightly tolerant to extra whitespace/noise.
    """
    tokens = raw_output.split()
    if not tokens:
        raise ValueError("ws_generator output is empty")

    for idx, token in enumerate(tokens):
        if not token.isdigit():
            continue

        n = int(token)
        if n <= 0:
            continue

        rows = tokens[idx + 1 : idx + 1 + n]
        if len(rows) != n:
            continue

        if all(len(row) == n and set(row).issubset({"0", "1"}) for row in rows):
            return n, rows

    raise ValueError(
        "Unable to parse ws_generator output into 'n + n bitstrings'. "
        f"Raw output:\n{raw_output}"
    )


def generate_ws_graph_via_subprocess(
    ws_generator_path: Path,
    n: int,
    k: int,
    p: float,
    seed: int,
) -> tuple[int, list[str]]:
    """Call ws_generator.py via subprocess and return (n, bitstrings)."""
    command = [
        sys.executable,
        str(ws_generator_path),
        "--n",
        str(n),
        "--k",
        str(k),
        "--p",
        str(p),
        "--seed",
        str(seed),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "ws_generator subprocess failed\n"
            f"command: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )

    return parse_ws_output(completed.stdout)


def _as_bit_vector(state: Any, expected_n: int) -> list[int]:
    """Extract bit-vector state from solver result state payload."""
    if isinstance(state, dict) and "bit_vector" in state:
        bit_vector = state["bit_vector"]
    elif isinstance(state, list):
        bit_vector = state
    else:
        raise ValueError(f"Cannot extract bit_vector from state: {state!r}")

    if len(bit_vector) != expected_n:
        raise ValueError(f"bit_vector length mismatch: got {len(bit_vector)}, expected {expected_n}")

    normalized: list[int] = []
    for value in bit_vector:
        if value in (0, 1):
            normalized.append(int(value))
        else:
            raise ValueError(f"bit_vector contains non-binary value: {value!r}")
    return normalized


def _as_strategy_state(state: Any, expected_n: int) -> list[Optional[int]]:
    """Extract strategy profile (None or neighbor index) from solver payload."""
    if isinstance(state, dict) and "strategy_state" in state:
        strategy_state = state["strategy_state"]
    elif isinstance(state, list):
        strategy_state = state
    else:
        raise ValueError(f"Cannot extract strategy_state from state: {state!r}")

    if len(strategy_state) != expected_n:
        raise ValueError(f"strategy_state length mismatch: got {len(strategy_state)}, expected {expected_n}")

    normalized: list[Optional[int]] = []
    for value in strategy_state:
        if value is None:
            normalized.append(None)
        elif isinstance(value, int):
            normalized.append(value)
        else:
            raise ValueError(f"strategy_state contains invalid value type: {value!r}")
    return normalized


def is_independent(graph: Any, state: list[int]) -> bool:
    """Return whether active nodes form an independent set."""
    if len(state) != graph.n:
        return False

    active_nodes = [i for i, value in enumerate(state) if value == 1]
    for i in active_nodes:
        for j in graph.neighbors(i):
            if state[j] == 1:
                return False
    return True


def is_dominating(graph: Any, state: list[int]) -> bool:
    """Return whether active nodes dominate all nodes."""
    if len(state) != graph.n:
        return False

    for i in range(graph.n):
        if state[i] == 1:
            continue
        if not any(state[j] == 1 for j in graph.neighbors(i)):
            return False
    return True


def is_independent_dominating_set(graph: Any, state: list[int]) -> bool:
    """Return whether state is a valid IDS."""
    return is_independent(graph, state) and is_dominating(graph, state)


def _argmax_actions(action_values: dict[int, float]) -> set[int]:
    """Return argmax set for binary actions with tolerance."""
    best_value = max(action_values.values())
    return {action for action, value in action_values.items() if math.isclose(value, best_value, abs_tol=EPSILON)}


def _problem1_l_sets(graph: Any) -> list[set[int]]:
    """Construct L_i = {j in N_i | deg(j) >= deg(i)}."""
    degrees = [graph.degree(i) for i in range(graph.n)]
    return [{j for j in graph.neighbors(i) if degrees[j] >= degrees[i]} for i in range(graph.n)]


def _utility_problem1_for_action(state: list[int], l_sets: list[set[int]], i: int, action: int, alpha: float) -> float:
    trial_state = list(state)
    trial_state[i] = action
    c_i = trial_state[i]
    neighboring_active_count = sum(trial_state[j] for j in l_sets[i])
    return c_i * (1.0 - alpha * neighboring_active_count)


def is_ne_problem1(graph: Any, state: list[int], alpha: float = 2.0) -> bool:
    """Exact NE check for Problem 1 using argmax best-response sets."""
    l_sets = _problem1_l_sets(graph)

    for i in range(graph.n):
        current_action = state[i]
        action_values = {
            0: _utility_problem1_for_action(state, l_sets, i, 0, alpha),
            1: _utility_problem1_for_action(state, l_sets, i, 1, alpha),
        }
        best_actions = _argmax_actions(action_values)
        if current_action not in best_actions:
            return False
    return True


def _build_closed_neighborhoods(graph: Any) -> list[set[int]]:
    """Construct M_i = N_i U {i}."""
    closed_neighbors: list[set[int]] = []
    for i in range(graph.n):
        m_i = set(graph.neighbors(i))
        m_i.add(i)
        closed_neighbors.append(m_i)
    return closed_neighbors


def _utility_problem2_for_action(
    graph: Any,
    state: list[int],
    closed_neighbors: list[set[int]],
    i: int,
    action: int,
    alpha: float,
    beta: float,
    gamma: float,
) -> float:
    trial_state = list(state)
    trial_state[i] = action
    if trial_state[i] == 0:
        return 0.0

    def domination_count(node: int) -> int:
        return sum(trial_state[j] for j in closed_neighbors[node])

    def domination_gain(node: int) -> float:
        return alpha if domination_count(node) == 1 else 0.0

    gain_sum = sum(domination_gain(j) for j in closed_neighbors[i])
    penalty = sum(trial_state[i] * trial_state[j] * gamma for j in graph.neighbors(i))
    return gain_sum - beta - penalty


def is_ne_problem2(
    graph: Any,
    state: list[int],
    alpha: float = 2.0,
    beta: float = 1.0,
    gamma: Optional[float] = None,
) -> bool:
    """Exact NE check for Problem 2 using argmax best-response sets."""
    gamma_value = (graph.n * alpha + 1.0) if gamma is None else gamma
    closed_neighbors = _build_closed_neighborhoods(graph)

    for i in range(graph.n):
        current_action = state[i]
        action_values = {
            0: _utility_problem2_for_action(graph, state, closed_neighbors, i, 0, alpha, beta, gamma_value),
            1: _utility_problem2_for_action(graph, state, closed_neighbors, i, 1, alpha, beta, gamma_value),
        }
        best_actions = _argmax_actions(action_values)
        if current_action not in best_actions:
            return False
    return True


def is_strategy_profile_well_formed(graph: Any, state: list[Optional[int]]) -> bool:
    """Check strategy profile is valid: each action is None or a legal neighbor."""
    if len(state) != graph.n:
        return False

    for i, choice in enumerate(state):
        if choice is None:
            continue
        if not isinstance(choice, int):
            return False
        if not (0 <= choice < graph.n):
            return False
        if choice == i:
            return False
        if choice not in graph.neighbors(i):
            return False
    return True


def compute_matching_edges(state: list[Optional[int]]) -> set[tuple[int, int]]:
    """Build matching edges from mutual choices only.

    Edge tuples are normalized to (min(i, j), max(i, j)).
    """
    edges: set[tuple[int, int]] = set()
    n = len(state)
    for i in range(n):
        j = state[i]
        if j is None:
            continue
        if not (0 <= j < n):
            continue
        if state[j] == i:
            edges.add((min(i, j), max(i, j)))
    return edges


def is_valid_matching(graph: Any, state: list[Optional[int]]) -> bool:
    """Check matching validity: legal edges and no shared endpoints."""
    if not is_strategy_profile_well_formed(graph, state):
        return False

    edges = compute_matching_edges(state)
    used_vertices: set[int] = set()
    for u, v in edges:
        if not graph.is_edge(u, v):
            return False
        if u in used_vertices or v in used_vertices:
            return False
        used_vertices.add(u)
        used_vertices.add(v)
    return True


def is_maximal_matching(graph: Any, state: list[Optional[int]]) -> bool:
    """Check maximality of the matching induced by strategy state."""
    if not is_valid_matching(graph, state):
        return False

    edges = compute_matching_edges(state)
    matched_vertices: set[int] = set()
    for u, v in edges:
        matched_vertices.add(u)
        matched_vertices.add(v)

    for u in range(graph.n):
        for v in range(u + 1, graph.n):
            if not graph.is_edge(u, v):
                continue
            if u in matched_vertices or v in matched_vertices:
                continue
            return False
    return True


def compute_unmatched_metrics(graph: Any, state: list[Optional[int]]) -> tuple[int, int]:
    """Return (unmatched_count, unmatched_with_unmatched_neighbor_count).

    unmatched_count: number of vertices not covered by any matching edge.
    unmatched_with_unmatched_neighbor_count: among unmatched vertices, how many
        have at least one neighbor that is also unmatched.  A non-zero value
        indicates the matching is *not* maximal (an augmenting edge still exists).
    """
    edges = compute_matching_edges(state)
    matched: set[int] = set()
    for u, v in edges:
        matched.add(u)
        matched.add(v)

    unmatched = [i for i in range(graph.n) if i not in matched]
    unmatched_set = set(unmatched)
    unmatched_with_unmatched_neighbor = sum(
        1 for u in unmatched if any(v in unmatched_set for v in graph.neighbors(u))
    )
    return len(unmatched), unmatched_with_unmatched_neighbor


def _utility_problem3_for_strategy(
    graph: Any,
    state: list[Optional[int]],
    i: int,
    strategy: Optional[int],
) -> float:
    """Utility for player i if they unilaterally play *strategy*, others unchanged.

    Mirrors the utility_problem3 definition from the main solver:
      - None  -> 0
      - j (mutual)   -> 3 + bias(j)
      - j (j -> None) -> 1 + bias(j)
      - j (j -> other) -> -1 + bias(j)
    where bias(j) = 1 / (1 + deg(j)).

    Because this is a unilateral deviation, state[j] (the neighbor's choice) is
    always taken from the *original* state, not a modified copy.
    """
    if strategy is None:
        return 0.0
    if not isinstance(strategy, int):
        return -1.0
    if not (0 <= strategy < graph.n):
        return -1.0
    if not graph.is_edge(i, strategy):
        return -1.0

    neighbor = strategy
    bias = 1.0 / (1.0 + graph.degree(neighbor))
    neighbor_strategy = state[neighbor]

    if neighbor_strategy == i:
        return 3.0 + bias
    if neighbor_strategy is None:
        return 1.0 + bias
    return -1.0 + bias


def is_ne_problem3(graph: Any, state: list[Optional[int]]) -> bool:
    """Exact NE check for Problem 3.

    A strategy profile is a Nash Equilibrium iff no player can strictly improve
    their utility by unilaterally deviating.  For each player i we enumerate
    every candidate strategy (None, or any graph-neighbour of i) and verify that
    the current choice achieves at least as high utility as every alternative.
    """
    for i in range(graph.n):
        current_utility = _utility_problem3_for_strategy(graph, state, i, state[i])
        for strategy in [None, *graph.neighbors(i)]:
            alt_utility = _utility_problem3_for_strategy(graph, state, i, strategy)
            if alt_utility > current_utility + EPSILON:
                return False
    return True


def _move_count_as_float(move_count: Optional[int]) -> float:
    """Normalize move_count to float for averaging."""
    return float(move_count) if move_count is not None else 0.0


def run_single_trial(
    module: Any,
    ws_generator_path: Path,
    n: int,
    k: int,
    p: float,
    seed: int,
) -> TrialMetrics:
    """Generate one graph, run all three solvers, and compute exact metrics."""
    parsed_n, bitstrings = generate_ws_graph_via_subprocess(ws_generator_path, n=n, k=k, p=p, seed=seed)
    graph = module.build_graph_from_bitstrings(parsed_n, bitstrings)

    result1 = module.solve_mis_based_ids(graph)
    result2 = module.solve_symmetric_mds_based_ids(graph)
    result3 = module.solve_maximal_matching(graph)

    state1 = _as_bit_vector(result1.state, graph.n)
    state2 = _as_bit_vector(result2.state, graph.n)
    state3 = _as_strategy_state(result3.state, graph.n)

    valid1 = is_independent_dominating_set(graph, state1)
    valid2 = is_independent_dominating_set(graph, state2)
    valid3 = is_valid_matching(graph, state3)
    maximal3 = is_maximal_matching(graph, state3)

    ne1 = is_ne_problem1(graph, state1)
    ne2 = is_ne_problem2(graph, state2)
    ne3 = is_ne_problem3(graph, state3)

    card3 = float(len(compute_matching_edges(state3)))
    unmatched_count, unmatched_nb_count = compute_unmatched_metrics(graph, state3)

    return TrialMetrics(
        cardinality_problem1=float(sum(state1)),
        cardinality_problem2=float(sum(state2)),
        cardinality_problem3=card3,
        move_count_problem1=_move_count_as_float(result1.move_count),
        move_count_problem2=_move_count_as_float(result2.move_count),
        move_count_problem3=_move_count_as_float(result3.move_count),
        valid_problem1=valid1,
        valid_problem2=valid2,
        valid_problem3=valid3,
        maximal_problem3=maximal3,
        ne_problem1=ne1,
        ne_problem2=ne2,
        ne_problem3=ne3,
        unmatched_count_p3=float(unmatched_count),
        unmatched_neighbor_count_p3=float(unmatched_nb_count),
    )


def _aggregate_trials(x_value: float, trials: list[TrialMetrics]) -> BenchmarkPoint:
    """Aggregate multiple trial metrics into one benchmark point."""
    trial_count = len(trials)
    if trial_count == 0:
        raise ValueError("Cannot aggregate empty trial list")

    return BenchmarkPoint(
        x_value=x_value,
        avg_cardinality_problem1=sum(t.cardinality_problem1 for t in trials) / trial_count,
        avg_cardinality_problem2=sum(t.cardinality_problem2 for t in trials) / trial_count,
        avg_cardinality_problem3=sum(t.cardinality_problem3 for t in trials) / trial_count,
        avg_move_count_problem1=sum(t.move_count_problem1 for t in trials) / trial_count,
        avg_move_count_problem2=sum(t.move_count_problem2 for t in trials) / trial_count,
        avg_move_count_problem3=sum(t.move_count_problem3 for t in trials) / trial_count,
        valid_rate_problem1=sum(1 for t in trials if t.valid_problem1) / trial_count,
        valid_rate_problem2=sum(1 for t in trials if t.valid_problem2) / trial_count,
        valid_rate_problem3=sum(1 for t in trials if t.valid_problem3) / trial_count,
        maximal_rate_problem3=sum(1 for t in trials if t.maximal_problem3) / trial_count,
        ne_rate_problem1=sum(1 for t in trials if t.ne_problem1) / trial_count,
        ne_rate_problem2=sum(1 for t in trials if t.ne_problem2) / trial_count,
        ne_rate_problem3=sum(1 for t in trials if t.ne_problem3) / trial_count,
        avg_unmatched_p3=sum(t.unmatched_count_p3 for t in trials) / trial_count,
        avg_unmatched_neighbor_p3=sum(t.unmatched_neighbor_count_p3 for t in trials) / trial_count,
    )


def benchmark_over_n(
    module: Any,
    ws_generator_path: Path,
    n_values: list[int],
    k: int,
    p: float,
    trials_per_n: int,
    seed_base: int,
) -> list[BenchmarkPoint]:
    """Benchmark with fixed k, p and varying n."""
    results: list[BenchmarkPoint] = []

    for idx, n in enumerate(n_values):
        trial_metrics: list[TrialMetrics] = []
        for t in range(trials_per_n):
            seed = seed_base + idx * 10_000 + t
            metrics = run_single_trial(module, ws_generator_path, n=n, k=k, p=p, seed=seed)
            trial_metrics.append(metrics)

        results.append(_aggregate_trials(float(n), trial_metrics))

    return results


def benchmark_over_p(
    module: Any,
    ws_generator_path: Path,
    n: int,
    k: int,
    p_values: list[float],
    trials_per_p: int,
    seed_base: int,
) -> list[BenchmarkPoint]:
    """Benchmark with fixed n, k and varying p."""
    results: list[BenchmarkPoint] = []

    for idx, p in enumerate(p_values):
        trial_metrics: list[TrialMetrics] = []
        for t in range(trials_per_p):
            seed = seed_base + idx * 10_000 + t
            metrics = run_single_trial(module, ws_generator_path, n=n, k=k, p=p, seed=seed)
            trial_metrics.append(metrics)

        results.append(_aggregate_trials(float(p), trial_metrics))

    return results


def plot_avg_cardinality_vs_n(results: list[BenchmarkPoint], output_path: Path) -> None:
    """Plot average cardinality of all three problems against n."""
    x_values = [int(point.x_value) for point in results]

    plt.figure()
    plt.plot(x_values, [point.avg_cardinality_problem1 for point in results], marker="o", label="Problem 1-1")
    plt.plot(x_values, [point.avg_cardinality_problem2 for point in results], marker="o", label="Problem 1-2")
    plt.plot(x_values, [point.avg_cardinality_problem3 for point in results], marker="o", label="Problem 2")
    plt.title("Average Cardinality vs n")
    plt.xlabel("n")
    plt.ylabel("Average Cardinality")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_avg_move_count_vs_n(results: list[BenchmarkPoint], output_path: Path) -> None:
    """Plot average move count of all three problems against n."""
    x_values = [int(point.x_value) for point in results]

    plt.figure()
    plt.plot(x_values, [point.avg_move_count_problem1 for point in results], marker="o", label="Problem 1-1")
    plt.plot(x_values, [point.avg_move_count_problem2 for point in results], marker="o", label="Problem 1-2")
    plt.plot(x_values, [point.avg_move_count_problem3 for point in results], marker="o", label="Problem 2")
    plt.title("Average Move Count vs n")
    plt.xlabel("n")
    plt.ylabel("Average Move Count")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_avg_cardinality_vs_p(results: list[BenchmarkPoint], output_path: Path) -> None:
    """Plot average cardinality of all three problems against p."""
    x_values = [point.x_value for point in results]

    plt.figure()
    plt.plot(x_values, [point.avg_cardinality_problem1 for point in results], marker="o", label="Problem 1-1")
    plt.plot(x_values, [point.avg_cardinality_problem2 for point in results], marker="o", label="Problem 1-2")
    plt.plot(x_values, [point.avg_cardinality_problem3 for point in results], marker="o", label="Problem 2")
    plt.title("Average Cardinality vs p")
    plt.xlabel("p")
    plt.ylabel("Average Cardinality")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def print_results_table(results: list[BenchmarkPoint], x_label: str) -> None:
    """Print a compact text table for quick inspection.

    Columns:
      avg_card_p{1,2,3}  - average cardinality of the returned set/matching
      avg_move_p{1,2,3}  - average number of player moves until convergence
      valid_p{1,2}       - fraction of trials where the IDS property holds
      valid_p3 / max_p3  - fraction of valid / maximal matchings
      ne_p{1,2,3}        - fraction of trials where the result is a Nash Equilibrium
      unmatched_p3       - average number of unmatched vertices (Problem 3)
      unmatch_nb_p3      - average number of unmatched vertices with an unmatched neighbor
    """
    width = 185
    print("=" * width)
    print(
        f"{x_label:>8} | {'avg_card_p1':>11} {'avg_card_p2':>11} {'avg_card_p3':>11} "
        f"| {'avg_move_p1':>11} {'avg_move_p2':>11} {'avg_move_p3':>11} "
        f"| {'valid_p1':>8} {'valid_p2':>8} {'valid_p3':>8} {'max_p3':>8} "
        f"| {'ne_p1':>8} {'ne_p2':>8} {'ne_p3':>8} "
        f"| {'unmatched':>10} {'unmatch_nb':>10}"
    )
    print("-" * width)

    for point in results:
        print(
            f"{point.x_value:8.3f} | "
            f"{point.avg_cardinality_problem1:11.3f} {point.avg_cardinality_problem2:11.3f} {point.avg_cardinality_problem3:11.3f} "
            f"| {point.avg_move_count_problem1:11.3f} {point.avg_move_count_problem2:11.3f} {point.avg_move_count_problem3:11.3f} "
            f"| {point.valid_rate_problem1:8.3f} {point.valid_rate_problem2:8.3f} {point.valid_rate_problem3:8.3f} {point.maximal_rate_problem3:8.3f} "
            f"| {point.ne_rate_problem1:8.3f} {point.ne_rate_problem2:8.3f} {point.ne_rate_problem3:8.3f} "
            f"| {point.avg_unmatched_p3:10.3f} {point.avg_unmatched_neighbor_p3:10.3f}"
        )

    print("=" * width)


def plot_maximal_rate_vs_n(results: list[BenchmarkPoint], output_path: Path) -> None:
    """Plot maximal_rate_problem3 against n."""
    x_values = [int(point.x_value) for point in results]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x_values, [point.maximal_rate_problem3 for point in results], marker="o", color="tab:orange", label="Maximal Rate (P3)")
    ax.set_title("Maximal Rate of Problem 3 vs n")
    ax.set_xlabel("n")
    ax.set_ylabel("Maximal Rate")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_maximal_rate_vs_p(results: list[BenchmarkPoint], output_path: Path) -> None:
    """Plot maximal_rate_problem3 against p."""
    x_values = [point.x_value for point in results]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x_values, [point.maximal_rate_problem3 for point in results], marker="o", color="tab:orange", label="Maximal Rate (P3)")
    ax.set_title("Maximal Rate of Problem 3 vs p")
    ax.set_xlabel("p (rewiring probability)")
    ax.set_ylabel("Maximal Rate")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_unmatched_metrics_vs_n(results: list[BenchmarkPoint], output_path: Path) -> None:
    """Plot avg unmatched and unmatched-with-unmatched-neighbor counts against n."""
    x_values = [int(point.x_value) for point in results]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x_values, [point.avg_unmatched_p3 for point in results], marker="o", color="tab:blue", label="Avg Unmatched Vertices")
    ax.plot(x_values, [point.avg_unmatched_neighbor_p3 for point in results], marker="s", color="tab:red", label="Avg Unmatched w/ Unmatched Neighbor")
    ax.set_title("Unmatched Vertices (Problem 3) vs n")
    ax.set_xlabel("n")
    ax.set_ylabel("Average Count")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_unmatched_metrics_vs_p(results: list[BenchmarkPoint], output_path: Path) -> None:
    """Plot avg unmatched and unmatched-with-unmatched-neighbor counts against p."""
    x_values = [point.x_value for point in results]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x_values, [point.avg_unmatched_p3 for point in results], marker="o", color="tab:blue", label="Avg Unmatched Vertices")
    ax.plot(x_values, [point.avg_unmatched_neighbor_p3 for point in results], marker="s", color="tab:red", label="Avg Unmatched w/ Unmatched Neighbor")
    ax.set_title("Unmatched Vertices (Problem 3) vs p")
    ax.set_xlabel("p (rewiring probability)")
    ax.set_ylabel("Average Count")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    """Parse checker CLI arguments."""
    parser = argparse.ArgumentParser(description="Exact checker + benchmark tool for HW1 graph-game solvers")
    parser.add_argument("--mode", choices=["n", "p"], required=True, help="Benchmark mode: vary n or vary p")
    parser.add_argument("--n-values", type=int, nargs="+", default=None, help="n list for mode=n")
    parser.add_argument("--p-values", type=float, nargs="+", default=None, help="p list for mode=p")
    parser.add_argument("--n", type=int, default=None, help="fixed n for mode=p")
    parser.add_argument("--k", type=int, required=True, help="WS graph parameter k")
    parser.add_argument("--p", type=float, default=None, help="fixed p for mode=n")
    parser.add_argument("--trials", type=int, default=5, help="number of trials per x-value")
    parser.add_argument("--seed-base", type=int, default=42, help="base random seed for batch runs")
    parser.add_argument(
        "--main-script",
        type=str,
        default="314581030_HW1_main.py",
        help="main solver script filename in the same folder",
    )
    parser.add_argument(
        "--ws-generator",
        type=str,
        default="ws_generator.py",
        help="WS generator script filename in the same folder",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="checker_outputs",
        help="directory for output plots",
    )
    args = parser.parse_args()

    if args.trials <= 0:
        parser.error("--trials must be positive")

    if args.mode == "n":
        if not args.n_values:
            parser.error("mode=n requires --n-values")
        if args.p is None:
            parser.error("mode=n requires --p")
    else:
        if args.n is None:
            parser.error("mode=p requires --n")
        if not args.p_values:
            parser.error("mode=p requires --p-values")

    return args


def main() -> None:
    """CLI entry point."""
    args = parse_args()

    base_dir = Path(__file__).resolve().parent
    main_path = base_dir / args.main_script
    ws_generator_path = base_dir / args.ws_generator
    output_dir = base_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    module = load_main_module(main_path)

    if args.mode == "n":
        n_values = sorted(args.n_values)
        results = benchmark_over_n(
            module=module,
            ws_generator_path=ws_generator_path,
            n_values=n_values,
            k=args.k,
            p=args.p,
            trials_per_n=args.trials,
            seed_base=args.seed_base,
        )
        print_results_table(results, x_label="n")

        plot_avg_cardinality_vs_n(results, output_dir / "avg_cardinality_vs_n.png")
        plot_avg_move_count_vs_n(results, output_dir / "avg_move_count_vs_n.png")
        plot_maximal_rate_vs_n(results, output_dir / "maximal_rate_vs_n.png")
        plot_unmatched_metrics_vs_n(results, output_dir / "unmatched_metrics_vs_n.png")

        print(f"Saved plot: {output_dir / 'avg_cardinality_vs_n.png'}")
        print(f"Saved plot: {output_dir / 'avg_move_count_vs_n.png'}")
        print(f"Saved plot: {output_dir / 'maximal_rate_vs_n.png'}")
        print(f"Saved plot: {output_dir / 'unmatched_metrics_vs_n.png'}")

    else:
        p_values = sorted(args.p_values)
        results = benchmark_over_p(
            module=module,
            ws_generator_path=ws_generator_path,
            n=args.n,
            k=args.k,
            p_values=p_values,
            trials_per_p=args.trials,
            seed_base=args.seed_base,
        )
        print_results_table(results, x_label="p")

        plot_avg_cardinality_vs_p(results, output_dir / "avg_cardinality_vs_p.png")
        plot_maximal_rate_vs_p(results, output_dir / "maximal_rate_vs_p.png")
        plot_unmatched_metrics_vs_p(results, output_dir / "unmatched_metrics_vs_p.png")

        print(f"Saved plot: {output_dir / 'avg_cardinality_vs_p.png'}")
        print(f"Saved plot: {output_dir / 'maximal_rate_vs_p.png'}")
        print(f"Saved plot: {output_dir / 'unmatched_metrics_vs_p.png'}")


if __name__ == "__main__":
    main()
