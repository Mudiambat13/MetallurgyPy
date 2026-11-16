"""Facts about the floating-point arithmetic actually available, detected rather than assumed."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PlatformPrecision:
    float64_epsilon: float
    float64_mantissa_bits: int
    longdouble_available: bool
    longdouble_mantissa_bits: int | None
    longdouble_is_extended: bool | None  # True if it carries more than 53 bits on this platform
    note: str


def platform_precision() -> PlatformPrecision:
    """Report float64 properties and, if NumPy is installed, what ``longdouble`` really is here.

    ``numpy.longdouble`` is 80-bit extended precision on most x86 Linux builds, but equal to
    float64 on Windows and on some ARM builds. MetallurgyPy does not use it unless this
    function says it is genuinely wider.
    """
    try:
        import numpy as np
    except ImportError:
        return PlatformPrecision(
            sys.float_info.epsilon,
            sys.float_info.mant_dig,
            False,
            None,
            None,
            "NumPy is not installed: only float64 and exact rational arithmetic are used.",
        )
    info: Any = np.finfo(np.longdouble)
    bits = int(info.nmant) + 1
    extended = bits > sys.float_info.mant_dig
    return PlatformPrecision(
        sys.float_info.epsilon,
        sys.float_info.mant_dig,
        True,
        bits,
        extended,
        f"numpy.longdouble has a {bits}-bit mantissa on this platform"
        + ("" if extended else " (no wider than float64)")
        + "; this varies between platforms.",
    )
