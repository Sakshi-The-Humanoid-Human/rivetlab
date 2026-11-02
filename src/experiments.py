"""Rivet Popper experiments: random vs targeted species removal."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

from src.simulation import run_extinction


@dataclass
class ExperimentStep:
    step: int
    removed_species: list[int] = field(default_factory=list)
    n_remaining: int = 0
    n_edges: int = 0
    density: float = 0.0
    largest_component: int = 0


@dataclass
class ExperimentResult:
    name: str
    initial_nodes: int
    steps: list[ExperimentStep] = field(default_factory=list)
    removal_sequence: list[int] = field(default_factory=list)

    @property
    def survival_series(self) -> list[float]:
        return [
            100.0 * s.n_remaining / max(self.initial_nodes, 1)
            for s in self.steps
        ]

    @property
    def removal_pct_series(self) -> list[float]:
        return [
            100.0 * len(s.removed_species) / max(self.initial_nodes, 1)
            for s in self.steps
        ]

    @property
    def r50(self) -> float | None:
        """Fraction directly removed when survival first drops to <= 50%."""
        if self.initial_nodes == 0:
            return None
        for s in self.steps:
            if s.n_remaining <= 0.5 * self.initial_nodes:
                return s.step / self.initial_nodes
        return None


def _network_step_stats(G: nx.DiGraph, removed_set: set) -> ExperimentStep:
    remaining = set(G.nodes()) - removed_set
    sub = G.subgraph(remaining)
    weak = list(nx.weakly_connected_components(sub))
    largest = max(weak, key=len) if weak else set()
    return ExperimentStep(
        step=0,
        removed_species=list(removed_set),
        n_remaining=sub.number_of_nodes(),
        n_edges=sub.number_of_edges(),
        density=nx.density(sub) if sub.number_of_nodes() > 1 else 0.0,
        largest_component=len(largest),
    )


def run_targeted_removal(
    G: nx.DiGraph,
    ranking: str = "degree",
    adaptive: bool = True,
    max_removals: int | None = None,
    strict: bool = False,
) -> ExperimentResult:
    """Remove species using a centrality ranking.

    Parameters
    ----------
    ranking : {"degree", "betweenness"}
        Centrality metric used to pick the next species.
    adaptive : bool
        If True, recompute centrality after every removal.
    max_removals : int | None
        Maximum number of direct removals. Defaults to all species.
    strict : bool
        Passed to the extinction simulator.
    """
    if G.number_of_nodes() == 0:
        return ExperimentResult(name=f"targeted_{ranking}", initial_nodes=0)

    max_removals = max_removals or G.number_of_nodes()
    working = G.copy()
    removed: set[int] = set()
    steps: list[ExperimentStep] = []
    removal_sequence: list[int] = []

    # Baseline step 0
    steps.append(_network_step_stats(G, removed))
    steps[0].step = 0

    for step_idx in range(1, max_removals + 1):
        subgraph = working.subgraph(set(working.nodes()) - removed)
        if subgraph.number_of_nodes() == 0:
            break
        if ranking == "degree":
            scores = nx.degree_centrality(subgraph)
        elif ranking == "betweenness":
            scores = nx.betweenness_centrality(subgraph)
        else:
            raise ValueError(f"Unknown ranking: {ranking}")

        # Pick highest score among remaining
        candidates = {n: s for n, s in scores.items() if n not in removed}
        if not candidates:
            break
        next_sp = max(candidates, key=candidates.get)

        result = run_extinction(working, [next_sp], strict=strict)
        for event in result.log:
            removed.add(event.species_id)
            if event.reason == "direct":
                removal_sequence.append(event.species_id)

        stats = _network_step_stats(G, removed)
        stats.step = step_idx
        steps.append(stats)

        if not adaptive:
            # Use original ranking order: remove next highest from original graph
            pass

    return ExperimentResult(
        name=f"targeted_{ranking}_{'adaptive' if adaptive else 'static'}",
        initial_nodes=G.number_of_nodes(),
        steps=steps,
        removal_sequence=removal_sequence,
    )


def run_random_removal(
    G: nx.DiGraph,
    n_trials: int = 10,
    seed: int = 42,
    max_removals: int | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    """Run multiple random-removal trials and return aggregated statistics.

    Returns a DataFrame with columns for removal percentage, mean survival,
    std survival, mean remaining edges, etc.
    """
    if G.number_of_nodes() == 0:
        return pd.DataFrame()

    max_removals = max_removals or G.number_of_nodes()
    rng = np.random.default_rng(seed)
    trial_results: list[ExperimentResult] = []

    for t in range(n_trials):
        trial_seed = int(rng.integers(0, 2**31))
        tr = _single_random_trial(
            G, seed=trial_seed, max_removals=max_removals, strict=strict
        )
        trial_results.append(tr)

    # Aggregate across trials by step index
    max_steps = max(len(tr.steps) for tr in trial_results) if trial_results else 0
    records = []
    for i in range(max_steps):
        surv = [
            tr.steps[i].n_remaining / max(tr.initial_nodes, 1)
            for tr in trial_results
            if i < len(tr.steps)
        ]
        edges = [tr.steps[i].n_edges for tr in trial_results if i < len(tr.steps)]
        dens = [tr.steps[i].density for tr in trial_results if i < len(tr.steps)]
        lcc = [tr.steps[i].largest_component for tr in trial_results if i < len(tr.steps)]
        removal_pct = i / max(G.number_of_nodes(), 1)
        records.append(
            {
                "removal_fraction": removal_pct,
                "mean_survival_fraction": np.mean(surv) if surv else 0.0,
                "std_survival_fraction": np.std(surv) if surv else 0.0,
                "mean_remaining_edges": np.mean(edges) if edges else 0.0,
                "mean_density": np.mean(dens) if dens else 0.0,
                "mean_largest_component": np.mean(lcc) if lcc else 0.0,
            }
        )
    r50_values = [tr.r50 for tr in trial_results if tr.r50 is not None]
    return {
        "df": pd.DataFrame(records),
        "mean_r50": float(np.mean(r50_values)) if r50_values else None,
        "std_r50": float(np.std(r50_values)) if r50_values else None,
    }


def _single_random_trial(
    G: nx.DiGraph, seed: int, max_removals: int, strict: bool
) -> ExperimentResult:
    rng = np.random.default_rng(seed)
    working = G.copy()
    removed: set[int] = set()
    steps: list[ExperimentStep] = []
    removal_sequence: list[int] = []

    steps.append(_network_step_stats(G, removed))
    steps[0].step = 0

    for step_idx in range(1, max_removals + 1):
        remaining = [n for n in working.nodes() if n not in removed]
        if not remaining:
            break
        next_sp = int(rng.choice(remaining))
        result = run_extinction(working, [next_sp], strict=strict)
        for event in result.log:
            removed.add(event.species_id)
            if event.reason == "direct":
                removal_sequence.append(event.species_id)

        stats = _network_step_stats(G, removed)
        stats.step = step_idx
        steps.append(stats)

    return ExperimentResult(
        name="random",
        initial_nodes=G.number_of_nodes(),
        steps=steps,
        removal_sequence=removal_sequence,
    )
