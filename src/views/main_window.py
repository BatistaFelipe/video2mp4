from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.controllers.converter_controller import ConverterController
from src.models.conversion_options import ConversionOptions
from src.models.ffmpeg_runner import FFmpegError

VIDEO_FILETYPES = (
    (
        "Vídeos",
        "*.dav *.264 *.h264 *.265 *.h265 *.avi *.mp4 *.mov *.mkv *.ts *.flv *.wmv",
    ),
    ("Todos os arquivos", "*.*"),
)

POLL_INTERVAL_MS = 100


class MainWindow(tk.Tk):
    def __init__(self, controller: ConverterController) -> None:
        super().__init__()
        self._controller = controller
        self._sources: list[Path] = []
        self._output_dir: Path | None = None
        self._queue: queue.Queue = queue.Queue()
        self._worker: threading.Thread | None = None
        self._cancel_event: threading.Event | None = None
        self._selection_buttons: list[ttk.Button] = []

        self.title("video2mp4")
        self.geometry("560x440")
        self.resizable(False, False)

        self._build_widgets()

    def _build_widgets(self) -> None:
        padding = {"padx": 10, "pady": 4}

        files_frame = ttk.LabelFrame(self, text="Arquivos de entrada")
        files_frame.pack(fill="both", expand=True, **padding)

        buttons_row = ttk.Frame(files_frame)
        buttons_row.pack(fill="x", padx=6, pady=6)

        select_btn = ttk.Button(
            buttons_row, text="Selecionar vídeos...", command=self._on_select_files
        )
        select_btn.pack(side="left")
        remove_btn = ttk.Button(
            buttons_row, text="Remover selecionado", command=self._on_remove_selected
        )
        remove_btn.pack(side="left", padx=6)
        clear_btn = ttk.Button(buttons_row, text="Limpar", command=self._on_clear)
        clear_btn.pack(side="left")
        self._selection_buttons.extend([select_btn, remove_btn, clear_btn])

        self._files_listbox = tk.Listbox(files_frame, height=8, activestyle="none")
        self._files_listbox.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        output_frame = ttk.LabelFrame(self, text="Pasta de saída")
        output_frame.pack(fill="x", **padding)

        output_row = ttk.Frame(output_frame)
        output_row.pack(fill="x", padx=6, pady=6)

        output_btn = ttk.Button(
            output_row, text="Selecionar pasta...", command=self._on_select_output
        )
        output_btn.pack(side="left")
        self._output_label = ttk.Label(
            output_row, text="(nenhuma pasta selecionada)", foreground="gray"
        )
        self._output_label.pack(side="left", padx=8)
        self._selection_buttons.append(output_btn)

        audio_frame = ttk.LabelFrame(self, text="Áudio")
        audio_frame.pack(fill="x", **padding)

        self._include_audio_var = tk.BooleanVar(value=True)
        self._audio_on_rb = ttk.Radiobutton(
            audio_frame,
            text="Com áudio (copiar faixa original)",
            variable=self._include_audio_var,
            value=True,
        )
        self._audio_on_rb.pack(anchor="w", padx=6, pady=2)
        self._audio_off_rb = ttk.Radiobutton(
            audio_frame,
            text="Sem áudio (remover faixa)",
            variable=self._include_audio_var,
            value=False,
        )
        self._audio_off_rb.pack(anchor="w", padx=6, pady=(0, 4))

        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", **padding)

        self._convert_button = ttk.Button(
            action_frame, text="Converter", command=self._on_convert
        )
        self._convert_button.pack(side="left")

        self._cancel_button = ttk.Button(
            action_frame,
            text="Cancelar",
            command=self._on_cancel,
            state="disabled",
        )
        self._cancel_button.pack(side="left", padx=(6, 0))

        self._progress = ttk.Progressbar(action_frame, mode="determinate")
        self._progress.pack(side="left", fill="x", expand=True, padx=8)

        self._status_label = ttk.Label(self, text="Pronto.", foreground="gray")
        self._status_label.pack(fill="x", padx=12, pady=(0, 8))

    def _on_select_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Selecione os vídeos", filetypes=VIDEO_FILETYPES
        )
        if not paths:
            return
        for raw in paths:
            path = Path(raw)
            if path not in self._sources:
                self._sources.append(path)
                self._files_listbox.insert("end", str(path))

    def _on_remove_selected(self) -> None:
        selection = list(self._files_listbox.curselection())
        for index in reversed(selection):
            self._files_listbox.delete(index)
            del self._sources[index]

    def _on_clear(self) -> None:
        self._files_listbox.delete(0, "end")
        self._sources.clear()

    def _on_select_output(self) -> None:
        path = filedialog.askdirectory(title="Selecione a pasta de saída")
        if not path:
            return
        self._output_dir = Path(path)
        self._output_label.configure(text=str(self._output_dir), foreground="black")

    def _on_convert(self) -> None:
        if self._worker is not None and self._worker.is_alive():
            return
        if not self._sources:
            messagebox.showwarning(
                "Nenhum arquivo", "Selecione pelo menos um vídeo para converter."
            )
            return
        if self._output_dir is None:
            messagebox.showwarning("Pasta de saída", "Selecione a pasta de saída.")
            return

        options = ConversionOptions(
            output_dir=self._output_dir,
            include_audio=self._include_audio_var.get(),
        )

        jobs = self._controller.build_jobs(list(self._sources), options)
        self._progress.configure(maximum=len(jobs), value=0)
        self._cancel_event = threading.Event()
        self._set_running(True)

        self._worker = threading.Thread(
            target=self._run_jobs_worker,
            args=(jobs, self._cancel_event),
            daemon=True,
        )
        self._worker.start()
        self.after(POLL_INTERVAL_MS, self._pump_queue)

    def _on_cancel(self) -> None:
        if self._cancel_event is None:
            return
        self._cancel_event.set()
        self._cancel_button.configure(state="disabled")
        self._status_label.configure(
            text="Cancelando (o arquivo em andamento termina antes de parar)...",
            foreground="orange",
        )

    def _run_jobs_worker(
        self, jobs: list, cancel_event: threading.Event
    ) -> None:
        def on_progress(current: int, total: int, name: str) -> None:
            self._queue.put(("progress", current, total, name))

        failures = self._controller.run_jobs(jobs, on_progress, cancel_event)
        self._queue.put(("done", failures, cancel_event.is_set()))

    def _pump_queue(self) -> None:
        try:
            while True:
                message = self._queue.get_nowait()
                self._handle_message(message)
        except queue.Empty:
            pass

        if self._worker is not None and self._worker.is_alive():
            self.after(POLL_INTERVAL_MS, self._pump_queue)

    def _handle_message(self, message: tuple) -> None:
        kind = message[0]
        if kind == "progress":
            _, current, total, name = message
            self._progress.configure(value=current - 1)
            self._status_label.configure(
                text=f"Convertendo {current}/{total}: {name}", foreground="black"
            )
        elif kind == "done":
            _, failures, cancelled = message
            if not cancelled:
                self._progress.configure(value=self._progress["maximum"])
            self._on_conversion_done(failures, cancelled)

    def _on_conversion_done(
        self, failures: list[tuple[object, FFmpegError]], cancelled: bool
    ) -> None:
        self._set_running(False)
        total = int(self._progress["maximum"])
        processed = int(self._progress["value"])
        success = max(processed - len(failures), 0)

        if cancelled:
            self._status_label.configure(
                text=f"Cancelado: {success}/{total} concluídos antes de parar.",
                foreground="orange",
            )
            messagebox.showinfo(
                "Cancelado",
                f"Conversão cancelada. {success}/{total} vídeos foram concluídos.",
            )
            return

        if not failures:
            self._status_label.configure(
                text=f"Concluído: {success}/{total} com sucesso.", foreground="black"
            )
            messagebox.showinfo(
                "Concluído", f"Convertidos {success}/{total} vídeos com sucesso."
            )
            return

        self._status_label.configure(
            text=f"Concluído com erros: {success}/{total}.", foreground="red"
        )
        details = "\n\n".join(
            f"- {job.source.name}:\n{str(err).strip()[:400]}"
            for job, err in failures
        )
        messagebox.showerror(
            "Falhas na conversão",
            f"{success}/{total} convertidos. Falhas:\n\n{details}",
        )

    def _set_running(self, running: bool) -> None:
        action_state = "disabled" if running else "normal"
        cancel_state = "normal" if running else "disabled"
        self._convert_button.configure(state=action_state)
        self._cancel_button.configure(state=cancel_state)
        for btn in self._selection_buttons:
            btn.configure(state=action_state)
        self._audio_on_rb.configure(state=action_state)
        self._audio_off_rb.configure(state=action_state)
