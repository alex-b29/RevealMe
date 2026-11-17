"""Shared styling helpers for the Streamlit app."""


APP_CSS = """
<style>
    .stApp {
        background: linear-gradient(135deg, #fff4b3 0%, #ffd7e8 45%, #dfeeff 100%);
        color-scheme: light;
    }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #fff4b3 0%, #ffd7e8 45%, #dfeeff 100%);
        color-scheme: light;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .big-title {
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        color: #ff4d8d;
    }
    .subtitle {
        text-align: center;
        font-size: 1.1rem;
        color: #5c2a9d;
        margin-bottom: 1rem;
    }
    .stMarkdown, .stTextInput, .stForm, .stSubheader, .stSuccess, .stWarning {
        color: #000000 !important;
    }
    .stTextInput label {
        color: #000000 !important;
    }
    .stForm p {
        color: #000000 !important;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #fff9d6 0%, #ffd7e8 100%);
        color: #000000 !important;
        border: 2px solid #ff7ab6;
        border-radius: 999px;
        font-weight: 700;
        padding: 0.7rem 1.5rem;
        box-shadow: 0 6px 18px rgba(255, 122, 182, 0.25);
        -webkit-appearance: none;
        appearance: none;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #ffe9a8 0%, #ffc2dd 100%);
        border-color: #ff5ca8;
    }
</style>
"""


def inject_styles() -> None:
    import streamlit as st

    st.markdown(APP_CSS, unsafe_allow_html=True)
