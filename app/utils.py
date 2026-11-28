import unicodedata


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return " ".join(without_accents.strip().lower().split())


def capitalize_name(value: str) -> str:
    value = str(value)
    if not value:
        return value
    return value[0].upper() + value[1:]
