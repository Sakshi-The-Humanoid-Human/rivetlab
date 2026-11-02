"""Graph-theoretic metrics for ecological food webs."""

from __future__ import annotations

from typing import Any

import networkx as nx
import pandas as pd


def compute_node_metrics(G: nx.DiGraph) -> pd.DataFrame:
    """Return a DataFrame of per-species metrics."""
    if G.number_of_nodes() == 0:
        return pd.DataFrame()

    records = []
    degree_centrality = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)

    for n in G.nodes():
        attrs = G.nodes[n]
        records.append(
            {
                "node_id": n,
                "name": attrs.get("name", str(n)),
                "group": attrs.get("group", "unknown"),
                "trophic_group": attrs.get("trophic_group", "unknown"),
                "trophic_level": attrs.get("trophic_level", 1.0),
                "in_degree": attrs.get("in_degree", G.in_degree(n)),
                "out_degree": attrs.get("out_degree", G.out_degree(n)),
                "degree": attrs.get("degree", G.degree(n)),
                "degree_centrality": degree_centrality.get(n, 0.0),
                "betweenness_centrality": betweenness.get(n, 0.0),
                "closeness_centrality": closeness.get(n, 0.0),
                "generality": attrs.get("generality", G.in_degree(n)),
                "vulnerability": attrs.get("vulnerability", G.out_degree(n)),
            }
        )
    df = pd.DataFrame(records)
    return df


def compute_network_metrics(G: nx.DiGraph) -> dict[str, Any]:
    """Return a dictionary of whole-network statistics."""
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    density = nx.density(G) if n_nodes > 1 else 0.0
    weak_components = list(nx.weakly_connected_components(G))
    largest_weak = max(weak_components, key=len) if weak_components else set()

    in_degrees = [d for _, d in G.in_degree()]
    out_degrees = [d for _, d in G.out_degree()]
    basal = sum(1 for _, d in G.in_degree() if d == 0)
    top = sum(1 for _, d in G.out_degree() if d == 0)
    intermediate = n_nodes - basal - top

    return {
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "density": round(density, 4),
        "n_weak_components": len(weak_components),
        "largest_weak_component": len(largest_weak),
        "avg_in_degree": round(sum(in_degrees) / n_nodes, 2) if n_nodes else 0.0,
        "avg_out_degree": round(sum(out_degrees) / n_nodes, 2) if n_nodes else 0.0,
        "max_in_degree": max(in_degrees) if in_degrees else 0,
        "max_out_degree": max(out_degrees) if out_degrees else 0,
        "basal_species": basal,
        "top_species": top,
        "intermediate_species": intermediate,
    }


def get_degree_distribution(G: nx.DiGraph) -> pd.DataFrame:
    """Return degree distribution counts."""
    in_deg = dict(G.in_degree())
    out_deg = dict(G.out_degree())
    max_in = max(in_deg.values()) if in_deg else 0
    max_out = max(out_deg.values()) if out_deg else 0
    records = []
    for k in range(max(max_in, max_out) + 1):
        records.append(
            {
                "degree": k,
                "in_degree_count": sum(1 for v in in_deg.values() if v == k),
                "out_degree_count": sum(1 for v in out_deg.values() if v == k),
            }
        )
    return pd.DataFrame(records)
