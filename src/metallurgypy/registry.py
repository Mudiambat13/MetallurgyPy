"""Registry of calculators, so interfaces can discover models from controlled metadata.

Studio builds its forms from :class:`ParameterSpec` and runs models through
:meth:`ModelSpec.run`. Saved files refer to models by ``model_id`` only: a file
can never make the program import or run code (see ``records.py``).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol

from metallurgypy.core.exceptions import InvalidParameterError
from metallurgypy.core.results import CalculationResult
from metallurgypy.core.units import Quantity


class Calculation(Protocol):
    def calculate(self) -> CalculationResult: ...


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    label: str
    description: str
    units: tuple[str, ...]
    default_unit: str


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    module_key: str
    title: str
    description: str
    model_version: str
    parameters: tuple[ParameterSpec, ...]
    factory: Callable[[Mapping[str, Quantity]], Calculation]
    # Illustrative values for the "fill with example" button. Never real plant data.
    example: Mapping[str, Quantity]
    doc_page: str

    def run(self, inputs: Mapping[str, Quantity]) -> CalculationResult:
        missing = [p.name for p in self.parameters if p.name not in inputs]
        if missing:
            raise InvalidParameterError(f"Missing input(s): {', '.join(missing)}.")
        unknown = sorted(set(inputs) - {p.name for p in self.parameters})
        if unknown:
            raise InvalidParameterError(f"Unknown input(s) for {self.model_id}: {', '.join(unknown)}.")
        return self.factory(inputs).calculate()


@dataclass(frozen=True)
class ModuleInfo:
    key: str
    title: str
    description: str
    doc_page: str


MODULE_CATALOG: tuple[ModuleInfo, ...] = (
    ModuleInfo("mass_balance", "Mass Balance", "Global and per-component balances, recovery, mass yield.", "scientific_methods/mass_balance/"),
    ModuleInfo("hydrometallurgy", "Hydrometallurgy", "Leaching, dissolution, precipitation, neutralization.", "scientific_methods/other_modules/#hydrometallurgy"),
    ModuleInfo("solvent_extraction", "Solvent Extraction", "Distribution, isotherms, theoretical stages, circuits.", "scientific_methods/other_modules/#solvent-extraction"),
    ModuleInfo("electrowinning", "Electrowinning", "Faraday's law, current efficiency, production, energy.", "scientific_methods/electrowinning/"),
    ModuleInfo("flotation", "Flotation", "Recovery, enrichment, kinetics.", "scientific_methods/other_modules/#flotation"),
    ModuleInfo("filtration", "Filtration", "Cake and medium resistance, moisture, filtration time.", "scientific_methods/other_modules/#filtration"),
    ModuleInfo("reagents", "Reagents", "Dosage, dilution, concentrations, consumption.", "scientific_methods/reagents/"),
    ModuleInfo("thermodynamics", "Thermodynamics", "Gibbs energy, equilibrium constants, pH.", "scientific_methods/other_modules/#thermodynamics"),
    ModuleInfo("statistics", "Statistics", "Descriptive statistics, regression, sensitivity.", "scientific_methods/other_modules/#statistics"),
)

_MODELS: dict[str, ModelSpec] = {}
_builtins_loaded = False


def register(spec: ModelSpec) -> None:
    if spec.model_id in _MODELS:
        raise ValueError(f"Model {spec.model_id!r} is already registered.")
    _MODELS[spec.model_id] = spec


def _load_builtins() -> None:
    global _builtins_loaded
    if not _builtins_loaded:
        _builtins_loaded = True
        import metallurgypy.mass_balance.spec  # noqa: F401  (registers its models)


def list_models(module_key: str | None = None) -> tuple[ModelSpec, ...]:
    _load_builtins()
    models = tuple(_MODELS.values())
    if module_key is not None:
        models = tuple(m for m in models if m.module_key == module_key)
    return models


def get_model(model_id: str) -> ModelSpec:
    _load_builtins()
    try:
        return _MODELS[model_id]
    except KeyError:
        known = ", ".join(sorted(_MODELS)) or "none"
        raise InvalidParameterError(f"Unknown model {model_id!r}. Available: {known}.") from None
