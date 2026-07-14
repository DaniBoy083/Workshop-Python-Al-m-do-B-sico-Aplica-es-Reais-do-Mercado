from __future__ import annotations

import re
import unicodedata


SAFE_NAME_PATTERN = re.compile(r"[^a-z0-9-]")


def normalize_pokemon_name(raw_name: str) -> str:
    """Normalize user-provided names to the format expected by PokeAPI."""
    normalized = unicodedata.normalize("NFKD", raw_name.strip().lower())
    no_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    no_spaces = no_accents.replace(" ", "-")
    safe_name = SAFE_NAME_PATTERN.sub("", no_spaces)
    safe_name = re.sub(r"-{2,}", "-", safe_name).strip("-")
    return safe_name
