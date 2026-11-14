"""GUI tests. They need PySide6 + pyqtgraph and run headless (offscreen platform).

They are skipped automatically when the GUI extra is not installed, so the Core
test job never depends on Qt.
"""

import os

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pyqtgraph")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from metallurgypy_studio.app import MainWindow  # noqa: E402
from metallurgypy_studio.main import main  # noqa: E402
from metallurgypy_studio.viewmodels.app_state import AppSettings  # noqa: E402

pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(qapp):
    win = MainWindow(qapp, AppSettings())
    yield win
    win.close()


def test_entry_point_builds_the_window():
    assert main(["--check"]) == 0


def test_navigation_switches_pages(window):
    assert window.nav.count() == 4
    for row in range(4):
        window.nav.setCurrentRow(row)
        assert window.stack.currentIndex() == row


def test_dashboard_shows_only_real_state(window):
    assert window.dashboard.recent.item(0).text() == "No saved calculation yet."
    assert window.dashboard.session.item(0).text() == "Nothing calculated yet."


def test_workspace_calculates_example_and_shows_unrounded_core_values(window):
    ws = window.workspace
    window.vm.fill_example()
    window.vm.calculate()  # synchronous path of the same view model
    assert ws.table.rowCount() == len(window.vm.result.outputs())
    labels = [ws.table.item(r, 0).text() for r in range(ws.table.rowCount())]
    assert "Metal recovered" in labels
    assert window.vm.result.metal_recovered.value == 23.0
    assert "Recovery" in ws.assumptions.toPlainText()
    assert window.dashboard.session.count() == 1


def test_invalid_input_shows_error_next_to_the_field(window):
    ws = window.workspace
    window.vm.fill_example()
    window.vm.set_field("recovery", text="120")
    window.vm.calculate()
    assert ws.calc_button.isEnabled()
    assert not ws._error_labels["recovery"].isHidden()
    assert "0 to 1" in ws._error_labels["recovery"].text()


def test_form_is_rebuilt_for_another_model(window):
    window.vm.select_model("mass_balance.two_product")
    assert set(window.workspace._edits) == {
        "feed_mass", "feed_grade", "concentrate_grade", "tailings_grade"
    }


def test_theme_switch_applies_stylesheet(window, qapp):
    window.state.settings.theme = "dark"
    window._on_settings_changed()
    assert "#1c2229" in qapp.styleSheet()
    window.state.settings.theme = "light"
    window._on_settings_changed()
    assert "#f6f7f9" in qapp.styleSheet()


def test_save_and_reopen_through_the_view(window, tmp_path):
    window.vm.fill_example()
    window.vm.calculate()
    path = window.vm.save(tmp_path / "gui.mpy.json")
    window.vm.select_model("mass_balance.two_product")
    window.workspace.open_path(str(path))
    assert window.vm.spec.model_id == "mass_balance.recovery"
    assert window.vm.differences == ()
    assert window.workspace.verify_label.text().startswith("Saved result reproduced")
