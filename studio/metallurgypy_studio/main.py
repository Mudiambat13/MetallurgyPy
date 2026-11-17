"""Entry point: ``metallurgypy-studio`` or ``python -m metallurgypy_studio``."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from typing import Any

from metallurgypy_studio import APP_NAME, __version__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="metallurgypy-studio", description=APP_NAME)
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    parser.add_argument(
        "--check",
        action="store_true",
        help="build the main window, then exit (used to verify the installation)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            'PySide6 is not installed. Install the GUI extra: pip install "metallurgypy[gui]"',
            file=sys.stderr,
        )
        return 2

    from metallurgypy_studio.app import MainWindow, settings_path
    from metallurgypy_studio.viewmodels.app_state import AppSettings

    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName(APP_NAME)
    config = settings_path()
    window = MainWindow(app, AppSettings.load(config), config_file=config)
    try:
        if args.check:
            app.processEvents()
            print(f"{APP_NAME} {__version__}: main window created.")
            return 0
        window.show()
        return int(app.exec())
    finally:
        _destroy_window(window, app)


def _destroy_window(window: Any, app: Any) -> None:
    """Delete the window while the QApplication still exists.

    Qt requires widgets to be destroyed before their QApplication. Python releases local
    variables in the order they were created, so without this step the application would be
    destroyed first, which crashes on some platforms (typically headless CI) at interpreter exit.
    """
    import shiboken6

    window.close()
    app.processEvents()
    if shiboken6.isValid(window):
        shiboken6.delete(window)
    app.processEvents()
