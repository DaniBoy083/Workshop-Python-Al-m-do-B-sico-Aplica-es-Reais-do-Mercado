from __future__ import annotations

import argparse
from pathlib import Path

from src.application.use_cases import BuildPokedexUseCase
from src.infrastructure.cache import JsonFileCache
from src.infrastructure.http_client import PokeApiClient
from src.infrastructure.storage import CsvFileStorage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Pokemon enriched CSV and answers file.")
    parser.add_argument("--base-csv", default="pokemon_base.csv", help="Path to base input CSV")
    parser.add_argument(
        "--complete-csv",
        default="pokemon_completo.csv",
        help="Path for generated complete CSV",
    )
    parser.add_argument("--answers", default="respostas.txt", help="Path for generated answers")
    parser.add_argument(
        "--no-bonus",
        action="store_true",
        help="Disable bonus type matchup analysis",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root_path = Path(__file__).resolve().parent

    base_csv_path = (root_path / args.base_csv).resolve()
    complete_csv_path = (root_path / args.complete_csv).resolve()
    answers_path = (root_path / args.answers).resolve()

    cache = JsonFileCache(root_path / "cache" / "pokeapi_cache.json")
    gateway = PokeApiClient(cache=cache)
    storage = CsvFileStorage()
    use_case = BuildPokedexUseCase(gateway=gateway, storage=storage, sleep_seconds=0.1)

    def on_progress(progress: float, message: str) -> None:
        percent = progress * 100
        print(f"[{percent:6.2f}%] {message}")

    result = use_case.execute(
        base_csv_path=base_csv_path,
        complete_csv_path=complete_csv_path,
        answers_path=answers_path,
        include_bonus=not args.no_bonus,
        on_progress=on_progress,
    )

    print("\nGeneration complete:")
    print(f"- Processed: {result.processed_count}")
    print(f"- Success: {result.success_count}")
    print(f"- Failed: {len(result.failed_names)}")
    print(f"- CSV: {result.complete_csv_path}")
    print(f"- Answers: {result.answers_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
