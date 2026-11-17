import streamlit as st

from app.auth import authenticate_user
from app.game import render_game_page
from app.styles import inject_styles


def render_login_page() -> None:
    st.markdown("<div class='subtitle'>Connecte-toi pour accéder au jeu</div>", unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Nom d’utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")

    if submitted:
        is_authenticated, is_main_user = authenticate_user(username, password)

        if is_authenticated:
            st.session_state.authenticated = True
            st.session_state.is_main_user = is_main_user
            st.rerun()
        else:
            st.error("Identifiants incorrects. Veuillez réessayer.")


st.set_page_config(
    page_title="Surprise d'anniversaire",
    page_icon="🎉",
    layout="centered",
)

inject_styles()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "is_main_user" not in st.session_state:
    st.session_state.is_main_user = False

if not st.session_state.authenticated:
    render_login_page()
    st.stop()

render_game_page(is_main_user=st.session_state.is_main_user)
