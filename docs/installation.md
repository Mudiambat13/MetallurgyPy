# Installation

!!! note
    MetallurgyPy has not been published to PyPI. Until the owner approves a release, install from a clone of the repository (development install below).

## Requirements

- Python (the supported versions will be listed in `pyproject.toml` and tested in CI)
- Windows or Linux for Studio; macOS compatibility is kept possible

## Install options

=== "Core only"

    ```bash
    pip install metallurgypy
    ```

    No PySide6 is installed. Suitable for servers and notebooks.

=== "With Studio (GUI)"

    ```bash
    pip install "metallurgypy[gui]"
    metallurgypy-studio
    ```

=== "Optional features"

    ```bash
    pip install "metallurgypy[visualization]"
    pip install "metallurgypy[uncertainty]"
    pip install "metallurgypy[all]"
    ```

## Development install

```bash
git clone https://github.com/Mudiambat13/MetallurgyPy.git
cd MetallurgyPy
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e .                 # Core
pip install -e ".[gui]"          # Core + Studio
pip install -e ".[dev]"          # tests, lint, type checks
```

During development Studio can also be launched with:

```bash
python -m metallurgypy_studio
```

## Build this documentation locally

```bash
pip install -r docs/requirements.txt
mkdocs serve            # live preview at http://127.0.0.1:8000
mkdocs build --strict   # same check as CI
```

## Verify the installation

```bash
python -c "import metallurgypy; print(metallurgypy.__version__)"
```

To confirm that the Core really is GUI-free, check that `PySide6` is absent from a fresh Core-only environment (`pip list`).
