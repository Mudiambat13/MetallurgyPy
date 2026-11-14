"""Exception hierarchy of MetallurgyPy.

All library errors derive from :class:`MetallurgyPyError`, so callers can catch
one type. Messages are written for engineers: they name the parameter and the
expected domain.
"""

from __future__ import annotations


class MetallurgyPyError(Exception):
    """Base class of every error raised on purpose by MetallurgyPy."""


class InvalidParameterError(MetallurgyPyError, ValueError):
    """An input is missing, non-finite, of the wrong type or out of its domain."""


class UnitConversionError(MetallurgyPyError):
    """A unit symbol is unknown or a conversion cannot be performed."""


class DimensionError(MetallurgyPyError):
    """A quantity has a physical dimension different from the one expected."""


class CalculationError(MetallurgyPyError):
    """A calculation could not be completed (for example a degenerate case)."""


class ConvergenceError(CalculationError):
    """An iterative method did not converge within its documented criteria."""


class ModelDomainError(MetallurgyPyError):
    """Inputs are individually valid but outside the validity domain of the model."""


class RecordFormatError(MetallurgyPyError):
    """A saved calculation file is malformed or uses an unsupported format version."""
