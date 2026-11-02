"""RivetLab — Ecosystem Experiments page."""

from __future__ import annotations

import streamlit as st

from src.data_loader import get_annotated_graph
from src.experiments import run_random_removal, run_targeted_removal
from src.plotting import plot_remaining_edges, plot_survival_curves
from src.theme import footer, info_box, set_page_config, sidebar_header

set_page_config("Ecosystem Experiments")
sidebar_header()

st.header("🧪 Ecosystem Experiments")
info_box(
    "Compare three removal strategies: random removal (mean ± σ over multiple seeded trials), "
    "adaptive degree-based removal, and adaptive betweenness-based removal. "
    "R50 is the fraction of species directly removed when survival first falls to 50%."
)

G = get_annotated_graph()

st.sidebar.subheader("Experiment settings")
n_trials = st.sidebar.slider("Random trials", 3, 50, 10)
seed = st.sidebar.number_input("Random seed", value=42, step=1)
max_removals = st.sidebar.slider(
    "Max direct removals (%)", 10, 100, 100, step=10
)
max_removals_abs = int(max_removals / 100 * G.number_of_nodes())

run_clicked = st.sidebar.button("Run experiments", type="primary")

if run_clicked:
    with st.spinner("Running experiments..."):
        random_result = run_random_removal(
            G, n_trials=n_trials, seed=int(seed), max_removals=max_removals_abs
        )
        degree_result = run_targeted_removal(
            G, ranking="degree", adaptive=True, max_removals=max_removals_abs
        )
        betweenness_result = run_targeted_removal(
            G, ranking="betweenness", adaptive=True, max_removals=max_removals_abs
        )

    st.session_state["random_result"] = random_result
    st.session_state["degree_result"] = degree_result
    st.session_state["betweenness_result"] = betweenness_result

if "random_result" in st.session_state:
    random_result = st.session_state["random_result"]
    degree_result = st.session_state["degree_result"]
    betweenness_result = st.session_state["betweenness_result"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Random R50", f"{random_result['mean_r50']:.3f}" if random_result["mean_r50"] else "n/a")
    c2.metric("Degree R50", f"{degree_result.r50:.3f}" if degree_result.r50 else "n/a")
    c3.metric("Betweenness R50", f"{betweenness_result.r50:.3f}" if betweenness_result.r50 else "n/a")

    fig_survival = plot_survival_curves(
        random_result["df"], degree_result, betweenness_result
    )
    st.plotly_chart(fig_survival, width='stretch')

    fig_edges = plot_remaining_edges(
        [degree_result, betweenness_result],
        ["Degree (adaptive)", "Betweenness (adaptive)"],
    )
    st.plotly_chart(fig_edges, width='stretch')

    st.subheader("Most damaging species (degree-based adaptive order)")
    damaging = degree_result.removal_sequence[:10]
    names = [G.nodes[n].get("name", str(n)) for n in damaging]
    st.write(
        pd.DataFrame({"Rank": range(1, len(names) + 1), "Species": names})
    )
else:
    st.info("Click **Run experiments** in the sidebar to generate comparison charts.")

footer()
