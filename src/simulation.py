"""Extinction simulation engine for RivetLab.

Edges follow RESOURCE -> CONSUMER. A non-basal consumer becomes secondarily
extinct when it has no remaining in-neighbours (resources). Basal species are
protected from secondary extinction but can be directly removed.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

import networkx as nx


@dataclass
class ExtinctionEvent:
    round: int
    species_id: int
    species_name: str
    reason: str  # "direct", "secondary", "strict"


@dataclass
class SimulationResult:
    initial_graph: nx.DiGraph = field(repr=False)
    final_graph: nx.DiGraph = field(repr=False)
    log: list[ExtinctionEvent] = field(default_factory=list)
    rounds: int = 0

    @property
    def removed_species(self) -> list[int]:
        return [e.species_id for e in self.log]

    @property
    def remaining_nodes(self) -> int:
        return self.final_graph.number_of_nodes()

    @property
    def remaining_edges(self) -> int:
        return self.final_graph.number_of_edges()


def _node_name(G: nx.DiGraph, n: Any) -> str:
    return str(G.nodes[n].get("name", n))


def _find_secondary_extinctions(
    G: nx.DiGraph, removed: set, strict: bool = False
) -> dict[int, str]:
    """Return mapping of consumers to extinction reason for the current round.

    Reasons:
        - "secondary": no surviving resources left.
        - "strict": in strict mode, has resources but is unreachable from any
          surviving basal species.
    """
    surviving_nodes = set(G.nodes()) - removed
    if not surviving_nodes:
        return {}
    sub = G.subgraph(surviving_nodes)

    # Basal species are protected from secondary extinction. Basal status is
    # determined from the original graph (in-degree == 0).
    original_basal = {n for n in G.nodes() if G.in_degree(n) == 0}

    reasons: dict[int, str] = {}
    for n in sub.nodes():
        if n in original_basal:
            continue  # basal species are protected from secondary extinction
        if not list(sub.predecessors(n)):
            reasons[n] = "secondary"

    if strict:
        # Additional strict rule: consumer must be reachable from at least one surviving basal node
        surviving_basal = original_basal & surviving_nodes
        for n in sub.nodes():
            if n in surviving_basal or n in reasons:
                continue
            reachable = any(nx.has_path(sub, b, n) for b in surviving_basal)
            if not reachable:
                reasons[n] = "strict"

    return reasons


def run_extinction(
    G: nx.DiGraph,
    direct_removals: list[int],
    strict: bool = False,
) -> SimulationResult:
    """Run a cascading extinction simulation.

    Parameters
    ----------
    G : nx.DiGraph
        Original food web (RESOURCE -> CONSUMER). Not mutated.
    direct_removals : list[int]
        Species IDs to remove directly.
    strict : bool
        If True, also remove consumers that are no longer reachable from any
        surviving basal species.

    Returns
    -------
    SimulationResult
    """
    if G.number_of_nodes() == 0:
        return SimulationResult(initial_graph=G, final_graph=G.copy(), log=[], rounds=0)

    working = G.copy()
    removed: set[int] = set()
    log: list[ExtinctionEvent] = []
    current_round = 0

    # Direct removals
    for sp in direct_removals:
        if sp in working and sp not in removed:
            removed.add(sp)
            log.append(
                ExtinctionEvent(
                    round=current_round,
                    species_id=sp,
                    species_name=_node_name(G, sp),
                    reason="direct",
                )
            )

    # Cascading secondary extinctions
    while True:
        current_round += 1
        newly_extinct = _find_secondary_extinctions(working, removed, strict=strict)
        # Filter out already removed
        newly_extinct = {n: r for n, r in newly_extinct.items() if n not in removed}
        if not newly_extinct:
            break
        for n, reason in newly_extinct.items():
            removed.add(n)
            log.append(
                ExtinctionEvent(
                    round=current_round,
                    species_id=n,
                    species_name=_node_name(G, n),
                    reason=reason,
                )
            )

    final_graph = working.subgraph(set(working.nodes()) - removed).copy()
    return SimulationResult(
        initial_graph=G,
        final_graph=final_graph,
        log=log,
        rounds=current_round - 1 if current_round > 0 else 0,
    )


def remove_single_species(
    G: nx.DiGraph, species_id: int, strict: bool = False
) -> SimulationResult:
    """Convenience wrapper to remove one species and cascade."""
    return run_extinction(G, [species_id], strict=strict)


def reset_simulation(initial_graph: nx.DiGraph) -> nx.DiGraph:
    """Return a fresh annotated copy of the initial graph."""
    return initial_graph.copy()
