# Other modules

These modules are planned. Each will get its own scientific page (equations, assumptions, validity domain, sources) **before** it is released.

## Hydrometallurgy

Leaching, dissolution, precipitation, neutralization, solid/liquid balances, solution concentration, extraction yield, reaction kinetics.

Candidate classes: `LeachingModel`, `PrecipitationModel`, `NeutralizationModel`, `DissolutionModel`, `SolutionAnalysis`.

Stoichiometric calculations, equilibrium models and kinetic models are kept distinct. A simplified kinetic model is not assumed to represent every ore or set of operating conditions.

## Solvent extraction

Distribution coefficient, O/A and A/O ratios, extraction and stripping isotherms, theoretical stages, mixer-settler circuits, phase balances, circuit scenarios.

Candidate classes: `DistributionCoefficient`, `ExtractionStage`, `StrippingStage`, `SXCircuit`, `McCabeThieleAnalysis`.

The user specifies the chemical system, the equilibrium data and the assumptions. No universal behaviour is coded for any given extractant.

## Flotation

Recovery, mass yield, enrichment, concentrate/tailings balances, grade analysis, flotation kinetics.

## Filtration

Filtration rate, cake resistance, medium resistance, cake moisture, filtration time, pressure filtration models.

## Thermodynamics

Gibbs free energy, equilibrium constants, acid-base equilibria, pH under stated assumptions, chemical reactions, dissolution and precipitation, equilibrium solving with SciPy and SymPy.

Every thermodynamic dataset documents its source, reference temperature and validity domain.

## Statistics

Descriptive statistics, regression, correlation, anomaly detection, time series, variability analysis, performance indicators, sensitivity analysis.
