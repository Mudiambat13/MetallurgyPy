import json
import sqlite3
import zipfile

import pytest

from metallurgypy.comparison import compare, comparison_to_csv, export_comparison_csv
from metallurgypy.core import InvalidParameterError, Quantity
from metallurgypy.precision import Measurement, propagate_model
from metallurgypy.projects import Project, ProjectError
from metallurgypy.registry import get_model
from metallurgypy.reports import ReportEntry, build_report, render_html, write_html, write_pdf


def _run(mass=1000.0, rec=0.92):
    return get_model("mass_balance.recovery").run(
        {
            "feed_mass": Quantity(mass, "t"),
            "feed_grade": Quantity(0.025, "fraction"),
            "recovery": Quantity(rec, "fraction"),
        }
    )


# ------------------------------ comparison ---------------------------------- #


def test_compare_differences_against_baseline():
    c = compare({"base": _run(), "better": _run(rec=0.95)})
    row = next(r for r in c.outputs() if r.name == "metal_recovered")
    assert row.difference["better"] == pytest.approx(1000 * 0.025 * 0.03)
    assert row.relative_difference["better"] == pytest.approx(0.03 / 0.92)
    assert row.difference["base"] is None
    names = [r.name for r in c.inputs()]
    assert names == ["recovery"]  # identical inputs are left out


def test_compare_converts_units_and_validates():
    other = get_model("mass_balance.recovery").run(
        {
            "feed_mass": Quantity(1_000_000.0, "kg"),
            "feed_grade": Quantity(2.5, "%"),
            "recovery": Quantity(92.0, "%"),
        }
    )
    c = compare({"a": _run(), "b": other})
    row = next(r for r in c.outputs() if r.name == "metal_recovered")
    assert row.difference["b"] == pytest.approx(0.0, abs=1e-9)
    with pytest.raises(InvalidParameterError):
        compare({"only": _run()})
    with pytest.raises(InvalidParameterError):
        compare({"a": _run(), "b": _run()}, baseline="zzz")


def test_compare_flags_different_models_and_exports(tmp_path):
    spec = get_model("reagents.dilution")
    flot = spec.run(dict(spec.example))
    c = compare({"a": _run(), "b": flot})
    assert any("different models" in w for w in c.warnings)
    csv_text = comparison_to_csv(compare({"a": _run(), "b": _run(rec=0.9)}))
    assert csv_text.splitlines()[0].startswith("section,name,unit,a,b")
    p = export_comparison_csv(tmp_path / "c.csv", compare({"a": _run(), "b": _run(rec=0.9)}))
    assert p.exists()
    with pytest.raises(FileExistsError):
        export_comparison_csv(p, compare({"a": _run(), "b": _run(rec=0.9)}))


# -------------------------------- reports ----------------------------------- #


def test_report_html_content_and_escaping(tmp_path):
    entry = ReportEntry(
        "Scenario <b>1</b>",
        _run(),
        observations={"Assay <script>": Quantity(2.4, "%")},
        notes="a & b",
    )
    doc = build_report([entry], title="T <i>", author="Eng & Co")
    html_text = render_html(doc)
    assert "<script>" not in html_text and "&lt;script&gt;" in html_text
    assert "a &amp; b" in html_text and "Eng &amp; Co" in html_text
    assert "not a validated" in html_text  # the disclaimer
    assert "Observations (entered by the user" in html_text
    assert "calculated" in html_text and "Equations" in html_text and "Assumptions" in html_text
    out = write_html(tmp_path / "r.html", doc)
    assert out.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
    with pytest.raises(FileExistsError):
        write_html(out, doc)


def test_report_with_uncertainty_column():
    m = {
        "feed_mass": Measurement(1000, "t", 5),
        "feed_grade": Measurement(2.5, "%", 0.05),
        "recovery": Measurement(92, "%"),
    }
    u = propagate_model("mass_balance.recovery", m)
    doc = build_report([ReportEntry("S", u.nominal, uncertain=u)], include_charts=False)
    assert "Standard uncertainty" in render_html(doc)


def test_report_needs_entries_and_charts_are_inline_svg():
    with pytest.raises(InvalidParameterError):
        build_report([])
    pytest.importorskip("matplotlib")
    assert "<svg" in render_html(build_report([ReportEntry("S", _run())]))


def test_report_pdf(tmp_path):
    pytest.importorskip("matplotlib")
    out = write_pdf(
        tmp_path / "r.pdf", build_report([ReportEntry("S", _run())], include_charts=False)
    )
    assert out.read_bytes().startswith(b"%PDF")


# ------------------------------- projects ----------------------------------- #


def test_project_lifecycle(tmp_path):
    p = Project.create(tmp_path / "proj", "Pilot plant", "desc")
    e1 = p.add_calculation(_run(), "Base case / v1")
    e2 = p.add_calculation(_run(rec=0.9), "Base case / v1")  # same name -> unique file
    assert e1.file != e2.file and e1.file.startswith("calculations/")
    assert "/" not in e1.file.split("/", 1)[1]

    again = Project.open(tmp_path / "proj")
    assert again.name == "Pilot plant" and [e.id for e in again.entries()] == [1, 2]
    rec = again.load_calculation(2)
    assert rec.model_id == "mass_balance.recovery"
    actions = [h.action for h in again.history()]
    assert actions == ["create", "add_calculation", "add_calculation"]

    again.remove_entry(1)
    assert [e.id for e in again.entries()] == [2]
    assert (tmp_path / "proj" / e1.file).exists()  # file kept
    assert again.history()[-1].action == "remove_entry"


def test_project_refuses_overwrite_and_bad_input(tmp_path):
    Project.create(tmp_path / "p", "A")
    with pytest.raises(ProjectError):
        Project.create(tmp_path / "p", "B")
    (tmp_path / "full").mkdir()
    (tmp_path / "full" / "x.txt").write_text("x")
    with pytest.raises(ProjectError):
        Project.create(tmp_path / "full", "B")
    with pytest.raises(ProjectError):
        Project.create(tmp_path / "q", "  ")
    with pytest.raises(ProjectError):
        Project.open(tmp_path / "nothing")


def test_project_blocks_path_traversal(tmp_path):
    p = Project.create(tmp_path / "p", "A")
    p.add_calculation(_run(), "x")
    index = tmp_path / "p" / "project.json"
    data = json.loads(index.read_text(encoding="utf-8"))
    data["calculations"][0]["file"] = "../../etc/passwd"
    index.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ProjectError, match="outside"):
        Project.open(tmp_path / "p").load_calculation(1)


def test_project_rejects_newer_or_malformed_index(tmp_path):
    Project.create(tmp_path / "p", "A")
    index = tmp_path / "p" / "project.json"
    data = json.loads(index.read_text(encoding="utf-8"))
    data["format_version"] = 99
    index.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ProjectError, match="newer"):
        Project.open(tmp_path / "p")
    index.write_text("{", encoding="utf-8")
    with pytest.raises(ProjectError, match="JSON"):
        Project.open(tmp_path / "p")


def test_project_archive_contents(tmp_path):
    p = Project.create(tmp_path / "p", "A")
    p.add_calculation(_run(), "one")
    arc = p.export_archive(tmp_path / "a.zip")
    names = set(zipfile.ZipFile(arc).namelist())
    assert {"project.json", "history.sqlite"} <= names
    assert any(n.startswith("calculations/") for n in names)
    assert all(".." not in n and not n.startswith("/") for n in names)
    with pytest.raises(FileExistsError):
        p.export_archive(arc)


def test_project_history_is_sqlite_and_logs_events(tmp_path):
    p = Project.create(tmp_path / "p", "A")
    p.log_event("export_report", "r.html")
    with sqlite3.connect(tmp_path / "p" / "history.sqlite") as db:
        assert (
            db.execute("SELECT COUNT(*) FROM events WHERE action='export_report'").fetchone()[0]
            == 1
        )


def test_project_stores_uncertainty_with_calculation(tmp_path):
    m = {
        "feed_mass": Measurement(1000, "t", 5),
        "feed_grade": Measurement(2.5, "%"),
        "recovery": Measurement(92, "%"),
    }
    u = propagate_model("mass_balance.recovery", m)
    p = Project.create(tmp_path / "p", "A")
    e = p.add_calculation(u.nominal, "with u", uncertain=u)
    assert p.load_calculation(e.id).uncertainty is not None
