"""Registry metadata for the filtration models."""

from metallurgypy.core.units import Quantity
from metallurgypy.filtration.models import CakeMoisture, ConstantPressureFiltration
from metallurgypy.registry import param, register_class

_DOC = "scientific_methods/filtration/"

register_class(
    ConstantPressureFiltration,
    module_key="filtration",
    title="Constant-pressure cake filtration",
    description="Time and rate to filter a volume through an incompressible cake at constant pressure.",
    parameters=(
        param("viscosity", "Filtrate viscosity", "Dynamic viscosity of the filtrate.", "mPa.s"),
        param("cake_resistance", "Specific cake resistance (alpha)", "Measured for this slurry.", "m/kg"),
        param("solids_per_filtrate", "Solids per filtrate volume (c)", "Dry solids deposited per volume of filtrate.", "kg/m3", ("kg/m3", "g/L", "g/m3", "mg/L")),
        param("medium_resistance", "Medium resistance (R_m)", "Resistance of the filter medium.", "1/m"),
        param("area", "Filter area", "Filtration area.", "m2"),
        param("pressure_drop", "Pressure drop", "Constant pressure difference across cake and medium.", "kPa"),
        param("filtrate_volume", "Filtrate volume", "Volume of filtrate to collect.", "m3"),
    ),
    example={
        "viscosity": Quantity(1.0, "mPa.s"),
        "cake_resistance": Quantity(1e11, "m/kg"),
        "solids_per_filtrate": Quantity(50.0, "kg/m3"),
        "medium_resistance": Quantity(1e10, "1/m"),
        "area": Quantity(10.0, "m2"),
        "pressure_drop": Quantity(300.0, "kPa"),
        "filtrate_volume": Quantity(5.0, "m3"),
    },
    doc_page=_DOC,
)
register_class(
    CakeMoisture,
    module_key="filtration",
    title="Cake moisture",
    description="Moisture of a filter cake (wet and dry basis) from wet and dry masses.",
    parameters=(
        param("wet_cake_mass", "Wet cake mass", "Mass before drying.", "kg"),
        param("dry_cake_mass", "Dry cake mass", "Mass after drying to constant mass.", "kg"),
    ),
    example={"wet_cake_mass": Quantity(100.0, "kg"), "dry_cake_mass": Quantity(80.0, "kg")},
    doc_page=_DOC,
)
