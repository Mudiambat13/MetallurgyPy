# Contributing

Contributions are welcome from engineers, researchers, teachers and developers.

## Ground rules

- Code and API are in English.
- Document every equation, assumption and domain of validity.
- Never add constants, experimental data or validation results without a source.
- Keep the Core free of GUI imports; Studio calls the Core public API only.
- Add a dependency only with a technical justification.
- Inspect existing files before changing them and preserve validated behaviour.
- Never round intermediate values without justification.

## Development setup

```bash
pip install -e ".[dev]"
```

Quality tools: pytest, ruff (lint and format) and mypy (strict). Core tests and GUI tests run as separate jobs in CI.

## Adding a model

1. Write its scientific page: equations, assumptions, validity domain, sources.
2. Implement it with unit checks and input validation.
3. Add tests: formula, limits, invalid input, convergence where relevant, and a documented reference case.
4. Add an example and register the model's metadata so Studio can discover it.

## Documentation changes

```bash
pip install -r docs/requirements.txt
mkdocs build --strict
```

The same strict build runs in CI on pull requests, and a push to `main` deploys the site to GitHub Pages.
