# Security policy

MetallurgyPy is a development release. Nothing is published on PyPI.

## Reporting a vulnerability

Please **do not** open a public issue for a security problem. Use GitHub's private
vulnerability reporting on the repository (Security tab → *Report a vulnerability*), or
contact the maintainer through the GitHub profile (Mudiambat13). Include the version,
the file or input that triggers the problem and the observed effect.

## What is in scope

- Reading untrusted files (`*.mpy.json` calculation files, CSV/JSON/XLSX imports, project folders).
- Writing files (overwrite protection, path handling, spreadsheet formula injection in CSV).
- HTML reports (escaping of user text).

See [docs/project/security.md](docs/project/security.md) for the design rules and the
open limitations.

## Out of scope

Scientific correctness of a model for a particular plant is not a security matter; see the
[scientific audit](docs/project/scientific_audit.md).
