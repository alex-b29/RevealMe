from io import BytesIO

import streamlit as st
from PIL import Image

from app.mosaic import (
    build_mosaic_positions,
    get_mosaic_dimensions,
    get_mosaic_image,
    normalize,
)
from app.storage import (
    fetch_image_from_storage,
    save_game_config,
    load_game_config,
)

GAME_CONFIG = load_game_config()
ORDERED_PARTICIPANTS = GAME_CONFIG["ordered_participants"]
GRID_COLS, GRID_ROWS = get_mosaic_dimensions(len(ORDERED_PARTICIPANTS))


def reset_game() -> None:
    game_config = load_game_config()
    game_config["progression"] = {
        "started": False,
        "current_index": 0,
        "mosaic_positions": build_mosaic_positions(len(ORDERED_PARTICIPANTS)),
    }
    save_game_config(game_config)
    apply_progression(game_config["progression"])


def apply_progression(progression: dict) -> None:
    mosaic_positions = progression.get("mosaic_positions", [])
    positions_need_repair = len(mosaic_positions) != len(ORDERED_PARTICIPANTS)

    if positions_need_repair:
        mosaic_positions = build_mosaic_positions(len(ORDERED_PARTICIPANTS))
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
                "name": participant_name,
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
    with text_column:
        st.markdown(f"<div class='big-title'>{GAME_CONFIG['name']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-title'>🎉 {GAME_CONFIG['age']} ans 🎉</div>", unsafe_allow_html=True)

    if not is_main_user:
        st.info("Mode administration : vous consultez la progression, sans pouvoir saisir de réponse.")
        if st.button("Actualiser"):
            apply_progression(load_game_config()["progression"])
            st.rerun()

    if not st.session_state.started:
        st.image(get_mosaic_image({}, GRID_COLS, GRID_ROWS), width="stretch")

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
        get_mosaic_image(st.session_state.revealed_portraits, GRID_COLS, GRID_ROWS),
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
