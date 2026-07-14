from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .models import Pokemon


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    strongest_pokemon: Pokemon
    top_attack_type: str
    top_attack_type_average: float
    water_count: int
    top_speed_pokemons: tuple[Pokemon, ...]
    dream_team: tuple[Pokemon, ...]
    advantage_types: tuple[str, ...]
    disadvantage_types: tuple[str, ...]


def run_analytics(
    pokemons: list[Pokemon],
    type_matchups: dict[str, dict[str, list[str]]] | None = None,
) -> AnalysisResult:
    if not pokemons:
        raise ValueError("Cannot run analytics with an empty pokemon list.")

    strongest = max(
        pokemons,
        key=lambda pokemon: (pokemon.total_stats, pokemon.attack, pokemon.speed, pokemon.name),
    )

    type_attack_values: dict[str, list[int]] = defaultdict(list)
    for pokemon in pokemons:
        for pokemon_type in pokemon.types:
            type_attack_values[pokemon_type].append(pokemon.attack)

    top_attack_type = ""
    top_attack_average = 0.0
    for pokemon_type, attacks in type_attack_values.items():
        attack_average = sum(attacks) / len(attacks)
        if (
            attack_average > top_attack_average
            or (attack_average == top_attack_average and pokemon_type < top_attack_type)
        ):
            top_attack_type = pokemon_type
            top_attack_average = attack_average

    water_count = sum(1 for pokemon in pokemons if "water" in pokemon.types)

    sorted_by_speed = sorted(
        pokemons,
        key=lambda pokemon: (pokemon.speed, pokemon.total_stats, pokemon.attack, pokemon.name),
        reverse=True,
    )
    top_speed_pokemons = tuple(sorted_by_speed[:5])

    sorted_by_total = sorted(
        pokemons,
        key=lambda pokemon: (pokemon.total_stats, pokemon.attack, pokemon.speed, pokemon.name),
        reverse=True,
    )
    dream_team = tuple(sorted_by_total[:6])

    advantage_types: tuple[str, ...] = tuple()
    disadvantage_types: tuple[str, ...] = tuple()
    if type_matchups:
        advantage_set: set[str] = set()
        disadvantage_set: set[str] = set()
        for pokemon in dream_team:
            for pokemon_type in pokemon.types:
                matchup = type_matchups.get(pokemon_type)
                if not matchup:
                    continue
                advantage_set.update(matchup.get("double_damage_to", []))
                disadvantage_set.update(matchup.get("double_damage_from", []))

        advantage_types = tuple(sorted(advantage_set))
        disadvantage_types = tuple(sorted(disadvantage_set))

    return AnalysisResult(
        strongest_pokemon=strongest,
        top_attack_type=top_attack_type,
        top_attack_type_average=top_attack_average,
        water_count=water_count,
        top_speed_pokemons=top_speed_pokemons,
        dream_team=dream_team,
        advantage_types=advantage_types,
        disadvantage_types=disadvantage_types,
    )


def build_answers_text(result: AnalysisResult) -> str:
    fastest_names = ", ".join(pokemon.name for pokemon in result.top_speed_pokemons)
    dream_team_names = ", ".join(pokemon.name for pokemon in result.dream_team)

    lines = [
        "RESPOSTAS DO DESAFIO POKEDEX",
        "",
        (
            "1. Pokemon com maior soma total de stats: "
            f"{result.strongest_pokemon.name} ({result.strongest_pokemon.total_stats})"
        ),
        (
            "2. Tipo com maior media de Attack: "
            f"{result.top_attack_type} ({result.top_attack_type_average:.2f})"
        ),
        f"3. Quantidade de Pokemon do tipo Water: {result.water_count}",
        f"4. Top 5 mais rapidos: {fastest_names}",
        f"5. Time dos sonhos (6 maiores totais): {dream_team_names}",
    ]

    if result.advantage_types or result.disadvantage_types:
        lines.extend(
            [
                "",
                "BONUS - MATCHUPS DO TIME DOS SONHOS",
                "Vantagens contra tipos: "
                + (", ".join(result.advantage_types) if result.advantage_types else "nenhuma"),
                "Desvantagens contra tipos: "
                + (
                    ", ".join(result.disadvantage_types)
                    if result.disadvantage_types
                    else "nenhuma"
                ),
            ]
        )

    return "\n".join(lines) + "\n"
