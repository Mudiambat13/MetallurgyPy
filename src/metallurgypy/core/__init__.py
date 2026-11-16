"""Foundations shared by all MetallurgyPy models."""

from metallurgypy.core.exceptions import (
    CalculationError,
    ConvergenceError,
    DimensionError,
    InvalidParameterError,
    MetallurgyPyError,
    ModelDomainError,
    RecordFormatError,
    UnitConversionError,
)
from metallurgypy.core.modes import CalculationMode
from metallurgypy.core.provenance import Provenance
from metallurgypy.core.results import CalculationResult, ChartData, GenericResult, OutputItem
from metallurgypy.core.units import Quantity
from metallurgypy.core.validation import DEFAULT_TOLERANCES, Tolerances

__all__ = [
    "DEFAULT_TOLERANCES",
    "CalculationError",
    "CalculationMode",
    "CalculationResult",
    "ChartData",
    "ConvergenceError",
    "DimensionError",
    "GenericResult",
    "InvalidParameterError",
    "MetallurgyPyError",
    "ModelDomainError",
    "OutputItem",
    "Provenance",
    "Quantity",
    "RecordFormatError",
    "Tolerances",
    "UnitConversionError",
]
