from io import BytesIO

import streamlit as st
from PIL import Image, ImageOps

from app.mosaic import (
    build_mosaic_positions,
    get_mosaic_dimensions,
    get_mosaic_image,
)
from app.utils import capitalize_name, normalize
from app.storage import (
    fetch_image_from_storage,
    save_game_config,
    load_game_config,
)

GAME_CONFIG = load_game_config()
ORDERED_PARTICIPANTS = GAME_CONFIG["ordered_participants"]
GRID_COLS, GRID_ROWS = get_mosaic_dimensions(len(ORDERED_PARTICIPANTS))


@st.cache_resource(ttl=3600)
def get_cached_portrait(participant_name: str) -> Image.Image | None:
    """Download and decode an image once, then keep it in memory."""
    image_bytes = fetch_image_from_storage(participant_name)
    if not image_bytes:
        return None

    return ImageOps.exif_transpose(Image.open(BytesIO(image_bytes))).convert("RGB")


def preload_game_images() -> None:
    """Preload all game images once per user session."""
    if st.session_state.get("images_preloaded", False):
        return

    image_names = tuple(dict.fromkeys((GAME_CONFIG["name"], *ORDERED_PARTICIPANTS)))
    with st.spinner("Préparation des images…"):
        for participant_name in image_names:
            get_cached_portrait(participant_name)

    st.session_state.images_preloaded = True


def get_phone_number(participant_name: str) -> str | None:
    phone_numbers = GAME_CONFIG.get("phone_number_by_participant", {})
    if not isinstance(phone_numbers, dict):
        return None

    phone_number = phone_numbers.get(participant_name)
    if phone_number is None:
        return None

    phone = str(phone_number).strip()
    return phone or None


def answer_matches_participant(answer: str, participant_name: str) -> bool:
    aliases_by_participant = GAME_CONFIG.get("alias_by_participant", {})
    valid_answers = [participant_name]

    if isinstance(aliases_by_participant, dict):
        aliases = aliases_by_participant.get(participant_name)
        if isinstance(aliases, list):
            valid_answers.extend(str(alias) for alias in aliases)

    normalized_answer = normalize(answer)
    return normalized_answer in valid_answers


def reset_game() -> None:
    game_config = load_game_config()
    game_config["progression"] = {
        "started": False,
        "current_index": 0,
        "mosaic_positions": build_mosaic_positions(
            len(ORDERED_PARTICIPANTS),
            ORDERED_PARTICIPANTS,
        ),
    }
    save_game_config(game_config)
    apply_progression(game_config["progression"])


def apply_progression(progression: dict) -> None:
    mosaic_positions = progression.get("mosaic_positions", [])
    expected_positions = build_mosaic_positions(
        len(ORDERED_PARTICIPANTS),
        ORDERED_PARTICIPANTS,
    )
    positions_need_repair = mosaic_positions != expected_positions

    if positions_need_repair:
        mosaic_positions = expected_positions
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
            portrait = get_cached_portrait(participant_name)
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
    preload_game_images()

    if "started" not in st.session_state:
        apply_progression(load_game_config()["progression"])

    image_column, text_column = st.columns([1, 2], vertical_alignment="center")
    with image_column:
        birthday_portrait = get_cached_portrait(GAME_CONFIG["name"])
        if birthday_portrait:
            st.image(birthday_portrait, width="stretch")
    with text_column:
        player_name = capitalize_name(GAME_CONFIG["name"])
        st.markdown(f"<div class='big-title'>{player_name}</div>", unsafe_allow_html=True)
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

    contact_message = st.session_state.pop("contact_message", None)
    if contact_message:
        st.success(contact_message)

    if st.session_state.completed:
        st.balloons()

        if is_main_user:
            st.markdown(f"## 🎂 Bon anniversaire, {capitalize_name(GAME_CONFIG['name'])} !")
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
        if answer_matches_participant(answer, current_name):
            phone_number = get_phone_number(current_name)
            if phone_number:
                contact_message = (
                    f"Bonne personne ! Contacte {capitalize_name(current_name)} au **{phone_number}** "
                    "pour recevoir la prochaine énigme."
                )
            else:
                contact_message = "Bonne personne ! Contacte-la pour recevoir la prochaine énigme."

            game_config = load_game_config()
            progression = game_config["progression"]
            progression["current_index"] = st.session_state.current_index + 1

            save_and_apply_progression(progression)
            st.session_state.contact_message = contact_message
            st.rerun()
        else:
            st.session_state.pop("contact_message", None)
            st.warning("Ce n'est pas cette personne. Essaie encore !")
