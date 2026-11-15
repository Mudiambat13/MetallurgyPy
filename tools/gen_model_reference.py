"""Fill the generated "Models" section of each scientific page from the model registry.

The equations, assumptions, parameters and example values shown in the documentation
are read from the code, so the documentation cannot drift from the implementation.

    python tools/gen_model_reference.py           # rewrite the pages
    python tools/gen_model_reference.py --check   # exit 1 if a page is out of date
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from metallurgypy.registry import list_models  # noqa: E402

PAGES = ("flotation", "filtration", "hydrometallurgy", "solvent_extraction", "thermodynamics")
DOCS = ROOT / "docs" / "scientific_methods"
BEGIN, END = "<!-- BEGIN GENERATED MODELS -->", "<!-- END GENERATED MODELS -->"


def render_models(module_key: str) -> str:
    out: list[str] = []
    for spec in list_models(module_key):
        result = spec.run(dict(spec.example))
        prov = result.provenance
        out += [f"### {spec.title}", "", f"`{spec.model_id}` · model version {spec.model_version}", "", spec.description, ""]
        out += ["| Parameter | Meaning | Default unit |", "|---|---|---|"]
        for p in spec.parameters:
            out.append(f"| `{p.name}` | {p.label}. {p.description} | {p.default_unit} |")
        out += ["", "**Equations**", "", "```text", *prov.equations, "```", "", "**Assumptions and limits**", ""]
        out += [f"- {a}" for a in prov.assumptions]
        if prov.convergence != "not_applicable":
            out += ["", f"**Numerical method:** {prov.method}."]
        out += ["", "**Illustrative example** (fictional values, not plant data)", ""]
        out += ["| Input | Value | Unit |", "|---|---|---|"]
        out += [f"| `{k}` | {q.value:.6g} | {q.unit} |" for k, q in spec.example.items()]
        out += ["", "| Output | Value | Unit |", "|---|---|---|"]
        out += [f"| {o.label} | {o.quantity.value:.6g} | {o.quantity.unit} |" for o in result.outputs()]
        if result.warnings:
            out += ["", *[f"!!! warning\n    {w}" for w in result.warnings]]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def updated(text: str, body: str) -> str:
    start, end = text.index(BEGIN) + len(BEGIN), text.index(END)
    return text[:start] + "\n\n" + body + "\n" + text[end:]


def main(argv: list[str]) -> int:
    check = "--check" in argv
    stale = []
    for key in PAGES:
        page = DOCS / f"{key}.md"
        text = page.read_text(encoding="utf-8")
        new = updated(text, render_models(key))
        if new != text:
            stale.append(page.name)
            if not check:
                page.write_text(new, encoding="utf-8")
    if stale and check:
        print("Out of date (run tools/gen_model_reference.py): " + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
