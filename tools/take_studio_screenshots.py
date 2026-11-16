"""Take pictures of MetallurgyPy Studio with Qt's offscreen platform.

Needs the GUI extra (``pip install -e ".[gui]"``). The windows are rendered by Qt itself
from the real application: the calculation shown is the model's own illustrative example.

    python tools/take_studio_screenshots.py [output-folder]

The default folder is docs/assets/studio. The CI "gui" job runs this script and uploads the
pictures as a build artifact, so they can be reviewed before being committed.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "studio")]

from PySide6.QtWidgets import QApplication  # noqa: E402

from metallurgypy_studio.app import MainWindow  # noqa: E402
from metallurgypy_studio.viewmodels.app_state import AppSettings  # noqa: E402

SIZE = (1280, 800)


def _snap(app: QApplication, window: MainWindow, folder: Path, name: str) -> None:
    app.processEvents()
    path = folder / f"{name}.png"
    if not window.grab().save(str(path)):
        raise SystemExit(f"could not write {path}")
    print("wrote", path)


def main(argv: list[str]) -> int:
    folder = Path(argv[0]) if argv else ROOT / "docs" / "assets" / "studio"
    folder.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    config = Path(tempfile.mkdtemp()) / "settings.json"  # never touch the user's real settings

    for theme in ("light", "dark"):
        window = MainWindow(app, AppSettings(theme=theme), config_file=config)
        window.resize(*SIZE)
        window.show()
        if theme == "light":
            window.nav.setCurrentRow(0)
            _snap(app, window, folder, "dashboard")
            window.nav.setCurrentRow(1)
            _snap(app, window, folder, "modules")
        window.nav.setCurrentRow(2)
        for model_id, label in (
            ("mass_balance.recovery", "mass_balance"),
            ("solvent_extraction.countercurrent_kremser", "kremser"),
        ):
            window.vm.select_model(model_id)
            window.vm.fill_example()
            window.vm.calculate()
            window.workspace.refresh()
            _snap(app, window, folder, f"calculation_{label}_{theme}")
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
