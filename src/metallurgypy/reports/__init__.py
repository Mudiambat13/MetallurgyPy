"""Calculation reports (HTML with the standard library; PDF needs the visualization extra).

A report separates three kinds of values and says so on the page:

* **calculated / estimated** values produced by a model;
* **observations**: values *measured or entered by the user*, shown as given, never computed;
* uncertainties, shown only when they were propagated from stated input uncertainties.

Every report carries the model, equations, assumptions, warnings, date and software
version, and a reminder that these are simplified models, not validated industrial simulation.
"""

from __future__ import annotations

import html
import io
import os
import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from metallurgypy.core.exceptions import InvalidParameterError
from metallurgypy.core.results import CalculationResult
from metallurgypy.core.units import Quantity
from metallurgypy.precision.significant_figures import format_with_uncertainty
from metallurgypy.precision.uncertainty import UncertainResult
from metallurgypy.records import _write_text
from metallurgypy.version import __version__

__all__ = ["ReportEntry", "Block", "ReportDocument", "build_report", "render_html", "write_html", "write_pdf"]

DISCLAIMER = (
    "These results come from simplified models documented in MetallurgyPy. They are not a validated "
    "industrial simulation. Check the assumptions and the domain of validity before using them for an "
    "engineering decision."
)

_KIND_TEXT = {"calculated": "calculated", "estimated": "estimated", "measured": "measured"}


@dataclass(frozen=True)
class ReportEntry:
    title: str
    result: CalculationResult
    uncertain: UncertainResult | None = None
    observations: Mapping[str, Quantity] = field(default_factory=dict)
    notes: str = ""


@dataclass(frozen=True)
class Block:
    kind: str  # h1 h2 h3 p note ul table svg
    text: str = ""
    items: tuple[str, ...] = ()
    header: tuple[str, ...] = ()
    rows: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class ReportDocument:
    title: str
    author: str
    generated: str
    blocks: tuple[Block, ...]


def _num(value: float) -> str:
    return f"{value:.10g}"


def _chart_svg(result: CalculationResult) -> str | None:
    chart = result.chart_data()
    if chart is None:
        return None
    try:
        from metallurgypy.visualization import build_figure
    except ImportError:
        return None
    try:
        figure = build_figure(chart)
    except ImportError:
        return None
    buffer = io.StringIO()
    figure.savefig(buffer, format="svg")
    svg = buffer.getvalue()
    start = svg.find("<svg")
    return svg[start:] if start >= 0 else None


def build_report(
    entries: Sequence[ReportEntry],
    *,
    title: str = "MetallurgyPy calculation report",
    author: str = "",
    include_charts: bool = True,
) -> ReportDocument:
    if not entries:
        raise InvalidParameterError("A report needs at least one entry.")
    blocks: list[Block] = [Block("note", DISCLAIMER)]
    for entry in entries:
        r, p = entry.result, entry.result.provenance
        blocks.append(Block("h2", entry.title))
        blocks.append(
            Block(
                "p",
                f"Model {p.model_id} (version {p.model_version}); mode {p.calculation_mode}; "
                f"convergence: {p.convergence}; calculated {p.timestamp} with MetallurgyPy {p.software_version}.",
            )
        )
        if entry.notes.strip():
            blocks += [Block("h3", "Notes"), Block("p", entry.notes.strip())]
        blocks.append(Block("h3", "Method"))
        blocks.append(Block("p", p.method))
        if p.equations:
            blocks += [Block("h3", "Equations"), Block("ul", items=tuple(p.equations))]
        if p.assumptions:
            blocks += [Block("h3", "Assumptions"), Block("ul", items=tuple(p.assumptions))]
        blocks.append(
            Block(
                "table",
                "Inputs",
                header=("Input", "Value", "Unit"),
                rows=tuple((k, _num(q.value), q.unit) for k, q in p.inputs.items()),
            )
        )
        u = entry.uncertain
        header = ("Output", "Value", "Unit", "Kind") + (("Standard uncertainty",) if u else ())
        rows = []
        for o in r.outputs():
            row: tuple[str, ...] = (o.label, _num(o.quantity.value), o.quantity.unit, _KIND_TEXT.get(o.kind, o.kind))
            if u:
                out_u = u.outputs.get(o.name)
                su = out_u.standard_uncertainty if out_u else 0.0
                row += (format_with_uncertainty(o.quantity.value, su) if su > 0.0 else "exact input",)
            rows.append(row)
        blocks.append(Block("table", "Results", header=header, rows=tuple(rows)))
        if u:
            blocks.append(Block("p", f"Uncertainty method: {u.method}. Standard uncertainties (k = 1)."))
        if entry.observations:
            blocks.append(
                Block(
                    "table",
                    "Observations (entered by the user; not computed by the model)",
                    header=("Quantity", "Value", "Unit"),
                    rows=tuple((k, _num(q.value), q.unit) for k, q in entry.observations.items()),
                )
            )
        warnings = list(r.warnings) + (list(u.warnings) if u else [])
        if warnings:
            blocks += [Block("h3", "Warnings"), Block("ul", items=tuple(warnings))]
        if include_charts:
            svg = _chart_svg(r)
            if svg:
                blocks.append(Block("svg", svg))
    return ReportDocument(
        title, author, datetime.now(timezone.utc).isoformat(timespec="seconds"), tuple(blocks)
    )


_CSS = (
    "body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#222}"
    "table{border-collapse:collapse;margin:.5rem 0 1rem}th,td{border:1px solid #bbb;padding:.3rem .6rem;"
    "text-align:left}th{background:#eef2f6}.note{border-left:4px solid #b8860b;background:#fff8e1;"
    "padding:.6rem 1rem}caption{text-align:left;font-weight:600;padding:.3rem 0}"
)


def render_html(document: ReportDocument) -> str:
    """Self-contained HTML. All text is escaped; the only raw markup is matplotlib's own SVG."""
    e = html.escape
    out = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        f"<title>{e(document.title)}</title><style>{_CSS}</style></head><body>",
        f"<h1>{e(document.title)}</h1>",
        f"<p>{e(document.author) + ' · ' if document.author else ''}Generated {e(document.generated)} "
        f"with MetallurgyPy {e(__version__)}</p>",
    ]
    for b in document.blocks:
        if b.kind in ("h2", "h3"):
            out.append(f"<{b.kind}>{e(b.text)}</{b.kind}>")
        elif b.kind == "p":
            out.append(f"<p>{e(b.text)}</p>")
        elif b.kind == "note":
            out.append(f'<p class="note">{e(b.text)}</p>')
        elif b.kind == "ul":
            out.append("<ul>" + "".join(f"<li>{e(i)}</li>" for i in b.items) + "</ul>")
        elif b.kind == "table":
            head = "".join(f"<th>{e(h)}</th>" for h in b.header)
            body = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in b.rows)
            out.append(f"<table><caption>{e(b.text)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
        elif b.kind == "svg":
            out.append(f'<div class="chart">{b.text}</div>')
    out.append("</body></html>")
    return "\n".join(out) + "\n"


def write_html(path: str | os.PathLike[str], document: ReportDocument, *, overwrite: bool = False) -> Path:
    target = Path(path)
    _write_text(target, render_html(document), overwrite=overwrite)
    return target


def write_pdf(path: str | os.PathLike[str], document: ReportDocument, *, overwrite: bool = False) -> Path:
    """Plain PDF (text and tables as text) through Matplotlib. Charts are in the HTML report."""
    target = Path(path)
    if target.exists() and not overwrite:
        raise FileExistsError(f"{target} already exists; refusing to overwrite it.")
    try:
        from matplotlib.backends.backend_pdf import PdfPages
        from matplotlib.figure import Figure
    except ImportError:
        raise ImportError('PDF reports need Matplotlib: pip install "metallurgypy[visualization]"') from None

    lines: list[tuple[str, str]] = [("h1", document.title)]
    lines.append(("p", f"{document.author + ' - ' if document.author else ''}Generated {document.generated} "
                       f"with MetallurgyPy {__version__}"))
    for b in document.blocks:
        if b.kind in ("h2", "h3"):
            lines += [("", ""), (b.kind, b.text)]
        elif b.kind in ("p", "note"):
            lines += [("p", ln) for ln in textwrap.wrap(b.text, 95)]
        elif b.kind == "ul":
            for item in b.items:
                lines += [("p", ln) for ln in textwrap.wrap("- " + item, 95, subsequent_indent="  ")]
        elif b.kind == "table":
            lines += [("h3", b.text), ("m", "  ".join(b.header))]
            lines += [("m", "  ".join(r)) for r in b.rows]
    per_page = 58
    pages = [lines[i : i + per_page] for i in range(0, len(lines), per_page)] or [[]]
    target.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(target) as pdf:
        for page in pages:
            fig = Figure(figsize=(8.27, 11.69))
            y = 0.97
            for kind, text in page:
                size = {"h1": 15, "h2": 12, "h3": 10.5}.get(kind, 8.5)
                fig.text(0.07, y, text[:140], fontsize=size, family="monospace" if kind == "m" else "sans-serif",
                         fontweight="bold" if kind in ("h1", "h2", "h3") else "normal", va="top")
                y -= 0.0165
            pdf.savefig(fig)
    return target
