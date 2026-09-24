# futura-ai-gtsm
This repository provides the development for the work under the EU FUTURA project. 

Link to the time series AI model: https://github.com/Deltares-research/AIHydroPoints.jl

## Repository structure

- [GTSM](GTSM) — GTSM-specific work (model setup, configuration, data prep) independent of the AI model.
- [GTSM_AI](GTSM_AI) — AI model development, structured as an installable Python package (`src/`, `tests/`, `examples/`, `sandbox/`). See [GTSM_AI/README.md](GTSM_AI/README.md) for details.
