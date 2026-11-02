"""Data loading utilities for RivetLab.

Reads locally persisted Mangal food-web data and builds a NetworkX DiGraph
using the convention RESOURCE -> CONSUMER.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import networkx as nx
import pandas as pd

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
NODES_CSV = DATA_DIR / "nodes.csv"
EDGES_CSV = DATA_DIR / "edges.csv"
INFO_JSON = DATA_DIR / "dataset_info.json"


class DataLoadError(Exception):
    """Raised when required dataset files are missing or malformed."""


def load_dataset_info() -> dict[str, Any]:
    """Load dataset metadata JSON."""
    if not INFO_JSON.exists():
        raise DataLoadError(f"Dataset metadata not found: {INFO_JSON}")
    with INFO_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_graph() -> nx.DiGraph:
    """Load nodes and edges CSVs and return a NetworkX DiGraph.

    Edge convention in the saved files is assumed to be RESOURCE -> CONSUMER.
    Node attributes are preserved; edge attributes are preserved.
    """
    if not NODES_CSV.exists() or not EDGES_CSV.exists():
        raise DataLoadError(
            f"Required dataset files missing. Expected {NODES_CSV} and {EDGES_CSV}."
        )

    nodes = pd.read_csv(NODES_CSV)
    edges = pd.read_csv(EDGES_CSV)

    # Standardize column names
    nodes.columns = [c.strip().lower() for c in nodes.columns]
    edges.columns = [c.strip().lower() for c in edges.columns]

    # Required columns
    if "node_id" not in nodes.columns:
        if "id" in nodes.columns:
            nodes = nodes.rename(columns={"id": "node_id"})
        else:
            raise DataLoadError("nodes.csv must contain a 'node_id' or 'id' column.")

    for required in ("from", "to"):
        if required not in edges.columns:
            raise DataLoadError(f"edges.csv must contain '{required}' column.")

    G = nx.DiGraph()

    # Add nodes with attributes
    id_col = "node_id"
    for _, row in nodes.iterrows():
        node_id = row[id_col]
        if pd.isna(node_id):
            continue
        node_id = int(node_id)
        attrs = {
            k: v for k, v in row.items() if k != id_col and not pd.isna(v)
        }
        # Ensure common attributes exist for downstream use
        attrs.setdefault("name", str(node_id))
        attrs.setdefault("group", "unknown")
        G.add_node(node_id, **attrs)

    # Add edges with attributes (RESOURCE -> CONSUMER)
    for _, row in edges.iterrows():
        source = row["from"]
        target = row["to"]
        if pd.isna(source) or pd.isna(target):
            continue
        source = int(source)
        target = int(target)
        if source not in G or target not in G:
            continue
        attrs = {k: v for k, v in row.items() if k not in ("from", "to") and not pd.isna(v)}
        if G.has_edge(source, target):
            # Merge duplicate edges: keep first, increment a weight counter
            G[source][target]["weight"] = G[source][target].get("weight", 1) + 1
        else:
            G.add_edge(source, target, **attrs)

    logger.info(
        "Loaded graph: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges()
    )
    return G


def annotate_graph(G: nx.DiGraph) -> nx.DiGraph:
    """Add derived attributes used across the application.

    Adds in_degree, out_degree, degree, trophic_level, and trophic_group.
    Returns the same graph object (modified in place).
    """
    if G.number_of_nodes() == 0:
        return G

    in_deg = dict(G.in_degree())
    out_deg = dict(G.out_degree())
    total_deg = dict(G.degree())

    # Trophic level: shortest-path distance from a basal node (in_degree == 0)
    # For non-basal nodes, use the average distance from basal nodes as a proxy.
    basal = [n for n, d in in_deg.items() if d == 0]
    trophic_levels: dict[Any, float] = {}
    for n in G.nodes():
        if in_deg[n] == 0:
            trophic_levels[n] = 1.0
        else:
            if basal:
                lengths = []
                for b in basal:
                    try:
                        length = nx.shortest_path_length(G, source=b, target=n)
                        lengths.append(length)
                    except nx.NetworkXNoPath:
                        pass
                if lengths:
                    trophic_levels[n] = 1.0 + sum(lengths) / len(lengths)
                else:
                    trophic_levels[n] = 2.0
            else:
                trophic_levels[n] = 2.0

    for n in G.nodes():
        G.nodes[n]["in_degree"] = in_deg[n]
        G.nodes[n]["out_degree"] = out_deg[n]
        G.nodes[n]["degree"] = total_deg[n]
        G.nodes[n]["trophic_level"] = round(trophic_levels.get(n, 1.0), 2)
        G.nodes[n]["generality"] = in_deg[n]
        G.nodes[n]["vulnerability"] = out_deg[n]
        G.nodes[n]["trophic_group"] = _trophic_group(in_deg[n], out_deg[n])

    return G


def _trophic_group(in_degree: int, out_degree: int) -> str:
    """Classify a node as basal, top, or intermediate."""
    if in_degree == 0 and out_degree > 0:
        return "basal"
    if in_degree > 0 and out_degree == 0:
        return "top"
    return "intermediate"


def get_annotated_graph() -> nx.DiGraph:
    """Convenience function: load and annotate the food web."""
    G = load_graph()
    return annotate_graph(G)
