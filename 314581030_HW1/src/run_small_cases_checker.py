#!/usr/bin/env python3
"""Run small manual cases and compact WS benchmarks via checker.py.

This script intentionally reuses checker.py and only adds orchestration/plotting.
Outputs in checker_outputs/:
  - small_cases_by_type_trials30.png
  - ws_vary_n_trials10.png
  - ws_vary_p_trials10.png
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt

# Small manual cases
TRIALS_PER_CASE = 30
CASES: list[tuple[str, int]] = [
    ("given_case", 6),
    ("P2", 2),
    ("P3", 3),
    ("P4", 4),
    ("P5", 5),
    ("C4", 4),
    ("C5", 5),
    ("C6", 6),
    ("Star6", 6),
    ("K3", 3),
    ("K4", 4),
]

# WS benchmarks (as requested: small trial count, few n values, p can be denser)
WS_TRIALS = 10
WS_N_VALUES = [20, 30, 40]
WS_K_FOR_N = 4
WS_P_FIXED = 0.3

WS_P_VALUES = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
WS_N_FIXED = 40
WS_K_FOR_P = 4

# Readable names for the three solver lines.
LABEL_1 = "Problem 1"
LABEL_2 = "Problem 2"
LABEL_3 = "Problem 3"


@dataclass
class PointMetrics:
    x: float
    avg_card_1: float
    avg_card_2: float
    avg_card_3: float
    avg_move_1: float
    avg_move_2: float
    avg_move_3: float
    valid_1: float
    valid_2: float
    valid_3: float
    max_3: float
    ne_1: float
    ne_2: float
    ne_3: float
    unmatched_3: float
    unmatch_nb_3: float


@dataclass
class CaseMetrics(PointMetrics):
    case_name: str
    n: int


def case_family(case_name: str) -> str:
    if case_name.startswith("P"):
        return "Path"
    if case_name.startswith("C"):
        return "Cycle"
    if case_name.startswith("K"):
        return "Dense/Complete"
    if case_name.startswith("Star"):
        return "Star"
    if case_name == "given_case":
        return "Given"
    return "Other"


def _parse_metric_line(line: str) -> PointMetrics:
    values = [float(token) for token in re.findall(r"-?\d+\.\d+", line)]
    if len(values) != 16:
        raise ValueError(f"Expected 16 numbers in checker row, got {len(values)}")
    return PointMetrics(
        x=values[0],
        avg_card_1=values[1],
        avg_card_2=values[2],
        avg_card_3=values[3],
        avg_move_1=values[4],
        avg_move_2=values[5],
        avg_move_3=values[6],
        valid_1=values[7],
        valid_2=values[8],
        valid_3=values[9],
        max_3=values[10],
        ne_1=values[11],
        ne_2=values[12],
        ne_3=values[13],
        unmatched_3=values[14],
        unmatch_nb_3=values[15],
    )


def _parse_checker_rows(stdout: str) -> list[PointMetrics]:
    data_pattern = re.compile(r"^\s*\d+\.\d+\s+\|")
    rows: list[PointMetrics] = []
    for line in stdout.splitlines():
        if data_pattern.match(line):
            rows.append(_parse_metric_line(line))
    if not rows:
        raise ValueError("No checker data rows found")
    return rows


def _run_checker(command: list[str], env: Optional[dict[str, str]] = None) -> list[PointMetrics]:
    completed = subprocess.run(command, capture_output=True, text=True, env=env)
    if completed.returncode != 0:
        raise RuntimeError(f"checker failed:\n{completed.stderr}")
    return _parse_checker_rows(completed.stdout)


def run_small_case(base_dir: Path, case_name: str, n: int) -> CaseMetrics:
    checker_path = base_dir / "checker.py"
    manual_generator = base_dir / "manual_ws_case_generator.py"

    with tempfile.TemporaryDirectory() as tmp:
        command = [
            sys.executable,
            str(checker_path),
            "--mode",
            "n",
            "--n-values",
            str(n),
            "--k",
            "2",
            "--p",
            "0.0",
            "--trials",
            str(TRIALS_PER_CASE),
            "--seed-base",
            "1",
            "--ws-generator",
            str(manual_generator),
            "--output-dir",
            tmp,
        ]
        env = os.environ.copy()
        env["MANUAL_CASE"] = case_name
        row = _run_checker(command, env=env)[0]

    return CaseMetrics(
        case_name=case_name,
        n=n,
        x=row.x,
        avg_card_1=row.avg_card_1,
        avg_card_2=row.avg_card_2,
        avg_card_3=row.avg_card_3,
        avg_move_1=row.avg_move_1,
        avg_move_2=row.avg_move_2,
        avg_move_3=row.avg_move_3,
        valid_1=row.valid_1,
        valid_2=row.valid_2,
        valid_3=row.valid_3,
        max_3=row.max_3,
        ne_1=row.ne_1,
        ne_2=row.ne_2,
        ne_3=row.ne_3,
        unmatched_3=row.unmatched_3,
        unmatch_nb_3=row.unmatch_nb_3,
    )


def plot_small_cases(output_path: Path, all_metrics: list[CaseMetrics]) -> None:
    family_order = ["Path", "Cycle", "Dense/Complete", "Star", "Given"]
    grouped: dict[str, list[CaseMetrics]] = {family: [] for family in family_order}
    for m in all_metrics:
        grouped.setdefault(case_family(m.case_name), []).append(m)
    for family in grouped:
        grouped[family] = sorted(grouped[family], key=lambda item: item.n)

    fig, axes = plt.subplots(len(family_order), 3, figsize=(24, 18))
    fig.suptitle(
        f"Small Test Cases by Type (averaged over {TRIALS_PER_CASE} trials)",
        fontsize=14,
    )

    for row_idx, family in enumerate(family_order):
        metrics = grouped.get(family, [])
        ax_card, ax_move, ax_p3 = axes[row_idx][0], axes[row_idx][1], axes[row_idx][2]

        if not metrics:
            for ax in (ax_card, ax_move, ax_p3):
                ax.text(0.5, 0.5, "No data", ha="center", va="center")
                ax.set_axis_off()
            continue

        x = list(range(len(metrics)))
        labels = [f"{m.case_name}(n={m.n})" for m in metrics]

        ax_card.plot(x, [m.avg_card_1 for m in metrics], marker="o", label=LABEL_1)
        ax_card.plot(x, [m.avg_card_2 for m in metrics], marker="o", label=LABEL_2)
        ax_card.plot(x, [m.avg_card_3 for m in metrics], marker="o", label=LABEL_3)
        ax_card.set_title(f"{family} - Cardinality")
        ax_card.set_ylabel("avg cardinality")
        ax_card.grid(alpha=0.3)
        ax_card.set_xticks(x)
        ax_card.set_xticklabels(labels, rotation=20, ha="right")
        ax_card.legend()

        ax_move.plot(x, [m.avg_move_1 for m in metrics], marker="o", label=LABEL_1)
        ax_move.plot(x, [m.avg_move_2 for m in metrics], marker="o", label=LABEL_2)
        ax_move.plot(x, [m.avg_move_3 for m in metrics], marker="o", label=LABEL_3)
        ax_move.set_title(f"{family} - Move Count")
        ax_move.set_ylabel("avg move count")
        ax_move.grid(alpha=0.3)
        ax_move.set_xticks(x)
        ax_move.set_xticklabels(labels, rotation=20, ha="right")
        ax_move.legend()

        unmatched_rate = [m.unmatched_3 / max(1, m.n) for m in metrics]
        unmatch_nb_rate = [m.unmatch_nb_3 / max(1, m.n) for m in metrics]
        ax_p3.plot(x, [m.valid_3 for m in metrics], marker="o", label="valid_p3")
        ax_p3.plot(x, [m.max_3 for m in metrics], marker="o", label="max_p3")
        ax_p3.plot(x, [m.ne_3 for m in metrics], marker="o", label="ne_p3")
        ax_p3.plot(x, unmatched_rate, marker="s", linestyle="--", label="unmatched/n")
        ax_p3.plot(x, unmatch_nb_rate, marker="s", linestyle="--", label="unmatch_nb/n")
        ax_p3.set_title(f"{family} - Problem 3 extra checks")
        ax_p3.set_ylabel("rate")
        ax_p3.set_ylim(0.0, 1.05)
        ax_p3.grid(alpha=0.3)
        ax_p3.set_xticks(x)
        ax_p3.set_xticklabels(labels, rotation=20, ha="right")
        ax_p3.legend()

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def run_ws_sweep_n(base_dir: Path) -> list[PointMetrics]:
    checker_path = base_dir / "checker.py"
    with tempfile.TemporaryDirectory() as tmp:
        command = [
            sys.executable,
            str(checker_path),
            "--mode",
            "n",
            "--n-values",
            *[str(v) for v in WS_N_VALUES],
            "--k",
            str(WS_K_FOR_N),
            "--p",
            str(WS_P_FIXED),
            "--trials",
            str(WS_TRIALS),
            "--seed-base",
            "100",
            "--output-dir",
            tmp,
        ]
        return _run_checker(command)


def run_ws_sweep_p(base_dir: Path) -> list[PointMetrics]:
    checker_path = base_dir / "checker.py"
    with tempfile.TemporaryDirectory() as tmp:
        command = [
            sys.executable,
            str(checker_path),
            "--mode",
            "p",
            "--n",
            str(WS_N_FIXED),
            "--k",
            str(WS_K_FOR_P),
            "--p-values",
            *[str(v) for v in WS_P_VALUES],
            "--trials",
            str(WS_TRIALS),
            "--seed-base",
            "200",
            "--output-dir",
            tmp,
        ]
        return _run_checker(command)


def plot_ws(rows: list[PointMetrics], output_path: Path, title: str, x_label: str, n_for_norm: list[float]) -> None:
    x = [r.x for r in rows]
    fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
    fig.suptitle(title, fontsize=14)

    axes[0].plot(x, [r.avg_card_1 for r in rows], marker="o", label=LABEL_1)
    axes[0].plot(x, [r.avg_card_2 for r in rows], marker="o", label=LABEL_2)
    axes[0].plot(x, [r.avg_card_3 for r in rows], marker="o", label=LABEL_3)
    axes[0].set_ylabel("avg cardinality")
    axes[0].set_title("Cardinality")
    axes[0].grid(alpha=0.3)
    axes[0].legend()

    axes[1].plot(x, [r.avg_move_1 for r in rows], marker="o", label=LABEL_1)
    axes[1].plot(x, [r.avg_move_2 for r in rows], marker="o", label=LABEL_2)
    axes[1].plot(x, [r.avg_move_3 for r in rows], marker="o", label=LABEL_3)
    axes[1].set_ylabel("avg move count")
    axes[1].set_title("Move Count")
    axes[1].grid(alpha=0.3)
    axes[1].legend()

    unmatched_rate = [r.unmatched_3 / max(1.0, n) for r, n in zip(rows, n_for_norm)]
    unmatch_nb_rate = [r.unmatch_nb_3 / max(1.0, n) for r, n in zip(rows, n_for_norm)]
    axes[2].plot(x, [r.valid_3 for r in rows], marker="o", label="valid_p3")
    axes[2].plot(x, [r.max_3 for r in rows], marker="o", label="max_p3")
    axes[2].plot(x, [r.ne_3 for r in rows], marker="o", label="ne_p3")
    axes[2].plot(x, unmatched_rate, marker="s", linestyle="--", label="unmatched/n")
    axes[2].plot(x, unmatch_nb_rate, marker="s", linestyle="--", label="unmatch_nb/n")
    axes[2].set_ylabel("rate")
    axes[2].set_ylim(0.0, 1.05)
    axes[2].set_title("Problem 3 extra checks")
    axes[2].grid(alpha=0.3)
    axes[2].legend()
    axes[2].set_xlabel(x_label)

    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def print_problem3_rows(tag: str, rows: list[PointMetrics]) -> None:
    print(f"\n  [{tag}] Problem 3 verification metrics")
    for r in rows:
        print(
            f"  x={r.x:6.2f} | valid_p3={r.valid_3:.3f} max_p3={r.max_3:.3f} ne_p3={r.ne_3:.3f} "
            f"| unmatched={r.unmatched_3:.3f} unmatch_nb={r.unmatch_nb_3:.3f}"
        )


def main(output_dir: Optional[Path] = None) -> None:
    base_dir = Path(__file__).resolve().parent
    if output_dir is None:
        output_dir = base_dir / "checker_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Keep output directory clean: only the latest PNGs from this script.
    for png in output_dir.glob("*.png"):
        png.unlink()

    # 1) Small manual cases
    small_metrics: list[CaseMetrics] = []
    for case_name, n in CASES:
        print(f"  [small] {case_name} (n={n})")
        small_metrics.append(run_small_case(base_dir, case_name, n))

    small_out = output_dir / f"small_cases_by_type_trials{TRIALS_PER_CASE}.png"
    plot_small_cases(small_out, small_metrics)
    print(f"  Saved: {small_out}")

    print("\n  [Small] Problem 3 verification metrics")
    for m in sorted(small_metrics, key=lambda item: (case_family(item.case_name), item.n, item.case_name)):
        print(
            f"  {m.case_name:>10} | valid_p3={m.valid_3:.3f} max_p3={m.max_3:.3f} ne_p3={m.ne_3:.3f} "
            f"| unmatched={m.unmatched_3:.3f} unmatch_nb={m.unmatch_nb_3:.3f}"
        )

    # 2) WS benchmarks: vary n
    ws_n_rows = run_ws_sweep_n(base_dir)
    ws_n_out = output_dir / f"ws_vary_n_trials{WS_TRIALS}.png"
    plot_ws(
        ws_n_rows,
        ws_n_out,
        title=(
            f"WS Benchmark (vary n, trials={WS_TRIALS})\n"
            f"k={WS_K_FOR_N}, p={WS_P_FIXED}, n={WS_N_VALUES}"
        ),
        x_label="n",
        n_for_norm=[r.x for r in ws_n_rows],
    )
    print(f"  Saved: {ws_n_out}")
    print_problem3_rows("WS vary n", ws_n_rows)

    # 3) WS benchmarks: vary p
    ws_p_rows = run_ws_sweep_p(base_dir)
    ws_p_out = output_dir / f"ws_vary_p_trials{WS_TRIALS}.png"
    plot_ws(
        ws_p_rows,
        ws_p_out,
        title=(
            f"WS Benchmark (vary p, trials={WS_TRIALS})\n"
            f"n={WS_N_FIXED}, k={WS_K_FOR_P}, p={WS_P_VALUES}"
        ),
        x_label="p",
        n_for_norm=[float(WS_N_FIXED) for _ in ws_p_rows],
    )
    print(f"  Saved: {ws_p_out}")
    print_problem3_rows("WS vary p", ws_p_rows)


if __name__ == "__main__":
    main()
