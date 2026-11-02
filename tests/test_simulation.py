"""Unit tests for the RivetLab extinction simulation engine."""

import networkx as nx
import pytest

from src.simulation import (
    ExtinctionEvent,
    remove_single_species,
    reset_simulation,
    run_extinction,
)


def _simple_food_web() -> nx.DiGraph:
    """Hand-constructed food web.

    Basal: 1, 2
    Intermediate: 3 (eats 1), 4 (eats 2)
    Top: 5 (eats 3, 4)
    """
    G = nx.DiGraph()
    for n in range(1, 6):
        G.add_node(n, name=f"sp{n}", group="species")
    G.add_edge(1, 3)
    G.add_edge(2, 4)
    G.add_edge(3, 5)
    G.add_edge(4, 5)
    return G


def test_direct_removal() -> None:
    G = _simple_food_web()
    result = remove_single_species(G, 5)
    assert 5 in result.removed_species
    assert result.final_graph.number_of_nodes() == 4
    assert result.final_graph.number_of_edges() == 2


def test_one_round_secondary_extinction() -> None:
    G = _simple_food_web()
    result = remove_single_species(G, 1)
    # Species 3 loses its only resource and should go secondarily extinct.
    assert 3 in result.removed_species
    # Species 5 loses resource 3 but still has resource 4, so it survives.
    assert 5 not in result.removed_species


def test_multi_round_cascading_extinction() -> None:
    G = _simple_food_web()
    result = remove_single_species(G, 1)
    # 1 removed directly, 3 loses its only resource -> secondary.
    # Species 5 still has resource 4, so it survives.
    assert result.removed_species == [1, 3]
    assert result.final_graph.number_of_nodes() == 3


def test_chain_cascading_extinction() -> None:
    """A linear chain demonstrates multi-round cascading extinction."""
    G = nx.DiGraph()
    for n in [1, 3, 5]:
        G.add_node(n, name=f"sp{n}")
    G.add_edge(1, 3)
    G.add_edge(3, 5)
    result = remove_single_species(G, 1)
    assert result.removed_species == [1, 3, 5]
    assert result.final_graph.number_of_nodes() == 0


def test_basal_species_protection() -> None:
    G = _simple_food_web()
    result = remove_single_species(G, 5)
    # Removing top predator should not trigger basal extinction.
    basal = [n for n in result.final_graph.nodes() if result.final_graph.in_degree(n) == 0]
    assert 1 in basal and 2 in basal


def test_reset_returns_original() -> None:
    G = _simple_food_web()
    result = remove_single_species(G, 1)
    reset = reset_simulation(G)
    assert reset.number_of_nodes() == G.number_of_nodes()
    assert reset.number_of_edges() == G.number_of_edges()
    assert list(reset.nodes()) == list(G.nodes())


def test_original_graph_immutability() -> None:
    G = _simple_food_web()
    original_nodes = set(G.nodes())
    original_edges = set(G.edges())
    remove_single_species(G, 1)
    assert set(G.nodes()) == original_nodes
    assert set(G.edges()) == original_edges


def test_empty_graph() -> None:
    G = nx.DiGraph()
    result = remove_single_species(G, 1)
    assert result.final_graph.number_of_nodes() == 0
    assert result.log == []


def test_extinction_log_contents() -> None:
    G = _simple_food_web()
    result = remove_single_species(G, 1)
    reasons = [e.reason for e in result.log]
    assert reasons == ["direct", "secondary"]
    rounds = [e.round for e in result.log]
    assert rounds[0] == 0
    assert rounds[1] == 1


def test_strict_mode_unreachable_consumer() -> None:
    # Basal 1 supports a consumer cycle 2 <-> 3.
    G = nx.DiGraph()
    for n in [1, 2, 3]:
        G.add_node(n, name=f"sp{n}")
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(3, 2)
    result = run_extinction(G, [1], strict=True)
    # 1 removed directly; 2 and 3 still consume each other but are unreachable
    # from any surviving basal species, so strict mode removes them.
    assert 1 in result.removed_species
    assert 2 in result.removed_species
    assert 3 in result.removed_species


def test_real_dataset_loads() -> None:
    from src.data_loader import get_annotated_graph
    from src.metrics import compute_network_metrics

    G = get_annotated_graph()
    assert G.number_of_nodes() > 0
    assert G.number_of_edges() > 0
    metrics = compute_network_metrics(G)
    assert metrics["n_nodes"] == G.number_of_nodes()
    assert metrics["n_edges"] == G.number_of_edges()
