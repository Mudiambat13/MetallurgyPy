# Data, comparison, reports and projects

These tools turn files into validated calculations and calculations into deliverables. All of them are in the Core (no GUI needed) and Studio exposes them in its **Data Import** and **Projects** pages. Examples use fictitious data.

## Import a data file

`read_table` reads `.csv`, `.tsv`, `.txt`, `.json` and `.xlsx` (the last needs `pip install "metallurgypy[excel]"`). It detects the delimiter, and a decimal comma when the delimiter is not a comma. The source file is only read, never modified.

You say what each column means. Units are **never guessed silently**: a numeric column needs an explicit unit.

```python
import tempfile
from pathlib import Path

from metallurgypy.data_io import (
    ColumnMapping,
    import_table,
    read_table,
    run_batch,
    write_rejected_csv,
)

work = Path(tempfile.mkdtemp())
(work / "assays.csv").write_text(
    "sample;mass [t];grade [%];rec [%]\n"
    "A;1000;2,5;92\n"
    "B;900;2,1;90\n"
    "C;800;2,0;91\n"
    "D;700;1,9;89\n"
    "E;abc;1,7;88\n",
    encoding="utf-8",
)

table = read_table(work / "assays.csv")  # delimiter ';' and decimal ',' detected
report = import_table(
    table,
    [
        ColumnMapping("sample", "sample", kind="text"),
        ColumnMapping("mass [t]", "feed_mass", "t", minimum=0.0),
        ColumnMapping("grade [%]", "feed_grade", "%"),
        ColumnMapping("rec [%]", "recovery", "%", maximum=100.0),
    ],
)
print(len(report.rows), "valid;", len(report.rejected), "rejected")
for row in report.rejected:
    print(row.row_number, row.reasons)
```

Rows that cannot be used are **reported with the reason**, never dropped silently. Write them to a new file with `write_rejected_csv(path, report)`.

Run a registered model on every valid row. A failing row gives an error item; the others still run:

```python
items = run_batch("mass_balance.recovery", report.rows)
for item in items:
    print(item.row_number, item.result.get("metal_recovered").value)
```

## Compare scenarios

```python
from metallurgypy.comparison import compare, comparison_to_csv
from metallurgypy.core import Quantity
from metallurgypy.registry import get_model

model = get_model("mass_balance.recovery")


def scenario(recovery):
    return model.run(
        {
            "feed_mass": Quantity(1000, "t"),
            "feed_grade": Quantity(2.5, "%"),
            "recovery": Quantity(recovery, "%"),
        }
    )


comparison = compare({"base": scenario(92), "improved": scenario(95)})
row = next(r for r in comparison.outputs() if r.name == "metal_recovered")
print(row.difference["improved"], row.relative_difference["improved"])
print(comparison_to_csv(comparison).splitlines()[0])
```

Values are converted to the baseline's unit. Inputs identical in every scenario are left out. A quantity with an incompatible unit is flagged, not forced; scenarios from different models or modes get a warning.

## Reports

A report keeps three things apart: **calculated or estimated** values from a model, **observations** you measured (shown as given, never computed), and **uncertainties** (only when propagated). It carries the model, version, equations, assumptions, warnings, date and software version, and a reminder that these are simplified models.

```python
from metallurgypy.reports import ReportEntry, build_report, render_html, write_html

entry = ReportEntry(
    "Base case",
    scenario(92),
    observations={"Plant assay of concentrate": Quantity(24.1, "%")},
    notes="Illustrative data.",
)
document = build_report([entry], title="Pilot study", author="Jane Doe", include_charts=False)
html_text = render_html(document)
assert "Observations (entered by the user" in html_text
write_html(work / "report.html", document)
```

All text is HTML-escaped. Charts are embedded as SVG when the `visualization` extra is installed. `write_pdf` makes a plain text/table PDF (it needs Matplotlib; charts stay in the HTML report).

## Projects

A project is a folder: `project.json` (versioned index), `calculations/` (one `.mpy.json` per calculation) and `history.sqlite` (append-only activity log).

```python
from metallurgypy.projects import Project

project = Project.create(work / "pilot", "Pilot study", "Illustrative project")
entry = project.add_calculation(scenario(92), "Base case", notes="fictitious")
project.add_calculation(scenario(95), "Improved recovery")

reopened = Project.open(work / "pilot")
print([e.name for e in reopened.entries()])
print([h.action for h in reopened.history()])
reopened.export_archive(work / "pilot.zip")
```

Safety rules: file names come from a sanitised slug (never raw user text); an index entry that points outside `calculations/` is refused; removing an entry only unlists it and keeps the file; a project folder is never overwritten.
