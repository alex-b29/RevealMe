"""Game logic and rendering for the reveal challenge."""

import io
import random
import urllib.request

import streamlit as st
from PIL import Image, ImageDraw

QUESTIONS = [
    {"question": "2 + 2 = ?", "answer": "4", "giver": "Alex"},
    {"question": "5 + 3 = ?", "answer": "8", "giver": "Camille"},
    {"question": "7 + 1 = ?", "answer": "8", "giver": "Sarah"},
    {"question": "9 + 6 = ?", "answer": "15", "giver": "Lucas"},
    {"question": "11 + 8 = ?", "answer": "19", "giver": "Chloé"},
]

PORTRAIT_URLS = [
    "https://picsum.photos/seed/alex/300/300",
    "https://picsum.photos/seed/camille/300/300",
    "https://picsum.photos/seed/sarah/300/300",
    "https://picsum.photos/seed/lucas/300/300",
    "https://picsum.photos/seed/chloe/300/300",
]


def normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


@st.cache_data(show_spinner=False)
def download_portrait(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read()


def load_portrait(url: str) -> Image.Image:
    try:
        image_bytes = download_portrait(url)
        return Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return Image.new("RGB", (300, 300), (255, 215, 232))


def build_reveal_plan() -> list[int]:
    return random.sample(range(TOTAL_CELLS), len(QUESTIONS))


def get_mosaic_dimensions(item_count: int) -> tuple[int, int]:
    if item_count <= 0:
        return 1, 1

    candidates: list[tuple[int, int, int, int]] = []

    for cols in range(1, item_count + 1):
        for rows in range(1, cols + 1):
            if item_count > 3 and rows == 1:
                continue

            cell_count = cols * rows
            if cell_count < item_count:
                continue

            extra = cell_count - item_count
            difference = cols - rows
            candidates.append((extra, difference, cols, rows))

    _, _, cols, rows = min(candidates)
    return cols, rows


GRID_COLS, GRID_ROWS = get_mosaic_dimensions(len(QUESTIONS))
TOTAL_CELLS = GRID_COLS * GRID_ROWS


def get_mosaic_image(revealed_portraits: dict[int, dict]) -> Image.Image:
    canvas = Image.new("RGB", (900, 675), (255, 244, 179))
    tile_w = canvas.width // GRID_COLS
    tile_h = canvas.height // GRID_ROWS
    draw = ImageDraw.Draw(canvas)

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell_id = row * GRID_COLS + col
            x0 = col * tile_w
            y0 = row * tile_h
            x1 = x0 + tile_w
            y1 = y0 + tile_h

            if cell_id not in revealed_portraits:
                draw.rectangle(
                    (x0 + 3, y0 + 3, x1 - 3, y1 - 3),
                    fill=(18, 22, 34),
                )
                draw.rectangle(
                    (x0 + 3, y0 + 3, x1 - 3, y1 - 3),
                    outline=(112, 128, 170),
                    width=3,
                )
                continue

            entry = revealed_portraits[cell_id]
            portrait = load_portrait(entry["portrait"])
            portrait = portrait.resize((tile_w - 6, tile_h - 6), Image.Resampling.LANCZOS)
            canvas.paste(portrait, (x0 + 3, y0 + 3))

    return canvas


def reset_game() -> None:
    st.session_state.started = False
    st.session_state.current_index = 0
    st.session_state.completed = False
    st.session_state.answer = ""
    st.session_state.revealed_portraits = {}
    st.session_state.reveal_plan = build_reveal_plan()


def render_game_page(is_main_user: bool = True) -> None:
    if "started" not in st.session_state:
        reset_game()

    st.markdown("<div class='big-title'>Mathilde</div>", unsafe_allow_html=True)
    st.markdown("<div class='big-title'>🎉 25 ans 🎉</div>", unsafe_allow_html=True)

    if not is_main_user:
        st.info("Mode administration : vous consultez la progression, sans pouvoir saisir de réponse.")

    if not st.session_state.started:
        st.image(get_mosaic_image({}), width="stretch")

        if is_main_user:
            if st.button("Démarrer le jeu"):
                st.session_state.started = True
                st.rerun()
        else:
            st.caption("Le jeu n'est pas encore démarré.")

        st.stop()

    st.image(
        get_mosaic_image(st.session_state.revealed_portraits),
        width="stretch",
    )

    if st.session_state.completed:
        st.balloons()

        if is_main_user:
            st.markdown("## 🎂 Bon anniversaire, Mathilde !")
            if st.button("Rejouer"):
                reset_game()
                st.rerun()
        else:
            st.markdown("## 🎂 Le jeu est terminé")

        st.stop()

    if not is_main_user:
        progress = st.session_state.current_index / len(QUESTIONS)
        st.progress(progress)
        st.caption(
            f"Progression : {st.session_state.current_index} / {len(QUESTIONS)} énigmes validées"
        )
        st.stop()

    current = QUESTIONS[st.session_state.current_index]

    with st.form("quiz_form"):
        st.subheader(f"Énigme {st.session_state.current_index + 1} / {len(QUESTIONS)}")
        st.write(current["question"])
        answer = st.text_input("Ta réponse", key="answer")
        submitted = st.form_submit_button("Valider")

    if submitted:
        if normalize(answer) == normalize(current["answer"]):
            mosaic_cell = st.session_state.reveal_plan[st.session_state.current_index]
            st.session_state.revealed_portraits[mosaic_cell] = {
                "giver": current["giver"],
                "portrait": PORTRAIT_URLS[st.session_state.current_index],
            }

            st.session_state.current_index += 1

            if st.session_state.current_index >= len(QUESTIONS):
                st.session_state.completed = True

            st.success("Bonne réponse ! Une case vient de se révéler.")
            st.rerun()
        else:
            st.warning("Presque ! Essaie encore.")
