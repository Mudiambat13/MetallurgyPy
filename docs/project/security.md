# Security review

This is a self-review of the code in this repository, done by reading and searching the source and by tests. It is **not** an independent audit or a penetration test.

## Threat model

MetallurgyPy is a local library and desktop application. It opens no network connection, runs no server and handles no credentials. The realistic risks are **untrusted files** (a project, calculation or data file received from someone else) and **untrusted text** (names, notes, column headers) that ends up in an exported file.

## What was checked

| Topic | Finding | Evidence |
|---|---|---|
| Code execution from files | None. A calculation file is JSON. Reopening looks the model up by `model_id` in a fixed registry and re-runs it from the stored numbers. | No `eval`, `exec`, `pickle`, `marshal`, `subprocess`, `os.system` or shell use in `src/` or `studio/` (searched). The only dynamic import loads a fixed internal list of model modules. |
| Malformed or hostile calculation / project files | Rejected with a clear `RecordFormatError` / `ProjectError`: wrong format name, newer version, bad types, malformed uncertainty block, invalid JSON. | `tests/integration`, `tests/studio`, `tests/phase6` |
| Path traversal in projects | An index entry pointing outside `calculations/` is refused before reading. File names come from a sanitised slug plus a counter, never from raw text. | `test_project_blocks_path_traversal` |
| Archives | Studio and the Core only **write** zip archives, with fixed relative names. Nothing extracts an archive, so there is no zip-slip path. | `test_project_archive_contents` |
| Overwriting data | Every writer refuses to overwrite an existing file unless `overwrite=True`. Writes are atomic (temporary file then replace). Source data files are only read. | `tests` for each writer |
| SQL | The only SQL is the project history. Values are bound parameters; no SQL is built from user text. | `projects/__init__.py` |
| HTML reports | All user-controlled text is escaped. The only raw markup is the SVG produced by Matplotlib from the result's own labels. | `test_report_html_content_and_escaping` |
| Spreadsheet formula injection | Text cells that start with `=`, `+`, `-` or `@` get a leading apostrophe in exported CSV (numbers are untouched). | `tests/phase6/test_security.py` |
| Non-finite numbers | NaN and infinity are refused on input and when writing JSON. | validation and record tests |
| Logging | Studio logs technical details to the log, not to dialogs. No secrets exist to log. | code review |

## Known limits

- **Excel files.** `.xlsx` is read with `openpyxl` (`read_only`, `data_only`): formulas are not evaluated and macros are not run. A very large or crafted workbook can still use a lot of memory or time. There is no size limit.
- **Large inputs.** CSV and JSON files are read fully into memory. There is no size limit.
- **Dependencies.** The Core has none. Optional extras (Matplotlib, PySide6, pyqtgraph, openpyxl) bring their own risk; keep them updated. No dependency scan (for example `pip-audit`) was run for this review.
- **Studio.** The GUI was never run in the environment where this code was written (no PySide6, no display). Its behaviour is checked by the CI job, not here.
- **Supply chain / release.** Nothing is published to PyPI. A future release needs a trusted-publisher setup and signed tags; that is not configured.
- **Not reviewed:** Qt and PySide6 themselves, the operating system's file dialogs, and the GitHub Actions configuration beyond reading it.

## Reporting a problem

Open a private security advisory on the GitHub repository, or contact the maintainer, rather than a public issue.
