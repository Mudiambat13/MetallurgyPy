# Roadmap

Work is delivered by phase. The repository stays in a working state after each one, and a feature is only called finished once it has been run and verified.

| Phase | Scope | Deliverable |
|---|---|---|
| 0. Design | Confirm APIs, versions, unit conventions, first scientific specifications | Approved architecture, initial repository |
| 1. Core foundation (**done**) | Packaging, units, validation, exceptions, results, provenance, tests | Installable minimal Core |
| 2. First calculators (**done**) | Mass Balance, Reagents, reference cases, examples, docs | Usable, tested calculations |
| 3. Precision and uncertainty (**done**) | `Measurement`, propagation, tolerances, sensitivity analysis | Calculations with documented uncertainty |
| 4. Studio MVP (**implemented, not yet run on a real display**) | Main window, side navigation, dashboard, Mass Balance workspace, results and charts, light/dark theme, save a calculation | Desktop app with Mass Balance |
| 5. Metallurgical processes (**done**) | Hydrometallurgy, solvent extraction, electrowinning, flotation, filtration, advanced reagents | Tested modules available in Studio |
| 6. Visualization and reports (**done**, GUI part not run on a display) | CSV/XLSX import, scenario comparison, advanced charts, PDF/HTML reports, project management | Complete scientific workspace |
| 7. Stabilization, 1.0 (**in progress**: audit and security notes written; expert review, real-data validation and CI runs still missing) | Scientific and software audit, cross-platform tests, security review, packaging | Release candidate; publication only after explicit approval |

## MVP acceptance criteria

The MVP is accepted only if all of these hold:

1. The Core installs without PySide6.
2. The `[gui]` install provides the desktop application.
3. The Mass Balance engine works from Python.
4. The same calculation works from Studio.
5. Units are checked.
6. Input errors are explained.
7. Results keep their internal precision.
8. Assumptions and warnings are visible.
9. Results can be visualized and exported.
10. A calculation can be saved and reopened.
11. Automated tests pass.
12. Documentation explains the equations and limits.

## Publication policy

No PyPI release happens without the owner's explicit approval.
