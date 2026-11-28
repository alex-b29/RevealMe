import unicodedata


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    dash_characters = "-‐‑‒–—−"
    return "".join(
        character
        for character in without_accents.lower()
        if not character.isspace() and character not in dash_characters
    )


def capitalize_name(value: str) -> str:
    value = str(value)
    if not value:
        return value
    return value[0].upper() + value[1:]
