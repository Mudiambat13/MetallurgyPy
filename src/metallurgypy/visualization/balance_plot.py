"""Static, publication-quality charts built from :class:`~metallurgypy.core.results.ChartData`.

Requires the optional ``visualization`` extra (Matplotlib). The chart shows
exactly the values of the result and states where they come from.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from metallurgypy.core.results import ChartData

_SUPPORTED = {".png", ".svg"}


def _figure_class() -> Any:
    try:
        from matplotlib.figure import Figure
    except ImportError:
        raise ImportError(
            'Matplotlib is required for charts: pip install "metallurgypy[visualization]"'
        ) from None
    return Figure


def build_figure(chart: ChartData) -> Any:
    """Return a Matplotlib ``Figure`` (no pyplot, no global state, no display needed)."""
    figure = _figure_class()(figsize=(6.4, 4.2), layout="constrained")
    # Keep a strip at the bottom for the source line, which constrained layout cannot see.
    figure.get_layout_engine().set(rect=(0.0, 0.05, 1.0, 0.95))
    axes = figure.subplots()
    if chart.kind == "line":
        axes.plot(chart.x, chart.values, color="#4a6b8a", linewidth=2)
        axes.set_xlabel(chart.x_label)
    else:
        bars = axes.bar(chart.categories, chart.values, color="#4a6b8a", width=0.6)
        axes.bar_label(bars, labels=[f"{v:.6g}" for v in chart.values], padding=3)
    axes.set_ylabel(chart.y_label or f"Mass ({chart.unit})")
    axes.set_title(chart.title)
    axes.margins(y=0.12)
    axes.spines[["top", "right"]].set_visible(False)
    figure.text(0.01, 0.005, chart.source, fontsize=7, color="#555555", ha="left", va="bottom")
    return figure


def save_chart(chart: ChartData, path: str | os.PathLike[str], *, overwrite: bool = False) -> Path:
    """Write ``chart`` as PNG or SVG (chosen by the file suffix)."""
    target = Path(path)
    if target.suffix.lower() not in _SUPPORTED:
        raise ValueError(f"Unsupported chart format {target.suffix!r}; use .png or .svg.")
    if target.exists() and not overwrite:
        raise FileExistsError(f"{target} already exists; refusing to overwrite it.")
    target.parent.mkdir(parents=True, exist_ok=True)
    build_figure(chart).savefig(target, dpi=200)
    return target
