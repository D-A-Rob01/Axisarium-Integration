# Cartomancy Engine Accessibility Map

## Source of Truth

The source code lives in local development storage:

```text
C:\Users\david\Documents\Axisarium Integration\cartomancy_engine\
```

## Vault Outputs

Generated readings are intended to be written to:

```text
Axisarium/03 Readings/Tarot/
```

Use `--output` when writing directly into the Axisarium vault.

## Mirror Policy

Google Drive may contain documentation and reading outputs, but not necessarily the full executable repo.

The executable package, tests, bundled data, and local development state should remain rooted in local development storage unless intentionally exported.

## Do Not Mirror Automatically

- `.venv/`
- `__pycache__/`
- `build/`
- `dist/`
- `.pytest_cache/`
- raw test artifacts unless intentionally preserved

## Safe to Mirror

- `README.md`
- `docs/`
- `readings/`
- review/audit summaries
