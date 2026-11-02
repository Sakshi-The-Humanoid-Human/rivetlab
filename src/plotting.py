"""Plotly-based visualizations for RivetLab."""

from __future__ import annotations

from typing import Any

import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Theme colors
BG = "#0B0C10"
PAPER = "#1F2833"
TEAL = "#2DD4BF"
AMBER = "#F59E0B"
TEXT = "#C5C6C7"
GRID = "#4B5563"


def _layout_kwargs(title: str) -> dict[str, Any]:
    return dict(
        title=dict(text=title, font=dict(color=TEXT, size=18)),
        paper_bgcolor=PAPER,
        plot_bgcolor=BG,
        font=dict(color=TEXT),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
        margin=dict(l=40, r=20, t=50, b=40),
        hovermode="closest",
    )


def build_food_web_figure(
    G: nx.DiGraph,
    layout: dict[int, tuple[float, float]] | None = None,
    highlight: set[int] | None = None,
    node_size_metric: str = "degree",
) -> go.Figure:
    """Build an interactive Plotly directed food-web graph."""
    if G.number_of_nodes() == 0:
        fig = go.Figure()
        fig.update_layout(**_layout_kwargs("Food web (empty)"))
        return fig

    highlight = highlight or set()

    # Compute layout if not provided
    if layout is None:
        layout = _trophic_layout(G)

    # Node traces by trophic group
    group_colors = {
        "basal": "#34D399",  # green
        "intermediate": TEAL,
        "top": "#F87171",  # red
        "unknown": "#9CA3AF",
    }

    fig = go.Figure()

    # Edges
    for u, v in G.edges():
        x0, y0 = layout[u]
        x1, y1 = layout[v]
        is_highlight = u in highlight or v in highlight
        fig.add_trace(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(
                    color=AMBER if is_highlight else "#6B7280",
                    width=2.5 if is_highlight else 1.0,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    # Nodes grouped by trophic group
    nodes_by_group: dict[str, list[int]] = {}
    for n in G.nodes():
        group = G.nodes[n].get("trophic_group", "unknown")
        nodes_by_group.setdefault(group, []).append(n)

    for group, nodes in nodes_by_group.items():
        xs, ys, sizes, texts, ids = [], [], [], [], []
        for n in nodes:
            x, y = layout[n]
            xs.append(x)
            ys.append(y)
            ids.append(n)
            val = G.nodes[n].get(node_size_metric, G.degree(n))
            sizes.append(_normalize_size(val, G, node_size_metric))
            texts.append(_node_hover_text(G, n))

        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                marker=dict(
                    size=sizes,
                    color=group_colors.get(group, "#9CA3AF"),
                    line=dict(
                        color=AMBER if any(n in highlight for n in nodes) else TEXT,
                        width=2 if any(n in highlight for n in nodes) else 1,
                    ),
                ),
                text=texts,
                hovertemplate="%{text}<extra></extra>",
                name=group.capitalize(),
                showlegend=True,
            )
        )

    kwargs = _layout_kwargs("Interactive food web")
    kwargs["xaxis"] = dict(showgrid=False, zeroline=False, showticklabels=False)
    kwargs["yaxis"] = dict(showgrid=False, zeroline=False, showticklabels=False)
    kwargs["legend"] = dict(
        orientation="h",
        yanchor="bottom",
        y=-0.15,
        xanchor="center",
        x=0.5,
        font=dict(color=TEXT),
    )
    kwargs["dragmode"] = "pan"
    fig.update_layout(**kwargs)
    return fig


def _normalize_size(value: float, G: nx.DiGraph, metric: str) -> float:
    values = [G.nodes[n].get(metric, G.degree(n)) for n in G.nodes()]
    min_v, max_v = min(values), max(values)
    if max_v == min_v:
        return 18
    return 10 + 25 * (value - min_v) / (max_v - min_v)


def _node_hover_text(G: nx.DiGraph, n: int) -> str:
    attrs = G.nodes[n]
    deg_centrality = attrs.get("degree_centrality")
    if isinstance(deg_centrality, (int, float)):
        deg_centrality_text = f"{deg_centrality:.3f}"
    else:
        deg_centrality_text = "n/a"
    lines = [
        f"<b>{attrs.get('name', n)}</b>",
        f"Group: {attrs.get('group', 'unknown')}",
        f"Trophic group: {attrs.get('trophic_group', 'unknown')}",
        f"Trophic level: {attrs.get('trophic_level', 'n/a')}",
        f"In-degree: {G.in_degree(n)}",
        f"Out-degree: {G.out_degree(n)}",
        f"Degree centrality: {deg_centrality_text}",
    ]
    return "<br>".join(lines)


def _trophic_layout(G: nx.DiGraph) -> dict[int, tuple[float, float]]:
    """Position nodes by trophic level (vertical) and degree (horizontal spread)."""
    if G.number_of_nodes() == 0:
        return {}

    levels: dict[int, float] = {}
    for n in G.nodes():
        levels[n] = float(G.nodes[n].get("trophic_level", 1.0))

    # Group by level, sort by within-level degree for horizontal spread
    by_level: dict[int, list[int]] = {}
    for n, lvl in levels.items():
        by_level.setdefault(int(lvl), []).append(n)

    layout: dict[int, tuple[float, float]] = {}
    for lvl, nodes in by_level.items():
        nodes_sorted = sorted(nodes, key=lambda n: G.degree(n))
        n = len(nodes_sorted)
        for i, node in enumerate(nodes_sorted):
            x = (i - (n - 1) / 2) * 1.5
            y = -lvl * 2.0
            layout[node] = (x, y)
    return layout


def plot_survival_curves(
    random_df: pd.DataFrame,
    targeted_degree: Any,
    targeted_betweenness: Any,
) -> go.Figure:
    """Plot survival percentage vs removal percentage for three strategies."""
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=random_df["removal_fraction"] * 100,
            y=random_df["mean_survival_fraction"] * 100,
            mode="lines",
            name="Random (mean)",
            line=dict(color="#9CA3AF", width=2),
            hovertemplate="Removed: %{x:.1f}%<br>Survival: %{y:.1f}%<extra></extra>",
        )
    )
    if "std_survival_fraction" in random_df.columns:
        fig.add_trace(
            go.Scatter(
                x=random_df["removal_fraction"] * 100,
                y=(random_df["mean_survival_fraction"] + random_df["std_survival_fraction"]) * 100,
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=random_df["removal_fraction"] * 100,
                y=(random_df["mean_survival_fraction"] - random_df["std_survival_fraction"]) * 100,
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(156,163,175,0.2)",
                name="Random ±1σ",
                hoverinfo="skip",
            )
        )

    def add_targeted(result: Any, color: str, name: str) -> None:
        x = [s.step / max(result.initial_nodes, 1) * 100 for s in result.steps]
        y = [s.n_remaining / max(result.initial_nodes, 1) * 100 for s in result.steps]
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                name=name,
                line=dict(color=color, width=2),
                hovertemplate="Removed: %{x:.1f}%<br>Survival: %{y:.1f}%<extra></extra>",
            )
        )

    add_targeted(targeted_degree, TEAL, "Degree (adaptive)")
    add_targeted(targeted_betweenness, AMBER, "Betweenness (adaptive)")

    fig.update_layout(
        **_layout_kwargs("Species survival vs direct removal"),
        xaxis_title="Directly removed species (%)",
        yaxis_title="Surviving species (%)",
        legend=dict(x=0.02, y=0.98, bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def plot_remaining_edges(results: list[Any], names: list[str]) -> go.Figure:
    """Plot remaining edges vs removal percentage."""
    fig = go.Figure()
    colors = ["#9CA3AF", TEAL, AMBER]
    for res, name, color in zip(results, names, colors):
        x = [s.step / max(res.initial_nodes, 1) * 100 for s in res.steps]
        y = [s.n_edges for s in res.steps]
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                name=name,
                line=dict(color=color, width=2),
            )
        )
    fig.update_layout(
        **_layout_kwargs("Remaining trophic interactions"),
        xaxis_title="Directly removed species (%)",
        yaxis_title="Remaining edges",
    )
    return fig


def plot_degree_distribution(G: nx.DiGraph) -> go.Figure:
    """Plot in-degree and out-degree distributions."""
    in_deg = [d for _, d in G.in_degree()]
    out_deg = [d for _, d in G.out_degree()]

    fig = make_subplots(rows=1, cols=2, subplot_titles=("In-degree", "Out-degree"))
    fig.add_trace(
        go.Histogram(x=in_deg, marker_color=TEAL, nbinsx=max(10, len(set(in_deg)))),
        row=1, col=1,
    )
    fig.add_trace(
        go.Histogram(x=out_deg, marker_color=AMBER, nbinsx=max(10, len(set(out_deg)))),
        row=1, col=2,
    )
    fig.update_layout(
        **_layout_kwargs("Degree distributions"),
        showlegend=False,
    )
    fig.update_xaxes(title_text="Degree")
    fig.update_yaxes(title_text="Count")
    return fig


def plot_generality_vulnerability(df: pd.DataFrame) -> go.Figure:
    """Scatter plot of generality (in-degree) vs vulnerability (out-degree)."""
    fig = px.scatter(
        df,
        x="generality",
        y="vulnerability",
        color="trophic_group",
        hover_data=["name"],
        color_discrete_map={
            "basal": "#34D399",
            "intermediate": TEAL,
            "top": "#F87171",
            "unknown": "#9CA3AF",
        },
    )
    fig.update_layout(
        **_layout_kwargs("Generality vs vulnerability"),
        xaxis_title="Generality (number of resources)",
        yaxis_title="Vulnerability (number of consumers)",
        legend=dict(x=0.98, y=0.98, xanchor="right"),
    )
    return fig
