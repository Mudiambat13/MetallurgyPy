"""Regenerate the pictures in docs/assets/screenshots from real library output.

Every picture is produced by running the library: charts come from ``save_chart`` and the
report picture is a rendering of ``render_html``. Nothing is drawn by hand.

    python tools/make_screenshots.py            # charts + report (needs matplotlib, playwright)

Pictures of the desktop application are made by ``tools/take_studio_screenshots.py``, which
needs PySide6.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "docs" / "assets" / "screenshots"


def main() -> int:
    from metallurgypy.core import Quantity
    from metallurgypy.registry import get_model
    from metallurgypy.reports import ReportEntry, build_report, render_html
    from metallurgypy.visualization import save_chart

    OUT.mkdir(parents=True, exist_ok=True)

    def run(model_id: str, **overrides: Quantity):  # type: ignore[no-untyped-def]
        spec = get_model(model_id)
        return spec.run({**spec.example, **overrides})

    balance = run("mass_balance.recovery")
    kinetics = run("hydrometallurgy.leach_kinetics_first_order")
    for name, result in (("chart_mass_balance", balance), ("chart_leach_kinetics", kinetics)):
        chart = result.chart_data()
        if chart is None:
            raise SystemExit(f"{name}: this result has no chart")
        save_chart(chart, OUT / f"{name}.png", overwrite=True)

    base = run("mass_balance.recovery")
    better = run("mass_balance.recovery", recovery=Quantity(95, "%"))
    entries = [
        ReportEntry(
            "Base case",
            base,
            observations={"Plant assay of concentrate": Quantity(24.1, "%")},
            notes="Illustrative data, not plant data.",
        ),
        ReportEntry("Improved recovery", better, notes="Illustrative data, not plant data."),
    ]
    html = render_html(
        build_report(entries, title="Pilot study", author="Example", include_charts=True)
    )

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright is not installed: report picture skipped", file=sys.stderr)
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        page_file = Path(tmp) / "report.html"
        page_file.write_text(html, encoding="utf-8")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1000, "height": 1100}, device_scale_factor=2)
            page.goto(page_file.as_uri())
            page.screenshot(path=str(OUT / "report_html.png"))
            browser.close()
    print("pictures written to", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
