"""Metal balance with the Core only (no GUI).

All input values are ILLUSTRATIVE, not plant data.
Run:  python examples/mass_balance/basic_balance.py
"""

from metallurgypy.core import Quantity
from metallurgypy.mass_balance import MassBalance, TwoProductBalance

balance = MassBalance(
    feed_mass=Quantity(1000, "t"),
    feed_grade=Quantity(2.5, "%"),
    recovery=Quantity(92, "%"),
).calculate()

print("Metal in feed:   ", balance.metal_feed)
print("Metal recovered: ", balance.metal_recovered)
print("Metal remaining: ", balance.metal_remaining)
print("Assumptions:")
for assumption in balance.provenance.assumptions:
    print("  -", assumption)

split = TwoProductBalance(
    feed_mass=Quantity(1000, "t"),
    feed_grade=Quantity(2.0, "%"),
    concentrate_grade=Quantity(20.0, "%"),
    tailings_grade=Quantity(0.4, "%"),
).calculate()
print()
print("Concentrate mass:", split.concentrate_mass)
print("Mass yield:      ", split.mass_yield, "(share of total mass)")
print("Recovery:        ", split.recovery, "(share of contained metal)")
