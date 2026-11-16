# Your first mass balance

!!! info "Verified"
    The code below was run against the implemented Core and gives the values shown.

The inputs below are **illustrative, not plant data**.

## 1. Compute by hand

Feed of 1000 mass units at 2.5 % metal, with 92 % recovery:

| Quantity | Calculation | Value |
|---|---|---|
| Contained metal | \(1000 \times 0.025\) | 25 |
| Recovered metal | \(25 \times 0.92\) | 23 |
| Remaining metal | \(25 - 23\) | 2 |

## 2. Compute with MetallurgyPy

```python
from metallurgypy.mass_balance import MassBalance

result = MassBalance(
    feed_mass=1000,  # tonnes
    feed_grade=0.025,  # mass fraction
    recovery=0.92,  # fraction
).calculate()

print(result.metal_recovered)  # 23.0 t
print(result.metal_remaining)  # 2.0 t
```

The result should match the hand calculation. If it does not, that is a bug to report.

## 3. Check conventions

Before trusting a number, confirm:

- the mass unit and whether the basis is dry or wet
- that the grade is a mass fraction, not a percentage
- that `recovery` means recovery of contained metal, not mass yield

## 4. Inspect assumptions

Read the warnings and assumptions attached to the result before using it. They are part of the answer.

## 5. Do the same in Studio

Open Studio, choose **Mass Balance** in the side navigation, enter the same values and compare the output to the Python result. Both call the same Core code.
