import ast

import streamlit as st


def normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def get_streamlit_users() -> list[list | tuple]:
    users = st.secrets.get("app", {}).get("USERS", [])

    if isinstance(users, str):
        try:
            users = ast.literal_eval(users)
        except (SyntaxError, ValueError):
            return []

    if not isinstance(users, (list, tuple)):
        return []

    return list(users)


def authenticate_user(username: str, password: str) -> tuple[bool, bool]:
    """Return (is_authenticated, is_main_user) for matching credentials."""
    normalized_username = normalize(username)
    normalized_password = normalize(password)

    for user in get_streamlit_users():
        if len(user) != 3:
            continue

        configured_username, configured_password, is_main_user = user

        if (
            normalize(str(configured_username)) == normalized_username
            and normalize(str(configured_password)) == normalized_password
        ):
            return True, bool(is_main_user)

    return False, False
