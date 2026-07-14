from __future__ import annotations

from pathlib import Path

from src.application.use_cases import BuildPokedexUseCase
from src.infrastructure.storage import CsvFileStorage


class FakeGateway:
    def __init__(self) -> None:
        self._pokemon_payloads = {
            "charizard": {
                "name": "charizard",
                "types": [
                    {"slot": 1, "type": {"name": "fire"}},
                    {"slot": 2, "type": {"name": "flying"}},
                ],
                "stats": [
                    {"stat": {"name": "hp"}, "base_stat": 78},
                    {"stat": {"name": "attack"}, "base_stat": 84},
                    {"stat": {"name": "defense"}, "base_stat": 78},
                    {"stat": {"name": "special-attack"}, "base_stat": 109},
                    {"stat": {"name": "special-defense"}, "base_stat": 85},
                    {"stat": {"name": "speed"}, "base_stat": 100},
                ],
                "height": 17,
                "weight": 905,
                "abilities": [{"ability": {"name": "blaze"}}],
            },
            "blastoise": {
                "name": "blastoise",
                "types": [{"slot": 1, "type": {"name": "water"}}],
                "stats": [
                    {"stat": {"name": "hp"}, "base_stat": 79},
                    {"stat": {"name": "attack"}, "base_stat": 83},
                    {"stat": {"name": "defense"}, "base_stat": 100},
                    {"stat": {"name": "special-attack"}, "base_stat": 85},
                    {"stat": {"name": "special-defense"}, "base_stat": 105},
                    {"stat": {"name": "speed"}, "base_stat": 78},
                ],
                "height": 16,
                "weight": 855,
                "abilities": [{"ability": {"name": "torrent"}}],
            },
            "mewtwo": {
                "name": "mewtwo",
                "types": [{"slot": 1, "type": {"name": "psychic"}}],
                "stats": [
                    {"stat": {"name": "hp"}, "base_stat": 106},
                    {"stat": {"name": "attack"}, "base_stat": 110},
                    {"stat": {"name": "defense"}, "base_stat": 90},
                    {"stat": {"name": "special-attack"}, "base_stat": 154},
                    {"stat": {"name": "special-defense"}, "base_stat": 90},
                    {"stat": {"name": "speed"}, "base_stat": 130},
                ],
                "height": 20,
                "weight": 1220,
                "abilities": [{"ability": {"name": "pressure"}}],
            },
        }

    def get_pokemon(self, pokemon_name: str):
        return self._pokemon_payloads.get(pokemon_name.lower())

    def get_type(self, pokemon_type: str):
        if pokemon_type == "fire":
            return {
                "damage_relations": {
                    "double_damage_to": [{"name": "grass"}],
                    "double_damage_from": [{"name": "water"}],
                }
            }
        if pokemon_type == "water":
            return {
                "damage_relations": {
                    "double_damage_to": [{"name": "fire"}],
                    "double_damage_from": [{"name": "electric"}],
                }
            }
        if pokemon_type == "psychic":
            return {
                "damage_relations": {
                    "double_damage_to": [{"name": "fighting"}],
                    "double_damage_from": [{"name": "ghost"}],
                }
            }
        return None


def test_use_case_generates_outputs_and_handles_not_found(tmp_path: Path) -> None:
    base_csv = tmp_path / "pokemon_base.csv"
    base_csv.write_text(
        "id,nome\n6,charizard\n9,blastoise\n150,mewtwo\n999,missingmon\n",
        encoding="utf-8",
    )

    complete_csv = tmp_path / "pokemon_completo.csv"
    answers_txt = tmp_path / "respostas.txt"

    use_case = BuildPokedexUseCase(
        gateway=FakeGateway(),
        storage=CsvFileStorage(),
        sleep_seconds=0,
    )

    progress_events: list[str] = []

    result = use_case.execute(
        base_csv_path=base_csv,
        complete_csv_path=complete_csv,
        answers_path=answers_txt,
        include_bonus=True,
        on_progress=lambda _progress, message: progress_events.append(message),
    )

    assert result.processed_count == 4
    assert result.success_count == 3
    assert result.failed_names == ("missingmon",)

    csv_content = complete_csv.read_text(encoding="utf-8")
    assert "charizard" in csv_content
    assert "blastoise" in csv_content
    assert "mewtwo" in csv_content
    assert "missingmon" not in csv_content

    answers_content = answers_txt.read_text(encoding="utf-8")
    assert "mewtwo" in answers_content
    assert "Pokemon nao encontrados e ignorados: missingmon" in answers_content
    assert "BONUS - MATCHUPS DO TIME DOS SONHOS" in answers_content
    assert "Vantagens contra tipos:" in answers_content

    assert any("Could not resolve missingmon" in event for event in progress_events)
    assert progress_events[-1] == "Generation finished."
