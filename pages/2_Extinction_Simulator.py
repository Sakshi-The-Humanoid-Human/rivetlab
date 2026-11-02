"""RivetLab — Extinction Simulator page."""

from __future__ import annotations

import random

import networkx as nx
import pandas as pd
import streamlit as st

from src.data_loader import get_annotated_graph
from src.metrics import compute_network_metrics
from src.plotting import build_food_web_figure
from src.simulation import remove_single_species, reset_simulation, run_extinction
from src.theme import footer, set_page_config, sidebar_header, warning_box

set_page_config("Extinction Simulator")
sidebar_header()

st.header("⚠️ Extinction Simulator")
warning_box(
    "Removing a species here simulates a structural loss in the food web. "
    "Secondary extinctions are triggered when a non-basal species has no surviving "
    "recorded resources. This is a simplified model, not a biological forecast."
)

# Initialize session state
if "sim_graph" not in st.session_state:
    st.session_state.sim_graph = get_annotated_graph()
    st.session_state.removed = set()
    st.session_state.log = []

G = st.session_state.sim_graph
name_to_id = {data["name"]: n for n, data in G.nodes(data=True)}
names = sorted(name_to_id.keys())

# Controls
st.sidebar.subheader("Removal controls")
selected_name = st.sidebar.selectbox("Select a species to remove", options=names)
selected_id = name_to_id[selected_name]

c1, c2 = st.sidebar.columns(2)
with c1:
    remove_clicked = st.button("Remove selected", width='stretch')
    random_clicked = st.button("Remove random", width='stretch')
    high_degree_clicked = st.button("Highest degree", width='stretch')
with c2:
    high_betweenness_clicked = st.button("Highest betweenness", width='stretch')
    reset_clicked = st.button("Reset", width='stretch', type="primary")

strict_mode = st.sidebar.checkbox("Strict mode (unreachable consumers also extinct)", value=False)

if reset_clicked:
    st.session_state.sim_graph = get_annotated_graph()
    st.session_state.removed = set()
    st.session_state.log = []
    st.rerun()

# Determine which species to remove
removals: list[int] = []
if remove_clicked:
    removals = [selected_id]
elif random_clicked:
    remaining = [n for n in G.nodes() if n not in st.session_state.removed]
    if remaining:
        removals = [random.choice(remaining)]
elif high_degree_clicked:
    remaining = {n: d for n, d in G.degree() if n not in st.session_state.removed}
    if remaining:
        removals = [max(remaining, key=remaining.get)]
elif high_betweenness_clicked:
    sub = G.subgraph(set(G.nodes()) - st.session_state.removed)
    if sub.number_of_nodes() > 0:
        scores = nx.betweenness_centrality(sub)
        removals = [max(scores, key=scores.get)]

if removals:
    result = run_extinction(G, removals, strict=strict_mode)
    for event in result.log:
        st.session_state.removed.add(event.species_id)
        st.session_state.log.append(event)

# Build current graph view
remaining_nodes = set(G.nodes()) - st.session_state.removed
current_graph = G.subgraph(remaining_nodes).copy()

# Metrics
c1, c2, c3, c4 = st.columns(4)
metrics = compute_network_metrics(current_graph)
c1.metric("Surviving species", metrics["n_nodes"])
c2.metric("Remaining edges", metrics["n_edges"])
c3.metric("Density", f"{metrics['density']:.3f}")
c4.metric("Weak components", metrics["n_weak_components"])

# Visualization
from src.plotting import _trophic_layout

layout = _trophic_layout(G)
fig = build_food_web_figure(
    current_graph, layout=layout, node_size_metric="degree"
)
st.plotly_chart(fig, width='stretch')

# Extinction log
st.subheader("Extinction sequence")
if st.session_state.log:
    log_df = pd.DataFrame(
        [
            {
                "Round": e.round,
                "Species": e.species_name,
                "Reason": e.reason,
                "ID": e.species_id,
            }
            for e in st.session_state.log
        ]
    )
    st.dataframe(log_df, width='stretch')
    st.download_button(
        "Download extinction log (CSV)",
        log_df.to_csv(index=False).encode("utf-8"),
        "extinction_log.csv",
        "text/csv",
    )
else:
    st.info("No species have been removed yet.")

footer()
