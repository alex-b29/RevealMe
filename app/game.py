import hashlib
import random
from io import BytesIO

import streamlit as st
from PIL import Image, ImageDraw, ImageOps

from app.storage import (
    fetch_game_config,
    fetch_image_from_storage,
    save_game_config_to_storage,
)


def normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def get_participant_color(name: str) -> tuple[int, int, int]:
    digest = hashlib.sha256(normalize(name).encode("utf-8")).digest()
    red = 110 + digest[0] % 126
    green = 110 + digest[1] % 126
    blue = 110 + digest[2] % 126
    return red, green, blue


def load_game_config() -> dict:
    remote_config = fetch_game_config()
    if remote_config is None:
        raise RuntimeError("game_config.json est introuvable dans le bucket S3")
    return remote_config


def save_game_config(game_config: dict) -> None:
    if not save_game_config_to_storage(game_config):
        raise RuntimeError("Impossible de sauvegarder game_config.json dans le bucket S3")


GAME_CONFIG = load_game_config()
ORDERED_PARTICIPANTS = GAME_CONFIG["ordered_participants"]


def build_mosaic_positions() -> list[int]:
    return random.sample(range(TOTAL_CELLS), len(ORDERED_PARTICIPANTS))


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


GRID_COLS, GRID_ROWS = get_mosaic_dimensions(len(ORDERED_PARTICIPANTS))
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
            portrait = entry.get("portrait")
            if portrait is not None:
                portrait = ImageOps.fit(
                    portrait,
                    (tile_w - 6, tile_h - 6),
                    method=Image.Resampling.LANCZOS,
                )
                canvas.paste(portrait, (x0 + 3, y0 + 3))
            else:
                draw.rectangle(
                    (x0 + 3, y0 + 3, x1 - 3, y1 - 3),
                    fill=get_participant_color(entry["giver"]),
                )

    return canvas


def reset_game() -> None:
    game_config = load_game_config()
    game_config["progression"] = {
        "started": False,
        "current_index": 0,
        "mosaic_positions": build_mosaic_positions(),
    }
    save_game_config(game_config)
    apply_progression(game_config["progression"])


def apply_progression(progression: dict) -> None:
    mosaic_positions = progression.get("mosaic_positions", [])
    if len(mosaic_positions) != len(ORDERED_PARTICIPANTS):
        mosaic_positions = build_mosaic_positions()
        progression["mosaic_positions"] = mosaic_positions
        game_config = load_game_config()
        game_config["progression"] = progression
        save_game_config(game_config)

    st.session_state.started = progression["started"]
    st.session_state.current_index = progression["current_index"]
    st.session_state.completed = st.session_state.current_index >= len(ORDERED_PARTICIPANTS)
    st.session_state.mosaic_positions = mosaic_positions

    revealed_portraits: dict[int, dict] = {}

    if len(mosaic_positions) == len(ORDERED_PARTICIPANTS):
        for index in range(st.session_state.current_index):
            if index >= len(ORDERED_PARTICIPANTS):
                break
            cell_id = mosaic_positions[index]
            participant_name = ORDERED_PARTICIPANTS[index]
            image_bytes = fetch_image_from_storage(participant_name)
            portrait = None
            if image_bytes:
                portrait = Image.open(BytesIO(image_bytes)).convert("RGB")
            revealed_portraits[cell_id] = {
                "giver": participant_name,
                "portrait": portrait,
            }

    st.session_state.revealed_portraits = revealed_portraits


def save_and_apply_progression(progression: dict) -> None:
    game_config = load_game_config()
    game_config["progression"] = progression
    save_game_config(game_config)
    apply_progression(progression)


def render_game_page(is_main_user: bool = True) -> None:
    if "started" not in st.session_state:
        apply_progression(load_game_config()["progression"])

    image_column, text_column = st.columns([1, 2], vertical_alignment="center")
    with image_column:
        image_bytes = fetch_image_from_storage(GAME_CONFIG["name"])
        if image_bytes:
            st.image(BytesIO(image_bytes), width="stretch")
        else:
            st.warning("Configure les secrets Supabase S3 pour afficher l’image.")
    with text_column:
        st.markdown(f"<div class='big-title'>{GAME_CONFIG['name']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-title'>🎉 {GAME_CONFIG['age']} ans 🎉</div>", unsafe_allow_html=True)

    if not is_main_user:
        st.info("Mode administration : vous consultez la progression, sans pouvoir saisir de réponse.")
        if st.button("Actualiser"):
            apply_progression(load_game_config()["progression"])
            st.rerun()

    if not st.session_state.started:
        st.image(get_mosaic_image({}), width="stretch")

        if is_main_user:
            if st.button("Démarrer le jeu"):
                game_config = load_game_config()
                game_config["progression"]["started"] = True
                save_and_apply_progression(game_config["progression"])
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
            st.markdown(f"## 🎂 Bon anniversaire, {GAME_CONFIG['name']} !")
            if st.button("Rejouer"):
                reset_game()
                st.rerun()
        else:
            st.markdown("## 🎂 Le jeu est terminé")

        st.stop()

    if not is_main_user:
        progress = st.session_state.current_index / len(ORDERED_PARTICIPANTS)
        st.progress(progress)
        st.caption(
            f"Progression : {st.session_state.current_index} / {len(ORDERED_PARTICIPANTS)} personnes validées"
        )
        st.stop()

    current_name = ORDERED_PARTICIPANTS[st.session_state.current_index]

    with st.form("quiz_form"):
        st.subheader(f"Personne {st.session_state.current_index + 1} / {len(ORDERED_PARTICIPANTS)}")
        answer = st.text_input(
            "Prénom de la personne",
            key=f"answer_{st.session_state.current_index}",
        )
        submitted = st.form_submit_button("Valider")

    if submitted:
        if normalize(answer) == normalize(current_name):
            game_config = load_game_config()
            progression = game_config["progression"]
            progression["current_index"] = st.session_state.current_index + 1

            save_and_apply_progression(progression)
            st.success("Bonne personne ! Contacte-la pour recevoir la prochaine énigme.")
            st.rerun()
        else:
            st.warning("Ce n'est pas cette personne. Essaie encore !")
