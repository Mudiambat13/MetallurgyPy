"""Measurements: a value, its unit and its uncertainty, with the type of that uncertainty stated.

Only conversions that are exact statements of the GUM (JCGM 100:2008) are
supported. ``kind="other"`` is deliberately not accepted: an uncertainty whose
meaning is unknown cannot be propagated.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from metallurgypy.core.exceptions import InvalidParameterError
from metallurgypy.core.units import Quantity

UncertaintyKind = Literal["standard", "expanded", "rectangular", "triangular"]

_KIND_HELP = (
    "standard (1 sigma), expanded (needs coverage_factor k), "
    "rectangular (half-width a, u = a / sqrt(3)), triangular (half-width a, u = a / sqrt(6))"
)


@dataclass(frozen=True)
class Measurement:
    """``uncertainty`` is in the unit of ``value`` and is interpreted according to ``kind``."""

    value: float
    unit: str
    uncertainty: float = 0.0
    kind: UncertaintyKind = "standard"
    coverage_factor: float | None = None
    method: str = ""
    timestamp: str | None = None

    def __post_init__(self) -> None:
        Quantity(self.value, self.unit)  # validates value (finite real) and unit
        if isinstance(self.uncertainty, bool) or not isinstance(self.uncertainty, (int, float)):
            raise InvalidParameterError("uncertainty must be a real number.")
        if not math.isfinite(self.uncertainty) or self.uncertainty < 0.0:
            raise InvalidParameterError(
                f"uncertainty must be finite and >= 0, got {self.uncertainty!r}."
            )
        if self.kind not in ("standard", "expanded", "rectangular", "triangular"):
            raise InvalidParameterError(
                f"Unsupported uncertainty kind {self.kind!r}. Use: {_KIND_HELP}."
            )
        if self.kind == "expanded":
            k = self.coverage_factor
            if k is None or not math.isfinite(k) or k <= 0.0:
                raise InvalidParameterError(
                    "An expanded uncertainty needs a coverage_factor k > 0."
                )
        elif self.coverage_factor is not None:
            raise InvalidParameterError("coverage_factor only applies to kind='expanded'.")

    @property
    def quantity(self) -> Quantity:
        return Quantity(self.value, self.unit)

    @property
    def standard_uncertainty(self) -> float:
        """The uncertainty as one standard deviation, in the unit of the value."""
        if self.kind == "standard":
            return self.uncertainty
        if self.kind == "expanded":
            assert self.coverage_factor is not None
            return self.uncertainty / self.coverage_factor
        if self.kind == "rectangular":
            return self.uncertainty / math.sqrt(3.0)
        return self.uncertainty / math.sqrt(6.0)  # triangular

    def expanded_uncertainty(self, k: float = 2.0) -> float:
        """Expanded uncertainty U = k * u. ``k = 2`` is a convention (about 95 % for a normal law)."""
        if not math.isfinite(k) or k <= 0.0:
            raise InvalidParameterError("k must be > 0.")
        return k * self.standard_uncertainty

    @property
    def relative_standard_uncertainty(self) -> float | None:
        """u / |value|, or None if the value is zero."""
        return None if self.value == 0.0 else self.standard_uncertainty / abs(self.value)

    @classmethod
    def from_replicates(
        cls, values: Sequence[float], unit: str, *, method: str = "Type A: mean of replicates"
    ) -> Measurement:
        """Type A evaluation: mean of ``values`` and standard uncertainty of the mean, s / sqrt(n)."""
        if len(values) < 2:
            raise InvalidParameterError(
                "At least two replicates are needed for a Type A uncertainty."
            )
        data = [Quantity(v, unit).value for v in values]
        mean = statistics.fmean(data)
        return cls(
            mean, unit, statistics.stdev(data) / math.sqrt(len(data)), "standard", method=method
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "value": self.value,
            "unit": self.unit,
            "uncertainty": self.uncertainty,
            "kind": self.kind,
            "coverage_factor": self.coverage_factor,
            "method": self.method,
            "timestamp": self.timestamp,
        }
