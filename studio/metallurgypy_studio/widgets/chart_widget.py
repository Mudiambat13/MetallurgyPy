"""Interactive chart of a result (pyqtgraph: zoom, pan, coordinates).

The chart plots exactly the :class:`ChartData` of the result and prints its
provenance under the plot. Static PNG/SVG export is done by the Core
(``metallurgypy.visualization``), so exported figures match the Core, not a
screen grab.
"""

from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtCore import QPointF, Slot
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from metallurgypy.core import ChartData


class ChartWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._chart: ChartData | None = None
        self._dark = False
        self.plot = pg.PlotWidget()
        self.plot.setMenuEnabled(True)
        self._coords = QLabel("")
        self._coords.setObjectName("Hint")
        self._source = QLabel("No result to plot yet.")
        self._source.setObjectName("Hint")
        layout = QVBoxLayout(self)
        layout.addWidget(self.plot, 1)
        layout.addWidget(self._coords)
        layout.addWidget(self._source)
        self.plot.scene().sigMouseMoved.connect(self._on_mouse_moved)
        self.set_dark(False)

    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        foreground = "#e3e8ee" if dark else "#1d2733"
        self.plot.setBackground("#232b33" if dark else "#ffffff")
        for axis in ("left", "bottom"):
            item = self.plot.getAxis(axis)
            item.setPen(foreground)
            item.setTextPen(foreground)
        if self._chart is not None:
            self.set_chart(self._chart)

    def set_chart(self, chart: ChartData | None) -> None:
        self._chart = chart
        self.plot.clear()
        self._coords.setText("")
        if chart is None:
            self._source.setText("No result to plot yet.")
            return
        positions = list(range(len(chart.values)))
        self.plot.addItem(
            pg.BarGraphItem(
                x=positions, height=list(chart.values), width=0.6, brush="#4a6b8a" if not self._dark else "#6fa3d6"
            )
        )
        for x, value in zip(positions, chart.values, strict=True):
            label = pg.TextItem(f"{value:.6g}", anchor=(0.5, 1.0), color="#e3e8ee" if self._dark else "#1d2733")
            label.setPos(x, value)
            self.plot.addItem(label)
        self.plot.getAxis("bottom").setTicks([list(zip(positions, chart.categories, strict=True))])
        self.plot.setLabel("left", f"Mass ({chart.unit})")
        self.plot.setTitle(chart.title)
        self.plot.showGrid(x=False, y=True, alpha=0.25)
        self.plot.enableAutoRange()
        self._source.setText(f"Source: {chart.source}")

    @Slot(object)
    def _on_mouse_moved(self, scene_pos: QPointF) -> None:
        if self._chart is None or not self.plot.sceneBoundingRect().contains(scene_pos):
            return
        point = self.plot.plotItem.vb.mapSceneToView(scene_pos)
        self._coords.setText(f"y = {point.y():.6g} {self._chart.unit}")
