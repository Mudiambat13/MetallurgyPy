"""Studio logic that needs no Qt: services and view models."""

import json
import logging
import subprocess
import sys
from pathlib import Path

import pytest

import metallurgypy_studio.services.calculation_service as service_module
from metallurgypy.mass_balance import MassBalance
from metallurgypy_studio.services.calculation_service import (
    CalculationService,
    FieldInput,
    parse_number,
)
from metallurgypy_studio.viewmodels.app_state import (
    MAX_RECENT,
    AppSettings,
    AppState,
    format_number,
)
from metallurgypy_studio.viewmodels.workspace_viewmodel import ERROR, IDLE, OK, WorkspaceViewModel

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def service():
    return CalculationService()


@pytest.fixture
def vm(service):
    return WorkspaceViewModel(service, AppState())


def _fill(vm, **values):
    for name, (text, unit) in values.items():
        vm.set_field(name, text=text, unit=unit)


# ------------------------------ service ------------------------------------ #


def test_studio_result_equals_core_result_exactly(service):
    outcome = service.run(
        "mass_balance.recovery",
        {
            "feed_mass": FieldInput("1000", "t"),
            "feed_grade": FieldInput("2.5", "%"),
            "recovery": FieldInput("92", "%"),
        },
    )
    assert outcome.ok
    direct = MassBalance(1000, 0.025, 0.92).calculate()
    assert outcome.result.metal_recovered.value == pytest.approx(direct.metal_recovered.value, rel=1e-14)
    assert outcome.result.metal_remaining.value == pytest.approx(2.0, rel=1e-14)


@pytest.mark.parametrize(("text", "expected"), [("2.5", 2.5), ("2,5", 2.5), (" 1 000 ", 1000.0), ("1e3", 1000.0)])
def test_parse_number(text, expected):
    assert parse_number(text) == expected


@pytest.mark.parametrize("bad", ["", "  ", "abc", "1.2.3"])
def test_parse_number_rejects(bad):
    with pytest.raises(ValueError, match=r".*"):
        parse_number(bad)


def test_unparsable_and_missing_fields_are_reported_per_field(service):
    outcome = service.run(
        "mass_balance.recovery",
        {"feed_mass": FieldInput("", "t"), "feed_grade": FieldInput("abc", "%")},
    )
    assert not outcome.ok
    assert set(outcome.field_errors) == {"feed_mass", "feed_grade", "recovery"}
    assert "number" in outcome.field_errors["feed_grade"]
    assert outcome.field_errors["recovery"] == "Required."


def test_model_rejection_is_attached_to_the_named_field(service):
    outcome = service.run(
        "mass_balance.recovery",
        {
            "feed_mass": FieldInput("1000", "t"),
            "feed_grade": FieldInput("2.5", "%"),
            "recovery": FieldInput("120", "%"),
        },
    )
    assert not outcome.ok and set(outcome.field_errors) == {"recovery"}
    assert "0 to 1" in outcome.field_errors["recovery"]


def test_domain_error_is_a_general_message(service):
    outcome = service.run(
        "mass_balance.two_product",
        {
            "feed_mass": FieldInput("100", "t"),
            "feed_grade": FieldInput("10", "%"),
            "concentrate_grade": FieldInput("30", "%"),
            "tailings_grade": FieldInput("30", "%"),
        },
    )
    assert outcome.error and "equal" in outcome.error and not outcome.field_errors


def test_unknown_model_and_unexpected_errors_are_contained(service, monkeypatch, caplog):
    assert "Unknown model" in service.run("nope", {}).error

    class Boom:
        parameters = ()

        def run(self, inputs):
            raise RuntimeError("secret technical detail")

    monkeypatch.setattr(service_module, "get_model", lambda _id: Boom())
    with caplog.at_level(logging.ERROR):
        outcome = service.run("anything", {})
    assert "Unexpected internal error" in outcome.error
    assert "secret technical detail" not in outcome.error  # user sees a clean message...
    assert "secret technical detail" in caplog.text  # ...the log keeps the details


def test_module_overview_covers_all_nine_modules_and_marks_availability(service):
    overview = service.module_overview()
    assert len(overview) == 9
    available = {o.info.key for o in overview if o.available}
    assert available == {
        "mass_balance", "reagents", "electrowinning", "flotation", "filtration",
        "hydrometallurgy", "solvent_extraction", "thermodynamics",
    }
    assert {o.info.key for o in overview if not o.available} == {"statistics"}


# ----------------------------- view model ---------------------------------- #


def test_workspace_flow_example_calculate_and_display_rows(vm):
    events = []
    vm.subscribe(lambda: events.append(vm.status))
    assert vm.status == IDLE and vm.rows() == []
    vm.fill_example()
    vm.calculate()
    assert vm.status == OK and events[-1] == OK
    rows = {r.name: r for r in vm.rows()}
    assert rows["metal_recovered"].value_text == "23" and rows["metal_recovered"].unit == "t"
    assert rows["metal_recovered"].kind == "calculated"
    assert vm.assumptions and "Recovery" in " ".join(vm.assumptions)
    assert "mass_balance.recovery" in vm.details_text()


def test_display_precision_never_changes_stored_values(vm):
    _fill(vm, feed_mass=("1", "t"), feed_grade=("33.333333333333", "%"), recovery=("14.285714285714", "%"))
    vm.calculate()
    exact = vm.result.metal_feed.value
    vm._state.settings.display_digits = 3
    short = {r.name: r.value_text for r in vm.rows()}["metal_feed"]
    vm._state.settings.display_digits = 12
    long = {r.name: r.value_text for r in vm.rows()}["metal_feed"]
    assert len(short) < len(long)
    assert vm.result.metal_feed.value == exact  # engine value untouched


def test_error_path_sets_status_and_keeps_messages(vm):
    vm.calculate()  # nothing entered
    assert vm.status == ERROR and set(vm.field_errors) == {p.name for p in vm.spec.parameters}
    assert vm.result is None and vm.rows() == []


def test_switching_model_resets_form_and_result(vm):
    vm.fill_example()
    vm.calculate()
    vm.select_model("mass_balance.two_product")
    assert vm.status == IDLE and vm.result is None
    assert set(vm.fields) == {"feed_mass", "feed_grade", "concentrate_grade", "tailings_grade"}
    assert all(f.text == "" for f in vm.fields.values())


def test_async_path_equals_sync_path(vm, service):
    vm.fill_example()
    model_id, fields, correlations = vm.prepare_run()
    assert vm.status == "running"
    vm.apply_outcome(service.run(model_id, fields, correlations))
    assert vm.status == OK


def test_save_and_reopen_through_the_view_model(vm, service, tmp_path):
    vm.fill_example()
    vm.name, vm.notes = "Demo", "illustrative data"
    vm.calculate()
    path = vm.save(tmp_path / "demo.mpy.json")
    assert str(path) in vm._state.settings.recent_files
    with pytest.raises(FileExistsError):
        vm.save(path)

    other = WorkspaceViewModel(service, AppState())
    other.select_model("mass_balance.two_product")
    opened = other.open_file(path)
    assert other.spec.model_id == "mass_balance.recovery" and other.status == OK
    assert other.notes == "illustrative data" and other.name == "Demo"
    assert other.fields == vm.fields
    assert opened.differences == () and other.differences == ()
    assert other.result.metal_recovered.value == vm.result.metal_recovered.value


def test_reopening_flags_a_tampered_file(vm, tmp_path):
    vm.fill_example()
    vm.calculate()
    path = vm.save(tmp_path / "t.mpy.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["result"]["outputs"][0]["value"] += 1.0
    path.write_text(json.dumps(data), encoding="utf-8")
    other = WorkspaceViewModel(CalculationService(), AppState())
    other.open_file(path)
    assert other.differences and "metal_feed" in other.differences[0]


def test_exports_require_a_result_and_refuse_overwrite(vm, tmp_path):
    with pytest.raises(ValueError, match="no result"):
        vm.export_csv(tmp_path / "x.csv")
    vm.fill_example()
    vm.calculate()
    csv_path = vm.export_csv(tmp_path / "x.csv")
    json_path = vm.export_json(tmp_path / "x.json")
    assert csv_path.exists() and json_path.exists()
    with pytest.raises(FileExistsError):
        vm.export_csv(csv_path)


# ------------------------------ settings ----------------------------------- #


def test_settings_round_trip_and_tolerant_loading(tmp_path):
    path = tmp_path / "cfg" / "settings.json"
    s = AppSettings(theme="dark", display_digits=9, default_folder="/data")
    s.add_recent("a")
    s.save(path)
    assert AppSettings.load(path) == s
    path.write_text('{"theme": "neon", "display_digits": 99, "recent_files": [1, "ok"]}', encoding="utf-8")
    loaded = AppSettings.load(path)
    assert loaded.theme == "light" and loaded.display_digits == 6 and loaded.recent_files == ["ok"]
    path.write_text("garbage", encoding="utf-8")
    assert AppSettings.load(path) == AppSettings()
    assert AppSettings.load(tmp_path / "missing.json") == AppSettings()


def test_recent_files_are_deduplicated_and_capped():
    s = AppSettings()
    for i in range(MAX_RECENT + 5):
        s.add_recent(f"f{i}")
    s.add_recent("f12")
    assert len(s.recent_files) == MAX_RECENT and s.recent_files[0] == "f12"
    assert s.recent_files.count("f12") == 1


@pytest.mark.parametrize(
    ("value", "digits", "expected"),
    [
        (0.0, 6, "0"),
        (23.0, 6, "23"),
        (1000.0, 3, "1000"),
        (1234.5, 3, "1234"),  # integer digits are never dropped (1234.5 rounds half to even)
        (0.025, 6, "0.025"),
        (1 / 3, 6, "0.333333"),
        (1e-9, 6, "1e-09"),
        (-0.0004567, 3, "-0.000457"),
    ],
)
def test_format_number(value, digits, expected):
    assert format_number(value, digits) == expected


# ------------------------- dependency boundaries --------------------------- #


def _run_python(code: str) -> subprocess.CompletedProcess[str]:
    env = {"PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'studio'}", "PATH": "/usr/bin:/bin"}
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, check=False)


def test_core_imports_without_gui_or_plotting_libraries():
    proc = _run_python(
        "import sys, metallurgypy.mass_balance, metallurgypy.records, metallurgypy.registry;"
        "bad=[m for m in sys.modules if m.split('.')[0] in ('PySide6','matplotlib','numpy','pandas','pyqtgraph')];"
        "assert not bad, bad"
    )
    assert proc.returncode == 0, proc.stderr


def test_studio_logic_layers_import_without_qt():
    proc = _run_python(
        "import sys, metallurgypy_studio.viewmodels.workspace_viewmodel;"
        "assert 'PySide6' not in sys.modules"
    )
    assert proc.returncode == 0, proc.stderr


# --------------------------- uncertainty in Studio -------------------------- #

_UNC_FIELDS = {
    "feed_mass": FieldInput("1000", "t", "5"),
    "feed_grade": FieldInput("2.5", "%", "0.05"),
    "recovery": FieldInput("92", "%"),
}


def test_run_with_uncertainty_propagates_and_keeps_nominal(service):
    plain = service.run("mass_balance.recovery", {k: FieldInput(v.text, v.unit) for k, v in _UNC_FIELDS.items()})
    outcome = service.run("mass_balance.recovery", _UNC_FIELDS)
    assert outcome.ok and outcome.uncertain is not None
    assert outcome.result.metal_recovered.value == pytest.approx(plain.result.metal_recovered.value, rel=1e-14)
    u = outcome.uncertain.outputs["metal_recovered"].standard_uncertainty
    # metal = m * g * R: relative variances add (first-order)
    expected_rel = ((5 / 1000) ** 2 + (0.05 / 2.5) ** 2) ** 0.5
    assert u / outcome.result.metal_recovered.value == pytest.approx(expected_rel, rel=1e-4)


def test_negative_or_bad_uncertainty_is_a_field_error(service):
    for bad in ("-1", "abc"):
        fields = dict(_UNC_FIELDS)
        fields["feed_mass"] = FieldInput("1000", "t", bad)
        outcome = service.run("mass_balance.recovery", fields)
        assert not outcome.ok and "feed_mass" in outcome.field_errors


def test_viewmodel_shows_uncertainty_column_and_budget(vm):
    vm.select_model("mass_balance.recovery")
    for name, f in _UNC_FIELDS.items():
        vm.set_field(name, text=f.text, unit=f.unit, uncertainty=f.uncertainty)
    vm.calculate()
    assert vm.status == OK
    assert any(r.uncertainty_text not in ("", "0") for r in vm.rows())
    budget = vm.uncertainty_budget_text()
    assert "of the variance" in budget and "feed_mass" in budget
    assert "Uncertainty budget" in vm.details_text()


def test_viewmodel_without_uncertainty_has_empty_column(vm):
    vm.select_model("mass_balance.recovery")
    vm.fill_example()
    vm.calculate()
    assert all(r.uncertainty_text == "" for r in vm.rows())
    assert vm.uncertainty_budget_text() == ""


def test_uncertainty_survives_save_and_reopen(service, tmp_path):
    outcome = service.run("mass_balance.recovery", _UNC_FIELDS)
    path = service.save(tmp_path / "unc.mpy.json", outcome.result, uncertain=outcome.uncertain)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["uncertainty"]["inputs"]["feed_mass"]["uncertainty"] == 5.0
    opened = service.open(path)
    assert opened.differences == ()
    again = opened.outcome.uncertain
    assert again is not None
    assert again.outputs["metal_recovered"].standard_uncertainty == pytest.approx(
        outcome.uncertain.outputs["metal_recovered"].standard_uncertainty, rel=1e-12
    )


def test_reopening_in_viewmodel_restores_uncertainty_fields(vm, service, tmp_path):
    outcome = service.run("mass_balance.recovery", _UNC_FIELDS)
    path = service.save(tmp_path / "u.mpy.json", outcome.result, uncertain=outcome.uncertain)
    vm.open_file(path)
    assert vm.fields["feed_mass"].uncertainty not in ("", "0.0")
    assert vm.uncertain is not None


def test_record_without_uncertainty_still_loads(service, tmp_path):
    outcome = service.run("mass_balance.recovery", {k: FieldInput(v.text, v.unit) for k, v in _UNC_FIELDS.items()})
    path = service.save(tmp_path / "plain.mpy.json", outcome.result)
    opened = service.open(path)
    assert opened.record.uncertainty is None and opened.outcome.uncertain is None


def test_malformed_uncertainty_block_is_rejected(service, tmp_path):
    from metallurgypy.core import RecordFormatError
    from metallurgypy.records import load_record

    outcome = service.run("mass_balance.recovery", _UNC_FIELDS)
    path = service.save(tmp_path / "bad.mpy.json", outcome.result, uncertain=outcome.uncertain)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["uncertainty"] = "oops"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RecordFormatError):
        load_record(path)
