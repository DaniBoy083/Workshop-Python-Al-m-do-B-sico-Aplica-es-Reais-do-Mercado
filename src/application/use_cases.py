from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from src.domain.analytics import AnalysisResult, build_answers_text, run_analytics
from src.domain.models import Pokemon
from src.infrastructure.storage import BasePokemonRecord


STAT_NAME_MAP = {
    "hp": "hp",
    "attack": "attack",
    "defense": "defense",
    "special-attack": "special_attack",
    "special-defense": "special_defense",
    "speed": "speed",
}

ProgressCallback = Callable[[float, str], None]


class PokemonGateway(Protocol):
    def get_pokemon(self, pokemon_name: str) -> dict[str, Any] | None:
        ...

    def get_type(self, pokemon_type: str) -> dict[str, Any] | None:
        ...


class StorageGateway(Protocol):
    def read_base_pokemon(self, file_path: Path) -> list[BasePokemonRecord]:
        ...

    def write_complete_pokemon(self, file_path: Path, pokemons: list[Pokemon]) -> None:
        ...

    def write_answers(self, file_path: Path, text: str) -> None:
        ...


@dataclass(frozen=True, slots=True)
class GenerationResult:
    processed_count: int
    success_count: int
    failed_names: tuple[str, ...]
    complete_csv_path: Path
    answers_path: Path
    answers_text: str
    analysis: AnalysisResult


class BuildPokedexUseCase:
    def __init__(
        self,
        gateway: PokemonGateway,
        storage: StorageGateway,
        sleep_seconds: float = 0.1,
    ) -> None:
        self._gateway = gateway
        self._storage = storage
        self._sleep_seconds = sleep_seconds

    def execute(
        self,
        base_csv_path: Path,
        complete_csv_path: Path,
        answers_path: Path,
        include_bonus: bool = True,
        on_progress: ProgressCallback | None = None,
    ) -> GenerationResult:
        base_records = self._storage.read_base_pokemon(base_csv_path)
        total = len(base_records)
        if on_progress:
            on_progress(0.0, f"Starting enrichment for {total} Pokemon entries...")

        pokemons: list[Pokemon] = []
        failed_names: list[str] = []

        for index, record in enumerate(base_records, start=1):
            pokemon = self._enrich_record(record)
            if pokemon is None:
                failed_names.append(record.name)
                message = f"[{index}/{total}] Could not resolve {record.name}; skipped."
            else:
                pokemons.append(pokemon)
                message = f"[{index}/{total}] {pokemon.name} enriched successfully."

            if on_progress:
                on_progress(index / total, message)

            if index < total and self._sleep_seconds > 0:
                time.sleep(self._sleep_seconds)

        self._storage.write_complete_pokemon(complete_csv_path, pokemons)
        if not pokemons:
            raise RuntimeError("No Pokemon could be enriched; output would be empty.")

        analysis = run_analytics(pokemons)
        if include_bonus:
            type_matchups = self._build_type_matchups(analysis)
            analysis = run_analytics(pokemons, type_matchups=type_matchups)

        answers_text = build_answers_text(analysis)
        if failed_names:
            answers_text += "\nPokemon nao encontrados e ignorados: " + ", ".join(failed_names) + "\n"

        self._storage.write_answers(answers_path, answers_text)

        if on_progress:
            on_progress(1.0, "Generation finished.")

        return GenerationResult(
            processed_count=total,
            success_count=len(pokemons),
            failed_names=tuple(failed_names),
            complete_csv_path=complete_csv_path,
            answers_path=answers_path,
            answers_text=answers_text,
            analysis=analysis,
        )

    def _enrich_record(self, record: BasePokemonRecord) -> Pokemon | None:
        payload = self._gateway.get_pokemon(record.name)
        if payload is None:
            return None

        try:
            return self._parse_payload(record.id, record.name, payload)
        except (KeyError, TypeError, ValueError):
            return None

    def _parse_payload(self, pokemon_id: int, fallback_name: str, payload: dict[str, Any]) -> Pokemon:
        raw_types = payload.get("types", [])
        sorted_types = sorted(raw_types, key=lambda item: item.get("slot", 999))
        types: list[str] = []
        for item in sorted_types:
            type_name = (
                item.get("type", {}).get("name", "").strip().lower() if isinstance(item, dict) else ""
            )
            if type_name:
                types.append(type_name)

        stats_map = {value: 0 for value in STAT_NAME_MAP.values()}
        for item in payload.get("stats", []):
            if not isinstance(item, dict):
                continue
            stat_name = item.get("stat", {}).get("name", "")
            mapped_name = STAT_NAME_MAP.get(stat_name)
            if not mapped_name:
                continue
            stats_map[mapped_name] = int(item.get("base_stat", 0))

        abilities = payload.get("abilities", [])
        ability_name = "unknown"
        if abilities and isinstance(abilities[0], dict):
            ability_name = abilities[0].get("ability", {}).get("name", "unknown")

        resolved_name = str(payload.get("name") or fallback_name).strip().lower()
        if not resolved_name:
            resolved_name = fallback_name.strip().lower()

        return Pokemon(
            id=pokemon_id,
            name=resolved_name,
            types=tuple(types) if types else ("unknown",),
            hp=stats_map["hp"],
            attack=stats_map["attack"],
            defense=stats_map["defense"],
            special_attack=stats_map["special_attack"],
            special_defense=stats_map["special_defense"],
            speed=stats_map["speed"],
            height=int(payload.get("height", 0)),
            weight=int(payload.get("weight", 0)),
            ability=str(ability_name),
        )

    def _build_type_matchups(self, analysis: AnalysisResult) -> dict[str, dict[str, list[str]]]:
        type_matchups: dict[str, dict[str, list[str]]] = {}
        dream_team_types = sorted({pokemon_type for pokemon in analysis.dream_team for pokemon_type in pokemon.types})

        for pokemon_type in dream_team_types:
            payload = self._gateway.get_type(pokemon_type)
            if not payload:
                continue

            damage_relations = payload.get("damage_relations", {})
            if not isinstance(damage_relations, dict):
                continue

            type_matchups[pokemon_type] = {
                "double_damage_to": self._extract_type_list(damage_relations.get("double_damage_to", [])),
                "double_damage_from": self._extract_type_list(
                    damage_relations.get("double_damage_from", [])
                ),
            }

        return type_matchups

    @staticmethod
    def _extract_type_list(values: Any) -> list[str]:
        if not isinstance(values, list):
            return []

        result: list[str] = []
        for item in values:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip().lower()
            if name:
                result.append(name)
        return result
