"""The Python examples in the tutorials and guides are executed, so they cannot rot."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PAGES = ["docs/tutorials/uncertainty.md", "docs/tutorials/first_mass_balance.md", "docs/guides/workflows.md",
         "docs/scientific_methods/statistics.md"]
FENCE = re.compile(r"```python\n(.*?)```", re.S)


@pytest.mark.parametrize("page", PAGES)
def test_python_blocks_run(page, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    namespace: dict = {"__name__": "doc_snippet"}
    source = (ROOT / page).read_text(encoding="utf-8")
    blocks = FENCE.findall(source)
    assert blocks, f"no python block in {page}"
    for i, block in enumerate(blocks, 1):
        if "# not run" in block:
            continue
        try:
            exec(compile(block, f"{page}#block{i}", "exec"), namespace)
        except Exception as exc:  # report which block failed
            raise AssertionError(f"{page}, block {i} failed: {exc!r}") from exc


def test_generated_model_pages_are_up_to_date():
    import subprocess
    import sys

    done = subprocess.run([sys.executable, str(ROOT / "tools" / "gen_model_reference.py"), "--check"],
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
