from __future__ import annotations

from pathlib import Path

import requests

from src.infrastructure.cache import JsonFileCache
from src.infrastructure.http_client import PokeApiClient


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, raises_json: bool = False) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self._raises_json = raises_json

    def json(self) -> dict:
        if self._raises_json:
            raise ValueError("invalid json")
        return self._payload


def test_client_retries_transient_network_error_then_succeeds(tmp_path: Path) -> None:
    cache = JsonFileCache(tmp_path / "cache.json")
    client = PokeApiClient(cache=cache, retry_count=2)

    call_count = {"count": 0}

    def fake_get(_url: str, timeout: float):
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise requests.RequestException("temporary network failure")
        return FakeResponse(200, {"name": "pikachu", "types": []})

    client._session.get = fake_get  # type: ignore[method-assign]

    payload = client.get_pokemon("Pikachu")

    assert payload is not None
    assert payload["name"] == "pikachu"
    assert call_count["count"] == 2


def test_client_uses_cache_and_avoids_second_request(tmp_path: Path) -> None:
    cache = JsonFileCache(tmp_path / "cache.json")
    client = PokeApiClient(cache=cache, retry_count=0)

    call_count = {"count": 0}

    def fake_get(_url: str, timeout: float):
        call_count["count"] += 1
        return FakeResponse(200, {"name": "raichu", "types": []})

    client._session.get = fake_get  # type: ignore[method-assign]

    first_payload = client.get_pokemon("raichu")
    second_payload = client.get_pokemon("raichu")

    assert first_payload == second_payload
    assert call_count["count"] == 1


def test_client_handles_not_found_and_unsafe_segment(tmp_path: Path) -> None:
    cache = JsonFileCache(tmp_path / "cache.json")
    client = PokeApiClient(cache=cache, retry_count=0)

    def fake_get(_url: str, timeout: float):
        return FakeResponse(404, {})

    client._session.get = fake_get  # type: ignore[method-assign]

    assert client.get_pokemon("notfound") is None
    assert client.get_pokemon("../etc/passwd") is None
