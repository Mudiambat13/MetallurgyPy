# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] - 0.1.0.dev0

### Added
- Core: units (mass and dimensionless grades), exception hierarchy, input validation, tolerances, calculation modes (only `standard` implemented; others are refused explicitly), provenance and result objects.
- Mass Balance: `MassBalance` (recovery-based) and `TwoProductBalance` (from the three grades), with documented equations, assumptions, closure checks and tests.
- Model registry with controlled metadata, used by Studio to build forms.
- Calculation records: versioned JSON save/reopen with verification against a fresh calculation, CSV/JSON export, PNG/SVG chart export (optional `visualization` extra).
- MetallurgyPy Studio (PySide6): main window, side navigation, dashboard, module explorer, Mass Balance workspace with generated forms, interactive chart, light/dark theme, settings.
- MkDocs documentation site deployed to GitHub Pages.

### Not yet implemented
- Measurement uncertainty propagation (Phase 3), the other process modules (Phase 5), data import, reports, project manager (Phase 6).
