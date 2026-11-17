"""Game logic and rendering for the reveal challenge."""

import random

import streamlit as st
from PIL import Image, ImageDraw

TOTAL_CELLS = 100
GRID_COLS = 10
GRID_ROWS = 10
QUESTIONS = [
    {"question": "2 + 2 = ?", "answer": "4"},
    {"question": "5 + 3 = ?", "answer": "8"},
    {"question": "7 + 1 = ?", "answer": "8"},
    {"question": "9 + 6 = ?", "answer": "15"},
    {"question": "11 + 8 = ?", "answer": "19"},
]


def normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def build_reveal_plan():
    all_cells = set(range(TOTAL_CELLS))
    remaining = set(all_cells)
    reveal_plan = []

    for index in range(len(QUESTIONS)):
        reveal_count = TOTAL_CELLS // len(QUESTIONS)
        if index == len(QUESTIONS) - 1:
            reveal_count = len(remaining)

        chosen = set(random.sample(sorted(remaining), reveal_count))
        reveal_plan.append(chosen)
        remaining -= chosen

    return reveal_plan


def get_image_for_step(revealed_cells: set[int]) -> Image.Image:
    image = Image.open("ski.png").convert("RGB")
    image = image.resize((900, 700), Image.Resampling.LANCZOS)

    width, height = image.size
    tile_w = width // GRID_COLS
    tile_h = height // GRID_ROWS

    display = image.copy()
    draw = ImageDraw.Draw(display)

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell_id = row * GRID_COLS + col
            x0 = col * tile_w
            y0 = row * tile_h
            x1 = x0 + tile_w
            y1 = y0 + tile_h

            if cell_id not in revealed_cells:
                draw.rectangle((x0, y0, x1 - 3, y1 - 3), fill=(18, 22, 34))
                draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=(112, 128, 170), width=2)
                draw.line((x0, y0, x1, y0), fill=(147, 162, 212), width=2)
                draw.line((x0, y0, x0, y1), fill=(147, 162, 212), width=2)

    return display


def reset_game():
    st.session_state.started = False
    st.session_state.current_index = 0
    st.session_state.completed = False
    st.session_state.answer = ""
    st.session_state.revealed_cells = set()
    st.session_state.reveal_plan = build_reveal_plan()


def render_game_page(is_main_user: bool = True):
    if "started" not in st.session_state:
        reset_game()

    st.markdown("<div class='big-title'>Mathilde</div>", unsafe_allow_html=True)
    st.markdown("<div class='big-title'>🎉 25 ans 🎉</div>", unsafe_allow_html=True)

    if not is_main_user:
        st.info("Mode administration: vous consultez la progression, sans pouvoir saisir de réponse.")

    if not st.session_state.started:
        st.image(get_image_for_step(st.session_state.revealed_cells), width="stretch")
        st.write("")

        if is_main_user:
            if st.button("Démarrer le jeu"):
                st.session_state.started = True
                st.rerun()
        else:
            st.caption("Le jeu n'est pas encore démarré.")

        st.stop()

    if st.session_state.completed:
        st.balloons()
        st.image(get_image_for_step(set(range(TOTAL_CELLS))), width="stretch")

        if is_main_user:
            st.markdown("## 🎂 Bon anniversaire, Mathilde ! Connecte toi sur url.com pour récupérer ton cadeau")
            if st.button("Rejouer"):
                reset_game()
                st.rerun()
        else:
            st.markdown("## 🎂 Le jeu est terminé")

        st.stop()

    current = QUESTIONS[st.session_state.current_index]

    st.image(get_image_for_step(st.session_state.revealed_cells), width="stretch")

    if not is_main_user:
        st.progress((st.session_state.current_index) / len(QUESTIONS))
        st.caption(f"Progression : énigme {st.session_state.current_index + 1} sur {len(QUESTIONS)}")
        st.stop()

    with st.form("quiz_form"):
        st.subheader(f"Énigme {st.session_state.current_index + 1} / {len(QUESTIONS)}")
        st.write(current["question"])
        answer = st.text_input("Ta réponse", key="answer")
        submitted = st.form_submit_button("Valider")

    if submitted:
        if normalize(answer) == normalize(current["answer"]):
            new_cells = st.session_state.reveal_plan[st.session_state.current_index]
            st.session_state.revealed_cells |= new_cells

            if st.session_state.current_index == len(QUESTIONS) - 1:
                st.session_state.completed = True
                st.success("Bonne réponse ! C'est la dernière énigme !")
                st.rerun()
            else:
                st.session_state.current_index += 1
                st.success("Bonne réponse !")
                st.rerun()
        else:
            st.warning("Presque ! Essaie encore.")
