"""RivetLab — Explore Food Web page."""

from __future__ import annotations

import streamlit as st

from src.data_loader import get_annotated_graph
from src.metrics import compute_node_metrics
from src.plotting import build_food_web_figure
from src.theme import footer, info_box, set_page_config, sidebar_header

set_page_config("Explore Food Web")
sidebar_header()

st.header("🔬 Explore the food web")
info_box(
    "Edges point from <b>resource → consumer</b>. "
    "Basal species are green, intermediates are teal, and top species are red."
)

G = get_annotated_graph()
metrics_df = compute_node_metrics(G)

# Sidebar controls
st.sidebar.subheader("Visualization controls")
node_size_metric = st.sidebar.selectbox(
    "Node size metric",
    options=["degree", "in_degree", "out_degree", "betweenness_centrality"],
    index=0,
)

trophic_filter = st.sidebar.multiselect(
    "Filter by trophic group",
    options=["basal", "intermediate", "top"],
    default=["basal", "intermediate", "top"],
)

min_degree = st.sidebar.slider("Minimum total degree", 0, int(metrics_df["degree"].max()), 0)

# Filter graph
selected_nodes = set(G.nodes())
if trophic_filter:
    selected_nodes &= {
        n for n in G.nodes() if G.nodes[n].get("trophic_group") in trophic_filter
    }
selected_nodes &= {n for n in G.nodes() if G.degree(n) >= min_degree}
subgraph = G.subgraph(selected_nodes).copy()

# Search and highlight
st.sidebar.subheader("Species search")
name_to_id = {data["name"]: n for n, data in G.nodes(data=True)}
search_name = st.sidebar.selectbox(
    "Select a species",
    options=["None"] + sorted(name_to_id.keys()),
    index=0,
)

highlight: set[int] = set()
if search_name != "None":
    selected_id = name_to_id[search_name]
    highlight = {selected_id}
    highlight |= set(G.predecessors(selected_id))
    highlight |= set(G.successors(selected_id))
    st.sidebar.write(f"Selected: **{search_name}** (ID {selected_id})")
    st.sidebar.write(
        f"Resources: {len(list(G.predecessors(selected_id)))} | "
        f"Consumers: {len(list(G.successors(selected_id)))}"
    )

# Layout caching
@st.cache_data(show_spinner=False)
def get_layout(_G: object) -> dict:
    # Import here to avoid heavy top-level imports on cache
    from src.plotting import _trophic_layout
    return _trophic_layout(_G)


layout = get_layout(G)
fig = build_food_web_figure(subgraph, layout=layout, highlight=highlight, node_size_metric=node_size_metric)
st.plotly_chart(fig, width='stretch')

# Metrics table
with st.expander("Species metrics", expanded=False):
    st.dataframe(
        metrics_df.sort_values("degree", ascending=False),
        width='stretch',
        column_config={
            "node_id": "ID",
            "name": "Species",
            "trophic_group": "Trophic group",
            "trophic_level": st.column_config.NumberColumn("Trophic level", format="%.2f"),
            "degree_centrality": st.column_config.NumberColumn("Degree centrality", format="%.3f"),
            "betweenness_centrality": st.column_config.NumberColumn("Betweenness", format="%.3f"),
        },
    )

footer()
