from __future__ import annotations

import re
from typing import Any

import requests

from src.infrastructure.cache import JsonFileCache
from src.shared.text_utils import normalize_pokemon_name


SAFE_SEGMENT_PATTERN = re.compile(r"^[a-z0-9-]+$")


class PokeApiClient:
    def __init__(
        self,
        cache: JsonFileCache,
        base_url: str = "https://pokeapi.co/api/v2",
        timeout_seconds: float = 10.0,
        retry_count: int = 2,
    ) -> None:
        self._cache = cache
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._retry_count = retry_count
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "pokedex-workshop-clean-arch/1.0",
            }
        )

    def get_pokemon(self, pokemon_name: str) -> dict[str, Any] | None:
        normalized_name = normalize_pokemon_name(pokemon_name)
        if not self._is_safe_segment(normalized_name):
            return None

        cache_key = f"pokemon:{normalized_name}"
        cached = self._cache.get(cache_key)
        if isinstance(cached, dict):
            return cached

        payload = self._get_json(f"/pokemon/{normalized_name}")
        if payload is not None:
            self._cache.set(cache_key, payload)
        return payload

    def get_type(self, pokemon_type: str) -> dict[str, Any] | None:
        normalized_type = normalize_pokemon_name(pokemon_type)
        if not self._is_safe_segment(normalized_type):
            return None

        cache_key = f"type:{normalized_type}"
        cached = self._cache.get(cache_key)
        if isinstance(cached, dict):
            return cached

        payload = self._get_json(f"/type/{normalized_type}")
        if payload is not None:
            self._cache.set(cache_key, payload)
        return payload

    def _get_json(self, endpoint: str) -> dict[str, Any] | None:
        url = f"{self._base_url}{endpoint}"
        for attempt in range(self._retry_count + 1):
            try:
                response = self._session.get(url, timeout=self._timeout_seconds)
            except requests.RequestException:
                if attempt == self._retry_count:
                    return None
                continue

            if response.status_code == 404:
                return None

            if response.status_code >= 500:
                if attempt == self._retry_count:
                    return None
                continue

            if response.status_code >= 400:
                return None

            try:
                data = response.json()
            except ValueError:
                if attempt == self._retry_count:
                    return None
                continue

            if isinstance(data, dict):
                return data

            return None

        return None

    @staticmethod
    def _is_safe_segment(value: str) -> bool:
        return bool(value) and bool(SAFE_SEGMENT_PATTERN.fullmatch(value))
