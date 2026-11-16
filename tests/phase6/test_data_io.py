import json

import pytest

from metallurgypy.data_io import (
    ColumnMapping,
    DataImportError,
    detect_column_types,
    guess_unit,
    import_table,
    read_table,
    run_batch,
    write_rejected_csv,
)

MAP = [
    ColumnMapping("sample", "sample", kind="text"),
    ColumnMapping("mass", "feed_mass", "t", minimum=0.0),
    ColumnMapping("grade", "feed_grade", "%"),
    ColumnMapping("rec", "recovery", "%", maximum=100.0),
]


def test_csv_comma_delimiter_and_dot_decimal(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("sample,mass,grade,rec\nA,1000,2.5,92\nB,500,1.8,88.5\n", encoding="utf-8")
    t = read_table(f)
    assert t.delimiter == "," and t.decimal == "."
    rep = import_table(t, MAP)
    assert len(rep.rows) == 2 and not rep.rejected
    assert rep.rows[1].values["feed_grade"].value == 1.8


def test_semicolon_and_decimal_comma(tmp_path):
    f = tmp_path / "fr.csv"
    f.write_text("sample;mass;grade;rec\nA;1000,5;2,5;92\n", encoding="utf-8")
    t = read_table(f)
    assert t.delimiter == ";" and t.decimal == ","
    rep = import_table(t, MAP)
    assert rep.rows[0].values["feed_mass"].value == 1000.5
    assert rep.rows[0].values["feed_grade"].value == 2.5


def test_bad_rows_are_reported_not_dropped(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text(
        "sample,mass,grade,rec\nA,1000,2.5,92\nB,abc,1.8,88\nC,-5,1,90\nD,100,2,120\nE,10,,50\n",
        encoding="utf-8",
    )
    rep = import_table(read_table(f), MAP)
    assert [r.row_number for r in rep.rows] == [1]
    assert [r.row_number for r in rep.rejected] == [2, 3, 4, 5]
    assert rep.total == 5 and rep.warnings
    assert "not a valid number" in rep.rejected[0].reasons[0]
    assert "below the minimum" in rep.rejected[1].reasons[0]
    assert "above the maximum" in rep.rejected[2].reasons[0]
    assert "missing" in rep.rejected[3].reasons[0]


def test_numeric_column_requires_unit_and_known_unit(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("mass\n1\n", encoding="utf-8")
    t = read_table(f)
    with pytest.raises(DataImportError, match="unit"):
        import_table(t, [ColumnMapping("mass", "m")])
    with pytest.raises(DataImportError):
        import_table(t, [ColumnMapping("mass", "m", "furlong")])
    with pytest.raises(DataImportError, match="not in the file"):
        import_table(t, [ColumnMapping("nope", "m", "t")])


def test_duplicate_headers_and_unknown_suffix(tmp_path):
    f = tmp_path / "d.csv"
    f.write_text("a,a\n1,2\n", encoding="utf-8")
    with pytest.raises(DataImportError):
        read_table(f)
    g = tmp_path / "x.dat"
    g.write_text("a", encoding="utf-8")
    with pytest.raises(DataImportError, match="Unsupported"):
        read_table(g)
    with pytest.raises(DataImportError):
        read_table(tmp_path / "missing.csv")


def test_json_both_shapes(tmp_path):
    a = tmp_path / "a.json"
    a.write_text(json.dumps([{"mass": 1, "grade": 2}, {"mass": 3, "grade": 4}]), encoding="utf-8")
    assert read_table(a).columns == ("mass", "grade")
    b = tmp_path / "b.json"
    b.write_text(json.dumps({"columns": ["x"], "rows": [[1], [2]]}), encoding="utf-8")
    assert len(read_table(b).rows) == 2
    c = tmp_path / "c.json"
    c.write_text("[1,2]", encoding="utf-8")
    with pytest.raises(DataImportError):
        read_table(c)


def test_xlsx_roundtrip(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["sample", "mass", "grade", "rec"])
    ws.append(["A", 1000, 2.5, 92])
    f = tmp_path / "a.xlsx"
    wb.save(f)
    rep = import_table(read_table(f), MAP)
    assert rep.rows[0].values["feed_mass"].value == 1000.0


def test_detect_types_and_guess_unit(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("name,mass\nA,1\nB,2\n", encoding="utf-8")
    assert detect_column_types(read_table(f)) == {"name": "text", "mass": "number"}
    assert guess_unit("Cu grade [%]") == "%"
    assert guess_unit("Mass (t)") == "t"
    assert guess_unit("Mass (parsecs)") is None
    assert guess_unit("Mass") is None


def test_source_file_is_never_modified_and_rejected_report(tmp_path):
    f = tmp_path / "s.csv"
    text = "sample,mass,grade,rec\nA,x,2.5,92\n"
    f.write_text(text, encoding="utf-8")
    rep = import_table(read_table(f), MAP)
    out = write_rejected_csv(tmp_path / "rej.csv", rep)
    assert f.read_text(encoding="utf-8") == text
    assert "not a valid number" in out.read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_rejected_csv(out, rep)


def test_run_batch_isolates_failures(tmp_path):
    f = tmp_path / "b.csv"
    f.write_text("sample,mass,grade,rec\nA,1000,2.5,92\nB,500,1.8,88\n", encoding="utf-8")
    rep = import_table(read_table(f), MAP)
    items = run_batch("mass_balance.recovery", rep.rows)
    assert all(i.result is not None for i in items)
    assert items[0].result.get("metal_recovered").value == pytest.approx(1000 * 0.025 * 0.92)
    # a row missing a parameter fails alone
    from metallurgypy.core import Quantity
    from metallurgypy.data_io import ImportedRow

    broken = ImportedRow(9, {"feed_mass": Quantity(1.0, "t")})
    mixed = run_batch("mass_balance.recovery", [rep.rows[0], broken])
    assert mixed[0].result is not None and mixed[1].error


def test_one_typo_does_not_turn_numeric_column_into_text(tmp_path):
    f = tmp_path / "t.csv"
    f.write_text("m\n1\n2\n3\n4\nx\n", encoding="utf-8")
    assert detect_column_types(read_table(f)) == {"m": "number"}
    g = tmp_path / "u.csv"
    g.write_text("m\na\nb\n1\n", encoding="utf-8")
    assert detect_column_types(read_table(g)) == {"m": "text"}
