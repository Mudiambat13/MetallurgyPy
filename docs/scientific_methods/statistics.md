# Statistics

**Package:** `metallurgypy.statistics` · **Status:** implemented, API only (Studio has no form for it)

Standard-library implementations (no NumPy) of the statistics used around metallurgical data. Functions return plain dataclasses and raise `InvalidParameterError` on unusable data: they never silently drop values.

| Function | What it does | Notes |
|---|---|---|
| `describe(values)` | n, mean, median, sample standard deviation, min, max, quartiles, coefficient of variation | Dispersion uses the \(n-1\) estimator. Quartiles use the inclusive method. `cv` is `None` when the mean is 0. |
| `linear_regression(x, y)` | Ordinary least squares \(y = a + bx\), \(R^2\), standard errors | Standard errors are `None` for 2 points (no residual degrees of freedom). |
| `correlation(x, y)` | Pearson coefficient | Linear association only; says nothing about causality. |
| `detect_outliers(values, threshold=3.5)` | Modified z-score (median and MAD) | A screening rule (Iglewicz and Hoaglin), **not** proof that a value is wrong. Raises if the MAD is zero. |
| `moving_average(values, window)` | Trailing simple moving average | The first `window - 1` points are not produced. |
| `variability(groups)` | Pooled within-group standard deviation and spread of group means | For replicate groups; at least two groups of two values. |

```python
from metallurgypy.statistics import describe, linear_regression

d = describe([2.4, 2.6, 2.5, 2.7, 2.5])
fit = linear_regression([1, 2, 3, 4], [2.1, 3.9, 6.2, 7.8])
print(d.mean, fit.slope, fit.r_squared)
```

## Limits

These are descriptive tools. They do not test hypotheses, do not choose a distribution, and an outlier flag must be investigated (sampling, assay, process upset), not deleted automatically.
