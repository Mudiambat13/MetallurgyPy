"""Traceability: everything needed to understand and reproduce a result."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from metallurgypy.core.units import Quantity
from metallurgypy.core.validation import Tolerances
from metallurgypy.version import __version__


@dataclass(frozen=True)
class Provenance:
    model_id: str
    model_version: str
    method: str
    equations: tuple[str, ...]
    assumptions: tuple[str, ...]
    inputs: Mapping[str, Quantity]
    tolerances: Tolerances
    calculation_mode: str = "standard"
    convergence: str = "not_applicable"
    software_version: str = __version__
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_version": self.model_version,
            "method": self.method,
            "equations": list(self.equations),
            "assumptions": list(self.assumptions),
            "inputs": {k: {"value": q.value, "unit": q.unit} for k, q in self.inputs.items()},
            "tolerances": {"rel": self.tolerances.rel, "abs": self.tolerances.abs},
            "calculation_mode": self.calculation_mode,
            "convergence": self.convergence,
            "software_version": self.software_version,
            "timestamp": self.timestamp,
        }
