"""RivetLab — Graph Analytics page."""

from __future__ import annotations

import streamlit as st

from src.data_loader import get_annotated_graph
from src.metrics import compute_network_metrics, compute_node_metrics, get_degree_distribution
from src.plotting import plot_degree_distribution, plot_generality_vulnerability
from src.theme import footer, info_box, set_page_config, sidebar_header

set_page_config("Graph Analytics")
sidebar_header()

st.header("📊 Graph Analytics")
info_box(
    "Edge convention is <b>resource → consumer</b>. In-degree therefore measures the number "
    "of recorded resources (generality), and out-degree measures the number of recorded consumers "
    "(vulnerability)."
)

G = get_annotated_graph()
metrics = compute_network_metrics(G)
df = compute_node_metrics(G)

# Network summary
st.subheader("Network summary")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Species", metrics["n_nodes"])
c2.metric("Interactions", metrics["n_edges"])
c3.metric("Density", metrics["density"])
c4.metric("Basal", metrics["basal_species"])
c5.metric("Top", metrics["top_species"])

st.write(
    f"Average in-degree: **{metrics['avg_in_degree']}** | "
    f"Average out-degree: **{metrics['avg_out_degree']}** | "
    f"Largest weak component: **{metrics['largest_weak_component']}** species | "
    f"Weak components: **{metrics['n_weak_components']}**"
)

# Rankings
st.subheader("Species rankings")
rank_metric = st.selectbox(
    "Rank by",
    options=[
        "degree",
        "betweenness_centrality",
        "closeness_centrality",
        "degree_centrality",
        "generality",
        "vulnerability",
    ],
    index=0,
)
display_df = df[[
    "name", "trophic_group", "trophic_level", "degree",
    "in_degree", "out_degree", "degree_centrality",
    "betweenness_centrality", "closeness_centrality",
    "generality", "vulnerability",
]].sort_values(rank_metric, ascending=False)

st.dataframe(display_df, width='stretch')
st.download_button(
    "Download metrics (CSV)",
    df.to_csv(index=False).encode("utf-8"),
    "species_metrics.csv",
    "text/csv",
)

# Charts
st.subheader("Degree distributions")
fig_deg = plot_degree_distribution(G)
st.plotly_chart(fig_deg, width='stretch')

st.subheader("Generality vs vulnerability")
fig_gv = plot_generality_vulnerability(df)
st.plotly_chart(fig_gv, width='stretch')

with st.expander("Degree distribution table"):
    st.dataframe(get_degree_distribution(G), width='stretch')

footer()
