"""Registry of calculators, so interfaces can discover models from controlled metadata.

Studio builds its forms from :class:`ParameterSpec` and runs models through
:meth:`ModelSpec.run`. Saved files refer to models by ``model_id`` only: a file
can never make the program import or run code (see ``records.py``).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

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


def param(
    name: str,
    label: str,
    description: str,
    default_unit: str,
    allowed: tuple[str, ...] | None = None,
) -> ParameterSpec:
    """Build a :class:`ParameterSpec`; allowed units default to the whole dimension."""
    from metallurgypy.core.units import dimension_of, units_of

    return ParameterSpec(
        name, label, description, allowed or units_of(dimension_of(default_unit)), default_unit
    )


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


def register_class(
    cls: type[Any],
    *,
    module_key: str,
    title: str,
    description: str,
    parameters: tuple[ParameterSpec, ...],
    example: Mapping[str, Quantity],
    doc_page: str,
) -> None:
    """Register a model class whose constructor takes the parameters as keyword arguments."""

    def factory(values: Mapping[str, Quantity]) -> Calculation:
        instance: Calculation = cls(**values)
        return instance

    register(
        ModelSpec(
            model_id=cls.MODEL_ID,
            module_key=module_key,
            title=title,
            description=description,
            model_version=cls.MODEL_VERSION,
            parameters=parameters,
            factory=factory,
            example=example,
            doc_page=doc_page,
        )
    )


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

_SPEC_MODULES = (
    "metallurgypy.mass_balance.spec",
    "metallurgypy.reagents.spec",
    "metallurgypy.electrowinning.spec",
    "metallurgypy.flotation.spec",
    "metallurgypy.filtration.spec",
    "metallurgypy.hydrometallurgy.spec",
    "metallurgypy.solvent_extraction.spec",
    "metallurgypy.thermodynamics.spec",
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
        import importlib

        for module in _SPEC_MODULES:
            importlib.import_module(module)  # each one registers its models


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
