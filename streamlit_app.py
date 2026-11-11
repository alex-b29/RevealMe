import random

import streamlit as st
from PIL import Image, ImageDraw

st.set_page_config(
    page_title="Surprise d'anniversaire",
    page_icon="🎉",
    layout="centered",
)

st.markdown(
    """
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
    """,
    unsafe_allow_html=True,
)

QUESTIONS = [
    {"question": "2 + 2 = ?", "answer": "4"},
    {"question": "5 + 3 = ?", "answer": "8"},
    {"question": "7 + 1 = ?", "answer": "8"},
    {"question": "9 + 6 = ?", "answer": "15"},
    {"question": "11 + 8 = ?", "answer": "19"},
]

TOTAL_CELLS = 100
GRID_COLS = 10
GRID_ROWS = 10


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


if "started" not in st.session_state:
    reset_game()

st.markdown("<div class='big-title'>Mathilde</div>", unsafe_allow_html=True)
st.markdown("<div class='big-title'>🎉 25 ans 🎉</div>", unsafe_allow_html=True)

if not st.session_state.started:
    st.image(get_image_for_step(st.session_state.revealed_cells), width="stretch")
    st.write("")
    if st.button("Démarrer la surprise"):
        st.session_state.started = True
        st.rerun()
    st.stop()

if st.session_state.completed:
    st.balloons()
    st.image(get_image_for_step(set(range(TOTAL_CELLS))), width="stretch")
    st.markdown("## 🎂 Bon anniversaire, Mathilde ! Connecte toi sur url.com pour récupérer ton cadeau")
    if st.button("Rejouer"):
        reset_game()
        st.rerun()
    st.stop()

current = QUESTIONS[st.session_state.current_index]

st.image(get_image_for_step(st.session_state.revealed_cells), width="stretch")

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
            st.success("Bonne réponse ! La surprise se dévoile un peu plus...")
            st.rerun()
    else:
        st.warning("Presque ! Essaie encore.")
