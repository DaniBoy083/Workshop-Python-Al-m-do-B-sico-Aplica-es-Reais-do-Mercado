from __future__ import annotations

from src.domain.analytics import run_analytics
from src.domain.models import Pokemon


def build_pokemon(
    pokemon_id: int,
    name: str,
    pokemon_types: tuple[str, ...],
    attack: int,
    speed: int,
    total_base: int,
) -> Pokemon:
    remainder = max(total_base - attack - speed, 0)
    hp = remainder // 4
    defense = remainder // 4
    special_attack = remainder // 4
    special_defense = remainder - hp - defense - special_attack
    return Pokemon(
        id=pokemon_id,
        name=name,
        types=pokemon_types,
        hp=hp,
        attack=attack,
        defense=defense,
        special_attack=special_attack,
        special_defense=special_defense,
        speed=speed,
        height=10,
        weight=100,
        ability="test-ability",
    )


def test_run_analytics_main_answers() -> None:
    sample = [
        build_pokemon(1, "alpha", ("fire",), attack=100, speed=95, total_base=530),
        build_pokemon(2, "beta", ("water",), attack=80, speed=85, total_base=500),
        build_pokemon(3, "gamma", ("water", "flying"), attack=120, speed=70, total_base=560),
        build_pokemon(4, "delta", ("psychic",), attack=130, speed=110, total_base=590),
        build_pokemon(5, "epsilon", ("steel",), attack=90, speed=60, total_base=520),
        build_pokemon(6, "zeta", ("dragon",), attack=125, speed=102, total_base=600),
        build_pokemon(7, "eta", ("ghost",), attack=105, speed=88, total_base=510),
    ]

    result = run_analytics(sample)

    assert result.strongest_pokemon.name == "zeta"
    assert result.top_attack_type == "psychic"
    assert result.water_count == 2
    assert [pokemon.name for pokemon in result.top_speed_pokemons] == [
        "delta",
        "zeta",
        "alpha",
        "eta",
        "beta",
    ]
    assert [pokemon.name for pokemon in result.dream_team] == [
        "zeta",
        "delta",
        "gamma",
        "alpha",
        "epsilon",
        "eta",
    ]
