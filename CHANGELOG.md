# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] - 0.2.0.dev0

### Added
- Phase 3: `Measurement`, GUM first-order uncertainty propagation with correlations, Monte Carlo cross-check, sensitivity analysis, significant-figure formatting, exact-arithmetic `high_precision` mode for Mass Balance. Uncertainties are stored in calculation files and shown in Studio (standard-uncertainty column and budget).
- Phase 5: reagents, electrowinning, flotation, filtration, hydrometallurgy, solvent extraction, thermodynamics and statistics (21 registered models).
- Phase 6: tabular import (CSV/JSON/optional XLSX) with row-level rejection report, scenario comparison, HTML/PDF reports, project manager, and the matching Studio views.
- Phase 7: scientific audit and security notes, SECURITY.md, CODE_OF_CONDUCT.md, one documentation page per module.

### Changed
- Uniform unit convention: grades, recoveries and efficiencies are fractions when given as bare numbers.
- `uncertainty` extra replaced by `excel` (optional `openpyxl`).

## 0.1.0.dev0 (previous snapshot)

### Added
- Core: units (mass and dimensionless grades), exception hierarchy, input validation, tolerances, calculation modes (only `standard` implemented; others are refused explicitly), provenance and result objects.
- Mass Balance: `MassBalance` (recovery-based) and `TwoProductBalance` (from the three grades), with documented equations, assumptions, closure checks and tests.
- Model registry with controlled metadata, used by Studio to build forms.
- Calculation records: versioned JSON save/reopen with verification against a fresh calculation, CSV/JSON export, PNG/SVG chart export (optional `visualization` extra).
- MetallurgyPy Studio (PySide6): main window, side navigation, dashboard, module explorer, Mass Balance workspace with generated forms, interactive chart, light/dark theme, settings.
- MkDocs documentation site deployed to GitHub Pages.

### Not yet implemented
- Measurement uncertainty propagation (Phase 3), the other process modules (Phase 5), data import, reports, project manager (Phase 6).
