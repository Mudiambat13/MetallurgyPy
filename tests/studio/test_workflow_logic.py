"""Import, project, comparison and report flows through the Qt-free view models."""

import pytest

from metallurgypy_studio.services.calculation_service import CalculationService
from metallurgypy_studio.services.workflow_service import DataService, ProjectService
from metallurgypy_studio.viewmodels.app_state import AppState
from metallurgypy_studio.viewmodels.workflow_viewmodels import ImportViewModel, ProjectViewModel
from metallurgypy_studio.viewmodels.workspace_viewmodel import WorkspaceViewModel


@pytest.fixture
def ws():
    vm = WorkspaceViewModel(CalculationService(), AppState())
    vm.select_model("mass_balance.recovery")
    vm.fill_example()
    vm.calculate()
    return vm


@pytest.fixture
def pvm(ws):
    return ProjectViewModel(ProjectService(CalculationService()), ws)


def test_import_flow_with_rejected_rows(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text("sample,mass [t],grade [%],rec [%]\nA,1000,2.5,92\nC,900,2.1,90\nD,800,2.0,91\nE,700,1.9,89\nF,600,1.7,88\nB,x,1,50\n", encoding="utf-8")
    ivm = ImportViewModel(DataService(), ["mass_balance.recovery"])
    assert ivm.load(f)
    by = {c.info.name: c for c in ivm.choices}
    assert by["mass [t]"].use and by["mass [t]"].unit == "t" and not by["sample"].use
    for col, name in (("mass [t]", "feed_mass"), ("grade [%]", "feed_grade"), ("rec [%]", "recovery")):
        by[col].name = name
    assert ivm.validate()
    assert "5 valid row(s), 1 rejected" in ivm.summary()
    assert ivm.run_model() and "5 succeeded" in ivm.summary()
    out = ivm.export_rejected(tmp_path / "rej.csv")
    assert out.exists()


def test_import_errors_become_messages(tmp_path):
    ivm = ImportViewModel(DataService(), ["mass_balance.recovery"])
    assert not ivm.load(tmp_path / "missing.csv") and ivm.error
    assert not ivm.validate() and ivm.error
    f = tmp_path / "d.csv"
    f.write_text("a\n1\n", encoding="utf-8")
    ivm.load(f)
    ivm.choices[0].use, ivm.choices[0].unit = True, "furlong"
    assert not ivm.validate() and "furlong" in (ivm.error or "")


def test_project_flow_compare_report_archive(pvm, ws, tmp_path):
    assert pvm.create(tmp_path / "p", "Pilot")
    assert pvm.add_current("Base")
    ws.set_field("recovery", text="95")
    ws.calculate()
    assert pvm.add_current("Improved")
    ids = [e.id for e in pvm.entries()]
    assert pvm.compare(ids)
    assert any(r.name == "metal_recovered" for r in pvm.comparison.outputs())
    assert pvm.export_comparison(tmp_path / "c.csv")
    assert pvm.export_report(ids, tmp_path / "r.html", author="Eng")
    assert "Base" in (tmp_path / "r.html").read_text(encoding="utf-8")
    assert pvm.export_archive(tmp_path / "p.zip")
    assert pvm.open_in_workspace(ids[0]) and ws.status == "ok"
    assert any("export_report" in line for line in pvm.history_lines())


def test_project_errors_are_messages_not_exceptions(pvm, tmp_path):
    assert not pvm.add_current("x") and "project" in pvm.error.lower()
    pvm.create(tmp_path / "p", "A")
    assert not pvm.create(tmp_path / "p", "B")  # already a project
    assert not pvm.export_report([], tmp_path / "r.html") and "at least one" in pvm.error
    assert not pvm.compare([1]) and pvm.error  # needs two


def test_add_with_uncertainty_keeps_it(ws, pvm, tmp_path):
    from metallurgypy_studio.services.calculation_service import FieldInput

    ws.set_field("feed_mass", uncertainty="5")
    ws.calculate()
    pvm.create(tmp_path / "p", "A")
    assert pvm.add_current("u")
    assert pvm.project.load_calculation(1).uncertainty is not None
