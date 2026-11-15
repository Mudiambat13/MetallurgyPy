"""Physical constants.

Only constants that are *exact by definition* in the 2019 SI redefinition are
included, and the derived ones are computed from them, so no digit is typed in
by hand. Reference: BIPM, *The International System of Units (SI)*, 9th edition
(2019): N_A, e and k_B are defined exact values.

Material properties, equilibrium data and operating values are deliberately
absent: they must come from the user or a documented source.
"""

from __future__ import annotations

AVOGADRO = 6.02214076e23  # 1/mol, exact (SI 2019)
ELEMENTARY_CHARGE = 1.602176634e-19  # C, exact (SI 2019)
BOLTZMANN = 1.380649e-23  # J/K, exact (SI 2019)

FARADAY = AVOGADRO * ELEMENTARY_CHARGE  # C/mol, derived (about 96485.33212)
GAS_CONSTANT = AVOGADRO * BOLTZMANN  # J/(mol.K), derived (about 8.314462618)
