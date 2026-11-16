import csv
import io
import json

import pytest

from metallurgypy.core import InvalidParameterError, Quantity, RecordFormatError
from metallurgypy.mass_balance import MassBalance, TwoProductBalance
from metallurgypy.records import (
    FORMAT_NAME,
    export_result_csv,
    export_result_json,
    load_record,
    recompute,
    result_to_csv,
    save_record,
    verify,
)
from metallurgypy.registry import MODULE_CATALOG, get_model, list_models


@pytest.fixture
def result():
    return MassBalance(Quantity(1234.5, "t"), Quantity(2.37, "%"), Quantity(91.3, "%")).calculate()


# ----------------------------- registry ------------------------------------ #


def test_registry_lists_models_and_modules():
    ids = {m.model_id for m in list_models()}
    assert {"mass_balance.recovery", "mass_balance.two_product"} <= ids
    assert len(ids) == len(list_models()) == 21
    assert len(MODULE_CATALOG) == 9
    assert {m.module_key for m in list_models()} <= {m.key for m in MODULE_CATALOG}
    assert len(list_models("mass_balance")) == 2 and len(list_models("flotation")) == 2
    assert list_models("statistics") == ()  # Python API only: its inputs are series, not scalars
    with pytest.raises(InvalidParameterError, match="Unknown model"):
        get_model("os.system")


@pytest.mark.parametrize("spec", list_models(), ids=lambda s: s.model_id)
def test_every_model_spec_is_consistent_and_its_example_runs(spec):
    names = [p.name for p in spec.parameters]
    assert set(spec.example) == set(names)
    for p in spec.parameters:
        assert p.default_unit in p.units
        assert spec.example[p.name].unit in p.units
    out = spec.run(spec.example)
    assert out.provenance.model_id == spec.model_id
    assert out.provenance.model_version == spec.model_version


def test_spec_run_reports_missing_and_unknown_inputs():
    spec = get_model("mass_balance.recovery")
    with pytest.raises(InvalidParameterError, match="Missing"):
        spec.run({"feed_mass": Quantity(1, "t")})
    with pytest.raises(InvalidParameterError, match="Unknown input"):
        spec.run({**spec.example, "bogus": Quantity(1, "t")})


# ----------------------------- save / reopen -------------------------------- #


def test_save_and_reopen_keeps_exact_values_and_reproduces(tmp_path, result):
    path = save_record(tmp_path / "calc.mpy.json", result, name="Test", notes="é \u2013 note")
    record = load_record(path)
    assert record.name == "Test" and record.notes == "é \u2013 note"
    assert record.model_id == "mass_balance.recovery"
    assert record.inputs == dict(result.provenance.inputs)
    for stored, item in zip(record.result["outputs"], result.outputs(), strict=True):
        assert stored["value"] == item.quantity.value  # bit-for-bit
        assert stored["unit"] == item.quantity.unit
    assert verify(record) == []
    assert recompute(record).metal_recovered == result.metal_recovered


def test_verify_detects_a_tampered_value(tmp_path, result):
    path = save_record(tmp_path / "c.mpy.json", result)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["result"]["outputs"][1]["value"] *= 1.01
    path.write_text(json.dumps(data), encoding="utf-8")
    differences = verify(load_record(path))
    assert len(differences) == 1 and "metal_recovered" in differences[0]


def test_two_product_record_round_trip(tmp_path):
    res = TwoProductBalance(
        1000, Quantity(2, "%"), Quantity(20, "%"), Quantity(0.4, "%")
    ).calculate()
    assert verify(load_record(save_record(tmp_path / "t.mpy.json", res))) == []


def test_save_refuses_to_overwrite_unless_asked(tmp_path, result):
    path = save_record(tmp_path / "c.mpy.json", result)
    with pytest.raises(FileExistsError):
        save_record(path, result)
    save_record(path, result, name="second", overwrite=True)
    assert load_record(path).name == "second"
    assert list(tmp_path.glob("*.tmp")) == []  # no temp files left behind


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("not json", "not valid JSON"),
        ("[]", "not a MetallurgyPy"),
        (json.dumps({"format": "other"}), "not a MetallurgyPy"),
        (json.dumps({"format": FORMAT_NAME, "format_version": 99}), "newer"),
        (json.dumps({"format": FORMAT_NAME, "format_version": 0}), "positive integer"),
        (
            json.dumps({"format": FORMAT_NAME, "format_version": 1, "model_id": "", "result": {}}),
            "model_id",
        ),
        (
            json.dumps(
                {
                    "format": FORMAT_NAME,
                    "format_version": 1,
                    "model_id": "mass_balance.recovery",
                    "result": {"outputs": []},
                    "inputs": {"feed_mass": {"value": 1, "unit": "furlong"}},
                }
            ),
            "invalid",
        ),
    ],
)
def test_malformed_files_are_refused_with_a_clear_error(tmp_path, content, message):
    path = tmp_path / "bad.mpy.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(RecordFormatError, match=message):
        load_record(path)


def test_a_file_cannot_make_the_program_run_arbitrary_code(tmp_path, result):
    path = save_record(tmp_path / "c.mpy.json", result)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["model_id"] = "os.system"
    data["payload"] = "__import__('os').system('echo pwned')"
    path.write_text(json.dumps(data), encoding="utf-8")
    record = load_record(path)  # loading is pure data parsing
    with pytest.raises(InvalidParameterError, match="Unknown model"):
        recompute(record)  # only registered models can run


# -------------------------------- export ----------------------------------- #


def test_csv_export_has_inputs_outputs_and_full_precision(tmp_path, result):
    rows = list(csv.DictReader(io.StringIO(result_to_csv(result))))
    assert [r["section"] for r in rows].count("input") == 3
    by_name = {r["name"]: r for r in rows if r["section"] == "output"}
    assert float(by_name["metal_recovered"]["value"]) == result.metal_recovered.value
    assert by_name["metal_recovered"]["kind"] == "calculated"
    path = export_result_csv(tmp_path / "r.csv", result)
    assert path.read_text(encoding="utf-8").startswith("section,name,label,value,unit,kind")
    with pytest.raises(FileExistsError):
        export_result_csv(path, result)


def test_json_export(tmp_path, result):
    path = export_result_json(tmp_path / "r.json", result)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["provenance"]["model_id"] == "mass_balance.recovery"
    assert data["outputs"][0]["value"] == result.metal_feed.value


# ------------------------------ visualization ------------------------------ #


def test_chart_export_png_and_svg(tmp_path, result):
    pytest.importorskip("matplotlib")
    from metallurgypy.visualization import save_chart

    chart = result.chart_data()
    png = save_chart(chart, tmp_path / "c.png")
    assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    svg = save_chart(chart, tmp_path / "c.svg")
    text = svg.read_text(encoding="utf-8")
    assert "<svg" in text and "MassBalance 1.0" in text  # provenance is printed on the chart
    with pytest.raises(ValueError, match="Unsupported"):
        save_chart(chart, tmp_path / "c.pdf")
    with pytest.raises(FileExistsError):
        save_chart(chart, png)
