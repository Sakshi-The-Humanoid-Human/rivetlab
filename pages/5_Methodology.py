"""RivetLab — Methodology page."""

from __future__ import annotations

import json

import streamlit as st

from src.data_loader import load_dataset_info
from src.theme import footer, set_page_config, sidebar_header

set_page_config("Methodology")
sidebar_header()

st.header("📖 Methodology")

info = load_dataset_info()

st.subheader("Dataset source")
st.markdown(
    f"""
    - **Network ID:** {info.get('network_identifier')}
    - **Name:** {info.get('network_name')}
    - **Title:** {info.get('dataset_title')}
    - **Description:** {info.get('description')}
    - **Source:** [{info.get('dataset_source')}]({info.get('dataset_source_url')})
    - **API documentation:** [{info.get('api_documentation')}]({info.get('api_documentation')})
    - **Reference:** {info.get('scientific_reference')}
    - **DOI:** {info.get('doi')}
    - **Retrieval date:** {info.get('retrieval_date')}
    - **Species:** {info.get('n_nodes')}
    - **Interactions:** {info.get('n_edges')}
    """
)

st.subheader("Data processing")
st.markdown(
    f"""
    - Node and interaction records were downloaded from the Mangal API.
    - Trophic interaction types in the raw data include predation, herbivory, and detritivore.
    - The Mangal API records directed trophic interactions as **consumer → resource**.
      RivetLab reverses these edges so that the application convention is **resource → consumer**.
    - Data cleaning operations performed: {', '.join(info.get('data_cleaning_operations', ['none']))}.
    - The processed data are saved locally in `data/nodes.csv`, `data/edges.csv`, and
      `data/dataset_info.json`; the deployed app uses these local files and does not
      require a live API connection.
    """
)

st.subheader("Graph construction")
st.markdown(
    """
    - Each species is a node in a directed graph.
    - Each recorded feeding relationship is a directed edge from resource to consumer.
    - Node attributes include species name, taxonomic group, trophic level, and derived metrics.
    - Edge attributes include interaction type and the original direction flag from Mangal.
    """
)

st.subheader("Extinction assumptions")
st.markdown(
    """
    - **Direct removal:** the species explicitly chosen for removal.
    - **Secondary extinction:** a non-basal species with no surviving recorded resources is removed.
    - **Cascading extinction:** secondary extinctions are applied repeatedly until the network stabilises.
    - **Basal protection:** species with in-degree 0 in the original graph are never removed by the
      secondary-extinction rule, but they can be directly removed by the user.
    - **Strict mode (optional):** in addition to the rule above, any consumer that is no longer
      reachable from a surviving basal species is also removed. This can matter in cyclic food webs.
    - The original graph is never mutated; each simulation works on a copy.
    """
)

st.subheader("Graph algorithms")
st.markdown(
    """
    - **Trophic level:** estimated as 1 plus the mean shortest-path distance from the nearest basal
      species. This is a structural proxy, not a measured energetic trophic position.
    - **Centrality:** degree, betweenness, and closeness centrality are computed with NetworkX.
    - **Connected components:** weakly connected components are used because the food web is directed.
    - **Robustness (R50):** the fraction of species directly removed when the surviving species count
      first drops to 50% of the initial count.
    """
)

st.subheader("Experimental methodology")
st.markdown(
    """
    - **Random removal:** multiple independent trials with fixed random seeds; results are reported
      as mean ± standard deviation.
    - **Targeted removal:** species are removed in descending order of a centrality metric.
      Adaptive rankings recalculate the metric after every removal.
    - All experiments are reproducible given the same seed and strategy settings.
    """
)

st.subheader("Limitations")
st.markdown(
    """
    - This is a topological model. It does not account for population dynamics, interaction strengths,
      environmental variability, or species traits such as dispersal or functional redundancy.
    - The Mangal record is a snapshot of reported interactions; unobserved interactions, seasonal
      variation, and spatial structure are not represented.
    - Edge direction in the raw Havens 1992 data is marked as "unknown" in the API; RivetLab infers
      the resource → consumer direction from the interaction type (herbivory, predation, detritivore)
      and the known ecology of the taxa involved, consistent with the directed records in other
      Mangal food webs.
    - Results should not be interpreted as validated extinction predictions.
    """
)

st.subheader("References")
st.markdown(
    f"""
    - Havens, K. E. (1992). Scale and structure in natural food webs. *Science*, 257(5073), 1107-1109.
      DOI: [{info.get('doi')}](https://doi.org/{info.get('doi')})
    - Mangal API documentation: {info.get('api_documentation')}
    """
)

footer()
