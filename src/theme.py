"""Common UI helpers and styling for RivetLab."""

from __future__ import annotations

import streamlit as st


def set_page_config(title: str, icon: str = "🌿") -> None:
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )


def sidebar_header() -> None:
    """Render the common sidebar title and navigation hint."""
    st.sidebar.markdown(
        """
        <h1 style="color:#2DD4BF; margin-bottom:0;">🌿 RivetLab</h1>
        <p style="color:#9CA3AF; font-size:0.85rem;">
            Ecological food-web extinction simulator
        </p>
        <hr style="border-color:#4B5563; margin:1rem 0;">
        """,
        unsafe_allow_html=True,
    )


def footer() -> None:
    """Render a small footer."""
    st.markdown(
        """
        <hr style="border-color:#4B5563; margin-top:2rem;">
        <p style="color:#9CA3AF; font-size:0.8rem; text-align:center;">
            RivetLab · Topological simulation for educational purposes · Not a validated ecological prediction
        </p>
        """,
        unsafe_allow_html=True,
    )


def info_box(text: str) -> None:
    """Render a styled info callout."""
    st.markdown(
        f"""
        <div style="background-color:#1F2833; border-left:4px solid #2DD4BF;
                    padding:0.75rem 1rem; margin:1rem 0; border-radius:4px;">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def warning_box(text: str) -> None:
    """Render a styled warning callout."""
    st.markdown(
        f"""
        <div style="background-color:#1F2833; border-left:4px solid #F59E0B;
                    padding:0.75rem 1rem; margin:1rem 0; border-radius:4px;">
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )
