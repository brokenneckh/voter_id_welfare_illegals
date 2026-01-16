# Voter ID & Welfare Benefits — Replication Pipeline

Code + data for reproducing the project’s empirical pipeline (analysis scripts, results, and paper artifacts).

## Repo layout

- **Pipeline / analysis code**: `src/` (entrypoint: `python -m pipeline.runner`)
- **Inputs + curated datasets**: `data/`
- **Machine-readable results**: `data/results/*.json`
- **Figures**: `output/*.png`
- **Markdown reports**: generated into `output/*.md` (not committed)
- **Standalone modules**: `standalone_high_contrast_maps/` (self-contained, distributable)

## Quick start

```bash
pip install -r requirements.txt

cd src
python -m pipeline.runner --smoke-test
python -m pipeline.runner --full
```

## Common commands

```bash
cd src

# Authoritative script list / counts live in code
python -m pipeline.runner --list-scripts

# Run one script
python -m pipeline.runner --script master_synthesis.py

# Run a tier range
python -m pipeline.runner --tier 0 1 2
```

## Tests

```bash
pytest -q
```

## Standalone Modules

### High-Contrast Maps

`standalone_high_contrast_maps/` contains a self-contained module for generating high-contrast map figures showing policy-electoral correlations. It can be copied and run independently:

```bash
cd standalone_high_contrast_maps
pip install -r requirements.txt
python generate_maps.py
```

Generates four figures in `output/`:
- Voter ID laws vs electoral outcomes
- Welfare benefits vs electoral outcomes
- Unauthorized immigrant population vs electoral outcomes
- Unauthorized immigrant % of population vs electoral outcomes

## Contributor notes

See `CLAUDE.md` for repo-specific conventions.

## License

MIT
