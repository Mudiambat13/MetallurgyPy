# MetallurgyPy Studio

Studio is the desktop application built on the Core. It targets Windows and Linux, with macOS compatibility kept possible.

!!! info "Status"
    Implemented in this version: main window, side navigation, dashboard, module explorer, the **Calculation Workspace** (Mass Balance), interactive chart, save/reopen, CSV/JSON export, PNG/SVG chart export, light/dark theme and settings. Not yet implemented: Results Explorer comparison, Data Import, Project Manager, Report Builder, PDF/HTML reports. Those sections below describe the target design.

```bash
pip install "metallurgypy[gui]"
metallurgypy-studio
```

## Technology

PySide6 (Qt), pyqtgraph for interactive charts, Matplotlib for publication-quality export, Pandas for tables.

## Screens

| Screen | Purpose |
|---|---|
| **Dashboard** | Version, quick access to modules, recent projects and calculations, calculation task status. Shows real project data only, never fake industrial statistics |
| **Module Explorer** | The scientific modules, with description, available models and a link to the documentation |
| **Calculation Workspace** | Pick a model, fill a generated form with explicit units, validate, calculate, read results, warnings and assumptions, save |
| **Results Explorer** | Numbers, tables, charts, uncertainties, scenario comparison, calculation details, export (CSV, JSON, Excel, PDF) |
| **Scientific Visualization** | Zoom/pan, coordinates, legends, series and unit selection, PNG and SVG export, underlying data export, data provenance |
| **Data Import** | CSV, XLSX, JSON with preview, separator choice, column mapping, type detection, units, validation and an invalid-rows report |
| **Project Manager** | Create, open, save, notes, scenario comparison, project archive export |
| **Report Builder** | PDF and HTML reports, plus CSV/Excel data |
| **Settings** | Language, light/dark theme, display precision, default units, project location, export preferences, tolerances |

## Honest-display rules

- Calculated, estimated and measured values are visually distinguished.
- Units are always shown next to values.
- Assumptions and warnings are visible next to results, not hidden in logs.
- No curve or data point is invented. Example data is labelled fictitious or educational.
- Display precision never alters the stored values.
- Source files are never overwritten without confirmation.
- Imported project files are data: they cannot run Python code.

## Projects

Projects use a versioned, documented and migratable format. SQLite holds metadata and history; large tables can be stored separately.
