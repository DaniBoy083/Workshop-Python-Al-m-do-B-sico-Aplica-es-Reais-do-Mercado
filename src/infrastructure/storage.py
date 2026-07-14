from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from src.domain.models import Pokemon


@dataclass(frozen=True, slots=True)
class BasePokemonRecord:
    id: int
    name: str


class CsvFileStorage:
    COMPLETE_COLUMNS = (
        "id",
        "nome",
        "tipos",
        "hp",
        "attack",
        "defense",
        "special_attack",
        "special_defense",
        "speed",
        "height",
        "weight",
        "ability",
        "total_stats",
    )

    def read_base_pokemon(self, file_path: Path) -> list[BasePokemonRecord]:
        if not file_path.exists():
            raise FileNotFoundError(f"Base CSV not found: {file_path}")

        with file_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            sample = csv_file.read(2048)
            csv_file.seek(0)

            dialect = self._detect_dialect(sample)
            reader = csv.DictReader(csv_file, dialect=dialect)
            if not reader.fieldnames:
                raise ValueError("CSV file has no header.")

            header_map = {header.strip().lower(): header for header in reader.fieldnames}
            id_column = header_map.get("id")
            name_column = header_map.get("nome") or header_map.get("name")
            if not id_column or not name_column:
                raise ValueError("CSV must contain id and nome columns.")

            base_records: list[BasePokemonRecord] = []
            for row_number, row in enumerate(reader, start=2):
                raw_id = (row.get(id_column) or "").strip()
                raw_name = (row.get(name_column) or "").strip()
                if not raw_id or not raw_name:
                    continue

                try:
                    pokemon_id = int(raw_id)
                except ValueError as error:
                    raise ValueError(
                        f"Invalid Pokemon id '{raw_id}' at line {row_number}."
                    ) from error

                base_records.append(BasePokemonRecord(id=pokemon_id, name=raw_name))

        if not base_records:
            raise ValueError("CSV did not contain any valid Pokemon entries.")

        return base_records

    def write_complete_pokemon(self, file_path: Path, pokemons: list[Pokemon]) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.COMPLETE_COLUMNS)
            writer.writeheader()
            for pokemon in pokemons:
                writer.writerow(pokemon.to_csv_row())

    def write_answers(self, file_path: Path, text: str) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(text, encoding="utf-8")

    @staticmethod
    def _detect_dialect(sample: str) -> csv.Dialect:
        if not sample.strip():
            return csv.get_dialect("excel")

        try:
            return csv.Sniffer().sniff(sample, delimiters=",;|\t")
        except csv.Error:
            return csv.get_dialect("excel")
