import pytest

from metallurgypy.comparison import compare, comparison_to_csv
from metallurgypy.core import Quantity
from metallurgypy.data_io import ColumnMapping, import_table, read_table, write_rejected_csv
from metallurgypy.records import csv_safe, result_to_csv
from metallurgypy.registry import get_model


def test_csv_safe_neutralises_formulas_but_not_numbers():
    assert csv_safe("=HYPERLINK(\"x\")") == "'=HYPERLINK(\"x\")"
    assert csv_safe("@SUM(A1)") == "'@SUM(A1)"
    assert csv_safe("-cmd") == "'-cmd"
    assert csv_safe("-5") == "-5" and csv_safe("+1.5e3") == "+1.5e3"
    assert csv_safe("plain") == "plain" and csv_safe("") == ""


def _res(rec=92):
    return get_model("mass_balance.recovery").run(
        {"feed_mass": Quantity(1000, "t"), "feed_grade": Quantity(2.5, "%"), "recovery": Quantity(rec, "%")})


def test_comparison_csv_neutralises_scenario_names():
    text = comparison_to_csv(compare({"=cmd|' /C calc'!A0": _res(), "ok": _res(95)}))
    assert text.splitlines()[0].startswith("section,name,unit,'=cmd")
    assert "\n=" not in text


def test_result_csv_keeps_numbers_intact():
    text = result_to_csv(_res())
    assert "23.0" in text and "'" not in text


def test_rejected_csv_neutralises_raw_cells(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text("m\n=1+1\n", encoding="utf-8")
    rep = import_table(read_table(f), [ColumnMapping("m", "m", "t")])
    out = write_rejected_csv(tmp_path / "r.csv", rep)
    assert "'=1+1" in out.read_text(encoding="utf-8")
