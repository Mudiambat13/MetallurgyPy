"""Generate the API reference pages (docs/api/*.md) from the docstrings of the public API.

No third-party dependency: it uses ``inspect`` only, so the pages always match the code.

    python tools/gen_api_reference.py           # rewrite the pages
    python tools/gen_api_reference.py --check   # exit 1 if a page is out of date
"""

from __future__ import annotations

import enum
import importlib
import inspect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "docs" / "api"

# (page file, title, module)
MODULES: tuple[tuple[str, str, str], ...] = (
    ("core", "Core (units, results, errors)", "metallurgypy.core"),
    ("registry", "Model registry", "metallurgypy.registry"),
    ("mass_balance", "Mass balance", "metallurgypy.mass_balance"),
    ("reagents", "Reagents", "metallurgypy.reagents"),
    ("electrowinning", "Electrowinning", "metallurgypy.electrowinning"),
    ("flotation", "Flotation", "metallurgypy.flotation"),
    ("filtration", "Filtration", "metallurgypy.filtration"),
    ("hydrometallurgy", "Hydrometallurgy", "metallurgypy.hydrometallurgy"),
    ("solvent_extraction", "Solvent extraction", "metallurgypy.solvent_extraction"),
    ("thermodynamics", "Thermodynamics", "metallurgypy.thermodynamics"),
    ("statistics", "Statistics", "metallurgypy.statistics"),
    ("precision", "Precision and uncertainty", "metallurgypy.precision"),
    ("records", "Records and export", "metallurgypy.records"),
    ("data_io", "Data import", "metallurgypy.data_io"),
    ("comparison", "Scenario comparison", "metallurgypy.comparison"),
    ("reports", "Reports", "metallurgypy.reports"),
    ("projects", "Projects", "metallurgypy.projects"),
    ("visualization", "Visualization", "metallurgypy.visualization"),
)

_UNDERLINE = re.compile(r"^\s*([-=~^])\1{2,}\s*$")


def _clean_doc(doc: str | None) -> str:
    """Dedent a docstring and make it valid Markdown.

    reST underlines become bold lines, ``::`` literal blocks and ``>>>`` examples become
    fenced code blocks.
    """
    lines = inspect.cleandoc(doc or "").splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _UNDERLINE.match(line) and out:
            out[-1] = f"**{out[-1].strip()}**"
            i += 1
            continue
        if line.lstrip().startswith(">>>"):  # doctest example: until the next blank line
            block = []
            while i < len(lines) and lines[i].strip():
                block.append(lines[i])
                i += 1
            out += ["", "```pycon", *block, "```", ""]
            continue
        if line.rstrip().endswith("::"):  # reST literal block: the indented lines that follow
            out.append(line.rstrip()[:-1] if line.strip() != "::" else "")
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            block = []
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                block.append(lines[i])
                i += 1
            while block and not block[-1].strip():
                block.pop()
            indent = min((len(b) - len(b.lstrip()) for b in block if b.strip()), default=0)
            out += ["", "```text", *(b[indent:] for b in block), "```", ""]
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def _signature(obj: object, name: str) -> str:
    try:
        sig = str(inspect.signature(obj))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        sig = "(...)"
    sig = re.sub(r" at 0x[0-9a-fA-F]+", "", sig)
    sig = re.sub(r"<(\w+\.\w+): '[^']*'>", r"\1", sig)  # enum default -> Class.MEMBER
    sig = re.sub(r"(: |-> )'([^']*)'", r"\1\2", sig)  # unquote string annotations
    return f"{name}{sig}"


def _first_paragraph(doc: str | None) -> str:
    return _clean_doc(doc).split("\n\n")[0].strip()


def _public_names(module: object) -> list[str]:
    """Names listed in ``__all__``; without it, only classes/functions defined in this package.

    Names merely imported from the standard library are skipped: their docstrings change
    between Python versions and would make the generated pages differ from one CI job to another.
    """
    names = getattr(module, "__all__", None)
    if names is not None:
        return sorted(n for n in names if not n.startswith("_"))
    found = []
    for name in dir(module):
        if name.startswith("_"):
            continue
        obj = getattr(module, name)
        owner = getattr(obj, "__module__", "") or ""
        if (inspect.isclass(obj) or inspect.isfunction(obj)) and owner.split(".")[
            0
        ] == "metallurgypy":
            found.append(name)
    return sorted(found)


def _members(cls: type) -> list[tuple[str, object]]:
    found: list[tuple[str, object]] = []
    for name, value in vars(cls).items():
        if name.startswith("_"):
            continue
        target = value.fget if isinstance(value, property) else value
        if isinstance(value, (staticmethod, classmethod)):
            target = value.__func__
        if inspect.isfunction(target) and target.__doc__:
            found.append((name, target))
    return found


def render_page(title: str, module_name: str) -> str:
    module = importlib.import_module(module_name)
    lines = [
        "<!-- Generated by tools/gen_api_reference.py. Do not edit by hand. -->",
        f"# {title}",
        "",
        f"`import {module_name}`",
        "",
    ]
    summary = _first_paragraph(module.__doc__)
    if summary:
        lines += [summary, ""]
    for name in _public_names(module):
        obj = getattr(module, name)
        if inspect.isclass(obj) and issubclass(obj, enum.Enum):
            # The signature of an Enum differs between Python versions: list the members instead.
            lines += [f"## `{name}`", "", "```python", f"class {name}(enum.Enum)", "```", ""]
            doc = _clean_doc(obj.__doc__)
            if doc:
                lines += [doc, ""]
            lines += [f"- `{name}.{m.name}` = `{m.value!r}`" for m in obj] + [""]
        elif inspect.isclass(obj):
            lines += [f"## `{name}`", "", "```python", f"class {_signature(obj, name)}", "```", ""]
            doc = _clean_doc(obj.__doc__)
            if doc and not doc.startswith(
                f"{name}("
            ):  # skip the auto-generated dataclass docstring
                lines += [doc, ""]
            for member, target in _members(obj):
                lines += [
                    f"### `{name}.{member}`",
                    "",
                    "```python",
                    _signature(target, member),
                    "```",
                    "",
                ]
                lines += [_clean_doc(getattr(target, "__doc__", None)), ""]
        elif inspect.isfunction(obj):
            lines += [f"## `{name}`", "", "```python", _signature(obj, name), "```", ""]
            lines += [_clean_doc(obj.__doc__) or "*No docstring.*", ""]
        elif not inspect.ismodule(obj):
            kind = type(obj).__name__
            lines += [f"## `{name}`", "", f"Constant of type `{kind}`.", ""]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    check = "--check" in argv
    stale: list[str] = []
    for page, title, module_name in MODULES:
        path = OUT / f"{page}.md"
        text = render_page(title, module_name)
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == text:
            continue
        if check:
            stale.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
    if stale:
        print("Out of date (run: python tools/gen_api_reference.py):", *stale, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
