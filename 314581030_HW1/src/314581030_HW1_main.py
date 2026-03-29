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
        # utility_for_node() is available for inspection/debugging purposes;
        # the best_response() rule derives BR directly without requiring explicit
        # utility values, so no per-step utility sweep is needed here.

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
    """Solver for Requirement 1-2: Symmetric MDS-based IDS Game.

    This implementation follows the textbook definitions directly:
    - M_i = N_i U {i}
    - v_i(C) = sum(c_j for j in M_i)
    - g_i(C) = alpha if v_i(C) == 1 else 0
    - w_i(C) = sum(c_i * c_j * gamma for j in N_i)
    - u_i(C):
        if c_i == 1:
            sum(g_j(C) for j in M_i) - beta - w_i(C)
        else:
            0

    Best response is computed by explicitly comparing utility under c_i=0 and
    c_i=1, with random tie-breaking.
    """
    alpha = 2.0
    beta = 1.0
    gamma = graph.n * alpha + 1.0
    num_restarts = max(16, 2 * graph.n)
    max_steps = max(1000, 50 * graph.n * graph.n)
    seed: Optional[int] = None

    # Keep constraints explicit to avoid silently violating textbook setup.
    if alpha <= 1.0:
        raise ValueError(f"alpha must satisfy alpha > 1, got {alpha}")
    if not (0.0 < beta < alpha):
        raise ValueError(f"beta must satisfy 0 < beta < alpha, got beta={beta}, alpha={alpha}")
    if gamma <= graph.n * alpha:
        raise ValueError(
            f"gamma must satisfy gamma > n * alpha, got gamma={gamma}, n={graph.n}, alpha={alpha}"
        )

    rng = random.Random(seed)
    closed_neighbors = build_closed_neighborhoods(graph)
    initial_states = generate_initial_states(graph.n, rng, num_restarts)

    best_valid: Optional[SolverResult] = None
    fallback: Optional[SolverResult] = None

    for start in initial_states:
        final_state, moves, final_cardinality, converged = run_problem2_dynamics(
            graph=graph,
            initial_state=start,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            closed_neighbors=closed_neighbors,
            rng=rng,
            max_steps=max_steps,
        )

        is_valid = converged and is_independent_dominating_set(graph, final_state)
        candidate = SolverResult(
            cardinality=final_cardinality,
            move_count=moves,
            state={
                "bit_vector": final_state,
                "converged": converged,
                "alpha": alpha,
                "beta": beta,
                "gamma": gamma,
                "starts": len(initial_states),
            },
            is_valid=is_valid,
        )

        if fallback is None or candidate.cardinality < fallback.cardinality:
            fallback = candidate

        if not is_valid:
            # Keep invalid outcomes for debugging/report analysis.
            continue

        if best_valid is None:
            best_valid = candidate
            continue

        if candidate.cardinality < best_valid.cardinality:
            best_valid = candidate
        elif candidate.cardinality == best_valid.cardinality:
            best_valid = rng.choice([best_valid, candidate])

    if best_valid is not None:
        return best_valid

    # Defensive fallback if no converged valid IDS is found.
    if fallback is None:
        return SolverResult(
            cardinality=graph.n,
            move_count=None,
            state={
                "bit_vector": [1] * graph.n,
                "converged": False,
                "alpha": alpha,
                "beta": beta,
                "gamma": gamma,
                "starts": 0,
            },
            is_valid=False,
        )
    return fallback


def build_closed_neighborhoods(graph: Graph) -> list[set[int]]:
    """Build M_i for each node i, where M_i = N_i U {i}."""
    closed_neighbors: list[set[int]] = []
    for i in range(graph.n):
        m_i = set(graph.neighbors(i))
        m_i.add(i)
        closed_neighbors.append(m_i)
    return closed_neighbors


def domination_count(state: Sequence[int], closed_neighbors: Sequence[set[int]], i: int) -> int:
    """Compute v_i(C) = sum(c_j for j in M_i)."""
    return sum(state[j] for j in closed_neighbors[i])


def domination_gain(state: Sequence[int], closed_neighbors: Sequence[set[int]], i: int, alpha: float) -> float:
    """Compute g_i(C) from textbook definition.

    g_i(C) = alpha if v_i(C) == 1 else 0
    """
    return alpha if domination_count(state, closed_neighbors, i) == 1 else 0.0


def independence_penalty(graph: Graph, state: Sequence[int], i: int, gamma: float) -> float:
    """Compute w_i(C) = sum(c_i * c_j * gamma for j in N_i)."""
    c_i = state[i]
    return sum(c_i * state[j] * gamma for j in graph.neighbors(i))


def utility_problem2(
    graph: Graph,
    state: Sequence[int],
    i: int,
    alpha: float,
    beta: float,
    gamma: float,
    closed_neighbors: Sequence[set[int]],
) -> float:
    """Compute u_i(C) exactly for Problem 2.

    If c_i == 1:
      u_i(C) = sum(g_j(C) for j in M_i) - beta - w_i(C)
    If c_i == 0:
      u_i(C) = 0
    """
    if state[i] == 0:
        return 0.0

    gain_sum = sum(domination_gain(state, closed_neighbors, j, alpha) for j in closed_neighbors[i])
    penalty = independence_penalty(graph, state, i, gamma)
    return gain_sum - beta - penalty


def best_response_problem2(
    graph: Graph,
    state: Sequence[int],
    i: int,
    alpha: float,
    beta: float,
    gamma: float,
    closed_neighbors: Sequence[set[int]],
    rng: random.Random,
) -> int:
    """Compute best response by direct utility comparison under c_i in {0,1}."""
    trial_zero = list(state)
    trial_one = list(state)
    trial_zero[i] = 0
    trial_one[i] = 1

    utility_zero = utility_problem2(graph, trial_zero, i, alpha, beta, gamma, closed_neighbors)
    utility_one = utility_problem2(graph, trial_one, i, alpha, beta, gamma, closed_neighbors)

    if utility_one > utility_zero:
        return 1
    if utility_zero > utility_one:
        return 0
    return rng.choice([0, 1])


def run_problem2_dynamics(
    graph: Graph,
    initial_state: Sequence[int],
    alpha: float,
    beta: float,
    gamma: float,
    closed_neighbors: Sequence[set[int]],
    rng: random.Random,
    max_steps: int,
) -> tuple[list[int], int, int, bool]:
    """Run asynchronous best-response dynamics for Problem 2.

    Process:
    - find all players whose current action differs from best response
    - randomly select one such player
    - update that player
    - stop when no player wants to deviate
    """
    state = list(initial_state)
    move_count = 0

    for _ in range(max_steps):
        improvable_nodes: list[int] = []
        br_map: dict[int, int] = {}

        for i in range(graph.n):
            br_i = best_response_problem2(
                graph=graph,
                state=state,
                i=i,
                alpha=alpha,
                beta=beta,
                gamma=gamma,
                closed_neighbors=closed_neighbors,
                rng=rng,
            )
            br_map[i] = br_i
            if br_i != state[i]:
                improvable_nodes.append(i)

        if not improvable_nodes:
            return state, move_count, cardinality(state), True

        chosen_i = rng.choice(improvable_nodes)
        # Use the cached BR to avoid re-invoking random tie-breaking a second time,
        # which could yield a different result and cause a phantom move_count increment.
        state[chosen_i] = br_map[chosen_i]
        move_count += 1

    return state, move_count, cardinality(state), False


def is_mutually_matched(state: Sequence[Optional[int]], i: int) -> bool:
    """Return True if player i is in a mutual proposal pair."""
    if not (0 <= i < len(state)):
        return False

    partner = state[i]
    if partner is None:
        return False
    if not (0 <= partner < len(state)):
        return False
    return state[partner] == i


def matched_partner(state: Sequence[Optional[int]], i: int) -> Optional[int]:
    """Return i's matched partner if mutual, otherwise None."""
    if is_mutually_matched(state, i):
        return state[i]
    return None


def utility_problem3(graph: Graph, state: Sequence[Optional[int]], i: int) -> float:
    """Compute utility for player i under the matching-game design.

    Utility rule:
    - choose None => 0
    - choose j and state[j] == i => 3 + bias(j)
    - choose j and state[j] is None => 1 + bias(j)
    - otherwise => -1 + bias(j)

    bias(j) = 1 / (1 + degree(j))
    """
    strategy = state[i]
    if strategy is None:
        return 0.0

    if not (0 <= strategy < graph.n):
        return -1.0
    if not graph.is_edge(i, strategy):
        return -1.0

    neighbor = strategy
    bias = 1.0 / (1.0 + graph.degree(neighbor))

    if state[neighbor] == i:
        return 3.0 + bias
    if state[neighbor] is None:
        return 1.0 + bias
    return -1.0 + bias


def best_response_problem3(
    graph: Graph,
    state: Sequence[Optional[int]],
    i: int,
    rng: random.Random,
) -> Optional[int]:
    """Compute best response for Problem 3 by utility enumeration.

    Tie-breaking among max-utility strategies:
    1) prefer smaller-degree neighbor,
    2) if still tie, random,
    3) None is included as a valid strategy.
    """
    candidate_strategies: list[Optional[int]] = [None, *graph.neighbors(i)]
    utilities: dict[Optional[int], float] = {}

    for strategy in candidate_strategies:
        trial_state = list(state)
        trial_state[i] = strategy
        utilities[strategy] = utility_problem3(graph, trial_state, i)

    best_utility = max(utilities.values())
    best_candidates = [strategy for strategy in candidate_strategies if utilities[strategy] == best_utility]

    neighbor_candidates = [strategy for strategy in best_candidates if strategy is not None]
    if neighbor_candidates:
        min_degree = min(graph.degree(strategy) for strategy in neighbor_candidates)
        degree_tied = [strategy for strategy in neighbor_candidates if graph.degree(strategy) == min_degree]
        return rng.choice(degree_tied)

    return rng.choice(best_candidates)


def compute_matching_edges(state: Sequence[Optional[int]]) -> set[tuple[int, int]]:
    """Build undirected matching edge set from a proposal state.

    Only mutual proposals create matched edges.
    """
    edges: set[tuple[int, int]] = set()
    for i in range(len(state)):
        j = matched_partner(state, i)
        if j is None:
            continue
        u, v = (i, j) if i < j else (j, i)
        edges.add((u, v))
    return edges


def matching_cardinality(state: Sequence[Optional[int]]) -> int:
    """Return number of matched pairs (not matched vertices)."""
    return len(compute_matching_edges(state))


def is_valid_matching_state(graph: Graph, state: Sequence[Optional[int]]) -> bool:
    """Check if a proposal state corresponds to a legal matching."""
    if len(state) != graph.n:
        return False

    for i, choice in enumerate(state):
        if choice is None:
            continue
        if not (0 <= choice < graph.n):
            return False
        if choice == i:
            return False
        if not graph.is_edge(i, choice):
            return False

    edges = compute_matching_edges(state)
    used_vertices: set[int] = set()
    for u, v in edges:
        if u in used_vertices or v in used_vertices:
            return False
        # Treat matching edges as undirected graph edges.
        if not graph.is_edge(u, v) or not graph.is_edge(v, u):
            return False
        used_vertices.add(u)
        used_vertices.add(v)

    return True


def is_maximal_matching_state(graph: Graph, state: Sequence[Optional[int]]) -> bool:
    """Check if matching induced by state is maximal."""
    if not is_valid_matching_state(graph, state):
        return False

    edges = compute_matching_edges(state)
    matched_vertices: set[int] = set()
    for u, v in edges:
        matched_vertices.add(u)
        matched_vertices.add(v)

    for u in range(graph.n):
        for v in range(u + 1, graph.n):
            if not graph.is_edge(u, v) or not graph.is_edge(v, u):
                continue
            if u in matched_vertices or v in matched_vertices:
                continue
            # Found an uncovered edge; we can add it, so current matching is not maximal.
            return False

    return True


def _random_problem3_state(graph: Graph, rng: random.Random, none_probability: float) -> list[Optional[int]]:
    """Generate one random proposal state for Problem 3."""
    state: list[Optional[int]] = []
    for i in range(graph.n):
        neighbors = graph.neighbors(i)
        if not neighbors:
            state.append(None)
            continue

        if rng.random() < none_probability:
            state.append(None)
        else:
            state.append(rng.choice(neighbors))
    return state


def generate_problem3_initial_states(
    graph: Graph,
    rng: random.Random,
    random_start_count: int,
) -> list[list[Optional[int]]]:
    """Build diverse initial states for Problem 3 multi-start search."""
    starts: list[list[Optional[int]]] = []

    # Deterministic anchor: everyone chooses null.
    starts.append([None for _ in range(graph.n)])

    # Random mixed starts: None/proposal at equal chance.
    mixed_count = max(1, random_start_count // 2)
    for _ in range(mixed_count):
        starts.append(_random_problem3_state(graph, rng, none_probability=0.5))

    # Bias toward more None.
    sparse_count = max(1, random_start_count // 4)
    for _ in range(sparse_count):
        starts.append(_random_problem3_state(graph, rng, none_probability=0.75))

    # Bias toward more proposals.
    dense_count = max(1, random_start_count - mixed_count - sparse_count)
    for _ in range(dense_count):
        starts.append(_random_problem3_state(graph, rng, none_probability=0.2))

    return starts


def run_problem3_dynamics(
    graph: Graph,
    initial_state: Sequence[Optional[int]],
    rng: random.Random,
    max_steps: int,
) -> tuple[list[Optional[int]], int, bool]:
    """Run asynchronous best-response dynamics for Problem 3.

    Update-order heuristic among improvable players:
    1) prioritize currently unmatched players,
    2) among them prioritize smaller degree,
    3) random tie-break.
    """
    state = list(initial_state)
    move_count = 0

    for _ in range(max_steps):
        improvable_nodes: list[int] = []
        br_map: dict[int, Optional[int]] = {}

        for i in range(graph.n):
            br_i = best_response_problem3(graph=graph, state=state, i=i, rng=rng)
            br_map[i] = br_i
            if br_i != state[i]:
                improvable_nodes.append(i)

        if not improvable_nodes:
            return state, move_count, True

        unmatched_improvable = [i for i in improvable_nodes if not is_mutually_matched(state, i)]
        candidate_nodes = unmatched_improvable if unmatched_improvable else improvable_nodes

        min_degree = min(graph.degree(i) for i in candidate_nodes)
        degree_tied = [i for i in candidate_nodes if graph.degree(i) == min_degree]
        chosen_i = rng.choice(degree_tied)

        state[chosen_i] = br_map[chosen_i]
        move_count += 1

    return state, move_count, False


def solve_maximal_matching(graph: Graph) -> SolverResult:
    """Solver for Requirement 2: Matching Game / Maximal Matching.

    This implementation keeps the game-theoretic structure:
    players repeatedly update to utility-maximizing best responses.
    Multi-start execution is used to improve the chance of finding larger
    maximal matchings, and the returned extremum is the maximum cardinality
    among valid maximal candidates.
    """
    rng = random.Random()
    random_start_count = max(24, 3 * graph.n)
    max_steps = max(1000, 80 * graph.n * graph.n)
    initial_states = generate_problem3_initial_states(graph, rng, random_start_count)

    best_valid_maximal: Optional[SolverResult] = None
    fallback: Optional[SolverResult] = None

    for start in initial_states:
        final_state, moves, converged = run_problem3_dynamics(
            graph=graph,
            initial_state=start,
            rng=rng,
            max_steps=max_steps,
        )

        is_valid = is_valid_matching_state(graph, final_state)
        is_maximal = is_maximal_matching_state(graph, final_state) if is_valid else False
        final_cardinality = matching_cardinality(final_state)
        matching_edges = sorted(compute_matching_edges(final_state))

        candidate = SolverResult(
            cardinality=final_cardinality,
            move_count=moves,
            state={
                "strategy_state": final_state,
                "matching_edges": matching_edges,
                "converged": converged,
                "starts": len(initial_states),
                "is_maximal": is_maximal,
            },
            is_valid=is_valid,
        )

        if fallback is None or candidate.cardinality > fallback.cardinality:
            fallback = candidate

        if not (is_valid and is_maximal):
            continue

        if best_valid_maximal is None:
            best_valid_maximal = candidate
            continue

        if candidate.cardinality > best_valid_maximal.cardinality:
            best_valid_maximal = candidate
        elif candidate.cardinality == best_valid_maximal.cardinality:
            best_valid_maximal = rng.choice([best_valid_maximal, candidate])

    if best_valid_maximal is not None:
        return best_valid_maximal

    if fallback is None:
        return SolverResult(
            cardinality=-1,
            move_count=None,
            state={
                "strategy_state": [None for _ in range(graph.n)],
                "matching_edges": [],
                "converged": False,
                "starts": 0,
                "is_maximal": False,
            },
            is_valid=False,
        )
    return fallback


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
