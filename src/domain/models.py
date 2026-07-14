from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Pokemon:
    id: int
    name: str
    types: tuple[str, ...]
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int
    height: int
    weight: int
    ability: str

    @property
    def total_stats(self) -> int:
        return (
            self.hp
            + self.attack
            + self.defense
            + self.special_attack
            + self.special_defense
            + self.speed
        )

    def to_csv_row(self) -> dict[str, str | int]:
        return {
            "id": self.id,
            "nome": self.name,
            "tipos": "|".join(self.types),
            "hp": self.hp,
            "attack": self.attack,
            "defense": self.defense,
            "special_attack": self.special_attack,
            "special_defense": self.special_defense,
            "speed": self.speed,
            "height": self.height,
            "weight": self.weight,
            "ability": self.ability,
            "total_stats": self.total_stats,
        }
