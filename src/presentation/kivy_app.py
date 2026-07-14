from __future__ import annotations

from pathlib import Path
from threading import Thread
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from src.application.use_cases import BuildPokedexUseCase, GenerationResult
from src.infrastructure.cache import JsonFileCache
from src.infrastructure.http_client import PokeApiClient
from src.infrastructure.storage import CsvFileStorage


KV_LAYOUT = """
#:import dp kivy.metrics.dp

<RootPanel>:
    orientation: "vertical"
    padding: dp(18)
    spacing: dp(12)
    canvas.before:
        Color:
            rgba: 0.95, 0.97, 0.99, 1
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: "vertical"
        size_hint_y: None
        height: dp(108)
        padding: dp(12)
        spacing: dp(6)
        canvas.before:
            Color:
                rgba: 0.07, 0.20, 0.36, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [16, 16, 16, 16]
        Label:
            text: "Pokedex Data Studio"
            bold: True
            color: 0.96, 0.98, 1, 1
            font_size: "26sp"
            halign: "left"
            text_size: self.size
        Label:
            text: "Enriquecimento via PokeAPI + respostas automaticas"
            color: 0.82, 0.90, 0.98, 1
            halign: "left"
            text_size: self.size

    BoxLayout:
        orientation: "vertical"
        spacing: dp(8)
        padding: dp(12)
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [14, 14, 14, 14]

        Label:
            text: "Arquivos"
            size_hint_y: None
            height: dp(28)
            bold: True
            color: 0.06, 0.14, 0.26, 1
            halign: "left"
            text_size: self.size

        Label:
            text: "CSV base"
            size_hint_y: None
            height: dp(18)
            halign: "left"
            text_size: self.size
            color: 0.20, 0.28, 0.39, 1
        TextInput:
            text: root.base_csv_path
            multiline: False
            on_text: root.base_csv_path = self.text
            size_hint_y: None
            height: dp(34)

        Label:
            text: "CSV completo"
            size_hint_y: None
            height: dp(18)
            halign: "left"
            text_size: self.size
            color: 0.20, 0.28, 0.39, 1
        TextInput:
            text: root.complete_csv_path
            multiline: False
            on_text: root.complete_csv_path = self.text
            size_hint_y: None
            height: dp(34)

        Label:
            text: "Arquivo de respostas"
            size_hint_y: None
            height: dp(18)
            halign: "left"
            text_size: self.size
            color: 0.20, 0.28, 0.39, 1
        TextInput:
            text: root.answers_file_path
            multiline: False
            on_text: root.answers_file_path = self.text
            size_hint_y: None
            height: dp(34)

        BoxLayout:
            size_hint_y: None
            height: dp(44)
            spacing: dp(10)

            Button:
                text: "Gerar Arquivos"
                bold: True
                disabled: root.is_running
                background_normal: ""
                background_color: 0.95, 0.38, 0.10, 1
                color: 1, 1, 1, 1
                on_release: root.run_generation()
            Button:
                text: "Limpar Log"
                disabled: root.is_running
                background_normal: ""
                background_color: 0.17, 0.29, 0.43, 1
                color: 1, 1, 1, 1
                on_release: root.clear_log()

        ProgressBar:
            max: 1
            value: root.progress_value
            size_hint_y: None
            height: dp(10)

        Label:
            text: root.status_text
            size_hint_y: None
            height: dp(22)
            halign: "left"
            text_size: self.size
            color: 0.25, 0.33, 0.45, 1

    BoxLayout:
        spacing: dp(12)

        BoxLayout:
            orientation: "vertical"
            padding: dp(10)
            spacing: dp(6)
            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [14, 14, 14, 14]

            Label:
                text: "Log de execucao"
                size_hint_y: None
                height: dp(26)
                bold: True
                color: 0.07, 0.14, 0.25, 1
                halign: "left"
                text_size: self.size

            ScrollView:
                do_scroll_x: False
                bar_width: dp(8)
                Label:
                    text: root.log_text if root.log_text else "Nenhum evento ainda."
                    text_size: self.width - dp(10), None
                    size_hint_y: None
                    height: self.texture_size[1] + dp(8)
                    valign: "top"
                    halign: "left"
                    color: 0.16, 0.22, 0.31, 1

        BoxLayout:
            orientation: "vertical"
            padding: dp(10)
            spacing: dp(6)
            canvas.before:
                Color:
                    rgba: 0.98, 0.99, 1, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [14, 14, 14, 14]

            Label:
                text: "Respostas"
                size_hint_y: None
                height: dp(26)
                bold: True
                color: 0.07, 0.14, 0.25, 1
                halign: "left"
                text_size: self.size

            TextInput:
                text: root.answers_preview
                readonly: True
                background_normal: ""
                background_color: 1, 1, 1, 1
                foreground_color: 0.16, 0.22, 0.31, 1
"""


class RootPanel(BoxLayout):
    base_csv_path = StringProperty("")
    complete_csv_path = StringProperty("")
    answers_file_path = StringProperty("")
    status_text = StringProperty("Ready to generate files.")
    log_text = StringProperty("")
    answers_preview = StringProperty("Respostas ainda nao geradas.")
    progress_value = NumericProperty(0.0)
    is_running = BooleanProperty(False)

    def __init__(self, use_case: BuildPokedexUseCase, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._use_case = use_case
        self._project_root = Path(__file__).resolve().parents[2]
        self.base_csv_path = str(self._project_root / "pokemon_base.csv")
        self.complete_csv_path = str(self._project_root / "pokemon_completo.csv")
        self.answers_file_path = str(self._project_root / "respostas.txt")

    def run_generation(self) -> None:
        if self.is_running:
            return

        self.is_running = True
        self.progress_value = 0.0
        self.status_text = "Running enrichment..."
        self._append_log("Starting generation workflow.")

        worker = Thread(target=self._run_generation_worker, daemon=True)
        worker.start()

    def clear_log(self) -> None:
        self.log_text = ""
        self.status_text = "Log cleared."

    def _run_generation_worker(self) -> None:
        try:
            result = self._use_case.execute(
                base_csv_path=Path(self.base_csv_path).expanduser(),
                complete_csv_path=Path(self.complete_csv_path).expanduser(),
                answers_path=Path(self.answers_file_path).expanduser(),
                include_bonus=True,
                on_progress=self._thread_safe_progress,
            )
            Clock.schedule_once(lambda dt: self._on_generation_success(result))
        except Exception as error:  # noqa: BLE001
            error_trace = traceback.format_exc()
            Clock.schedule_once(
                lambda dt: self._on_generation_error(str(error), error_trace)
            )

    def _thread_safe_progress(self, progress: float, message: str) -> None:
        Clock.schedule_once(lambda dt, p=progress, m=message: self._update_progress(p, m))

    def _update_progress(self, progress: float, message: str) -> None:
        self.progress_value = max(0.0, min(1.0, progress))
        self.status_text = message
        self._append_log(message)

    def _on_generation_success(self, result: GenerationResult) -> None:
        self.is_running = False
        self.progress_value = 1.0
        self.status_text = (
            f"Done. Success: {result.success_count}/{result.processed_count}. "
            f"Failed: {len(result.failed_names)}"
        )
        self.answers_preview = result.answers_text
        self._append_log("Generation completed successfully.")
        self._append_log(f"CSV saved at: {result.complete_csv_path}")
        self._append_log(f"Answers saved at: {result.answers_path}")

    def _on_generation_error(self, message: str, stack_trace: str) -> None:
        self.is_running = False
        self.status_text = f"Execution failed: {message}"
        self._append_log("Error while generating files.")
        self._append_log(stack_trace)

    def _append_log(self, message: str) -> None:
        current_lines = self.log_text.splitlines() if self.log_text else []
        current_lines.append(message)
        self.log_text = "\n".join(current_lines[-200:])


class PokedexApp(App):
    def build(self) -> RootPanel:
        self.title = "Pokedex Data Studio"
        Builder.load_string(KV_LAYOUT)

        project_root = Path(__file__).resolve().parents[2]
        cache = JsonFileCache(project_root / "cache" / "pokeapi_cache.json")
        gateway = PokeApiClient(cache=cache)
        storage = CsvFileStorage()
        use_case = BuildPokedexUseCase(gateway=gateway, storage=storage, sleep_seconds=0.1)

        return RootPanel(use_case=use_case)
