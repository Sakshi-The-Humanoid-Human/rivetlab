"""RivetLab — Home / Overview page."""

from __future__ import annotations

import streamlit as st

from src.data_loader import get_annotated_graph, load_dataset_info
from src.metrics import compute_network_metrics
from src.theme import footer, info_box, set_page_config, sidebar_header, warning_box

set_page_config("RivetLab — Home")
sidebar_header()

st.markdown(
    """
    <h1 style="color:#2DD4BF; margin-bottom:0.2rem;">🌿 RivetLab</h1>
    <h3 style="color:#C5C6C7; margin-top:0;">Interactive food-web extinction simulator</h3>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    RivetLab lets you explore how removing species from an ecological food web can
    trigger cascading changes in network structure. It is inspired by the
    **Rivet Popper Hypothesis**: just as removing rivets one by one can eventually
    cause an airplane wing to fail, species losses can erode the stability of an
    ecosystem.
    """
)

warning_box(
    "This is a <b>topological simulation</b> based on recorded feeding relationships. "
    "It is intended for exploration and education, not as a validated prediction of "
    "real population dynamics or extinction risk."
)

# Load data
try:
    G = get_annotated_graph()
    info = load_dataset_info()
    metrics = compute_network_metrics(G)

    st.subheader("Dataset snapshot")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Species", metrics["n_nodes"])
    c2.metric("Interactions", metrics["n_edges"])
    c3.metric("Network density", f"{metrics['density']:.3f}")
    c4.metric("Basal species", metrics["basal_species"])

    info_box(
        f"Dataset: <b>{info.get('dataset_title', 'Unknown')}</b><br>"
        f"Reference: {info.get('scientific_reference', 'n/a')}<br>"
        f"Source: <a href='{info.get('dataset_source_url', 'https://mangal.io')}' style='color:#2DD4BF;'>mangal.io</a>"
    )

    st.subheader("How to use this app")
    st.markdown(
        """
        1. **Explore Food Web** — Inspect the directed food web, search for species,
           and highlight neighbours.
        2. **Extinction Simulator** — Remove species manually or via targeted strategies
           and watch cascading secondary extinctions unfold.
        3. **Ecosystem Experiments** — Compare random, degree-based, and betweenness-based
           removal using adaptive rankings and reproducible seeds.
        4. **Graph Analytics** — Browse centrality rankings, degree distributions, and
           generality vs. vulnerability.
        5. **Methodology** — Read about the dataset, graph construction, assumptions,
           and limitations.
        """
    )

    st.subheader("What the numbers mean")
    st.markdown(
        """
        - **Basal species** have no recorded predators or grazers in this network.
        - **Intermediate species** both consume and are consumed.
        - **Top species** have no recorded consumers.
        - Edges point from **resource → consumer**.
        - **Secondary extinction** occurs when a non-basal species loses all its
          remaining food resources.
        """
    )
except Exception as e:
    st.error(f"Failed to load dataset: {e}")
    st.stop()

footer()
