# GTSM_AI

AI model development for the FUTURA GTSM work.

## Structure

```
GTSM_AI/
├── src/
│   └── gtsm_ai/        # importable package — all reusable, tested code lives here
├── tests/              # pytest unit tests, mirrors the src/gtsm_ai layout
├── examples/           # small, runnable, documented scripts/notebooks showing how to use gtsm_ai
├── sandbox/            # throwaway/exploratory work, not covered by tests, not part of the package
├── data/               # local data (git-ignored by default, see .gitignore)
└── pyproject.toml      # package metadata, dependencies, pytest/tooling config
```

## Guidelines

- Anything under `src/gtsm_ai` should be tested. Add/extend tests in `tests/`
  whenever you add code there.
- `examples/` is for clean, minimal, working demonstrations of the package's
  public API — keep them in sync with `src/gtsm_ai`.
- `sandbox/` is for experiments and scratch work. Nothing in here is expected
  to be stable, tested, or imported by other code. Promote useful code out of
  the sandbox into `src/gtsm_ai` (with tests) once it matures.
- `data/` holds local datasets used during development; large/raw data should
  not be committed (see root `.gitignore`).
