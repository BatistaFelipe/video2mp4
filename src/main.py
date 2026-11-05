from __future__ import annotations

import sys
import tkinter as tk
from tkinter import messagebox

from src.controllers.converter_controller import ConverterController
from src.models.ffmpeg_locator import locate_ffmpeg
from src.models.ffmpeg_runner import FFmpegRunner
from src.views.main_window import MainWindow


def main() -> int:
    try:
        ffmpeg_path = locate_ffmpeg()
    except FileNotFoundError as err:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("ffmpeg não encontrado", str(err))
        root.destroy()
        return 1

    runner = FFmpegRunner(ffmpeg_path)
    controller = ConverterController(runner)
    app = MainWindow(controller)
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
