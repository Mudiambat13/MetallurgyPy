"""GUI tests. They need PySide6 + pyqtgraph and run headless (offscreen platform).

They are skipped automatically when the GUI extra is not installed, so the Core
test job never depends on Qt.
"""

import os

import pytest

pytest.importorskip("PySide6")
pytest.importorskip("pyqtgraph")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from metallurgypy_studio.app import MainWindow
from metallurgypy_studio.main import main
from metallurgypy_studio.viewmodels.app_state import AppSettings

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
    assert window.nav.count() == 6
    for row in range(6):
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
        "feed_mass",
        "feed_grade",
        "concentrate_grade",
        "tailings_grade",
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


def test_import_view_lists_columns_and_reports_rows(window, tmp_path):
    f = tmp_path / "d.csv"
    f.write_text(
        "mass [t],grade [%],rec [%]\n1000,2.5,92\n900,2.1,90\n800,2.0,x\n700,1.9,89\n600,1.7,88\n",
        encoding="utf-8",
    )
    view = window.import_view
    assert window.import_vm.load(f)
    assert view.columns.rowCount() == 3
    for r, name in enumerate(("feed_mass", "feed_grade", "recovery")):
        view.columns.cellWidget(r, 2).setText(name)
    view._validate()
    assert "4 valid row(s), 1 rejected" in view.summary.text()
    assert view.results.rowCount() == 1


def test_project_view_add_and_compare(window, tmp_path):
    window.vm.select_model("mass_balance.recovery")
    window.vm.fill_example()
    window.vm.calculate()
    pv = window.project_vm
    assert pv.create(tmp_path / "p", "Pilot")
    assert pv.add_current("A") and pv.add_current("B")
    view = window.project_view
    assert view.list.count() == 2
    assert pv.compare([1, 2])
    assert view.table.rowCount() == len(pv.comparison.rows)
